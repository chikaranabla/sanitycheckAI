"""
FastAPI Application for Opentrons Protocol Sanity Check
"""

import sys
import asyncio

# Windows環境でのMCPサブプロセス対応
if sys.platform == "win32":
    # WindowsSelectorEventLoopPolicyを使用してサブプロセス作成を可能にする
    # ProactorEventLoopではサブプロセス作成に制限があるため
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
import os
import tempfile
from pathlib import Path
from typing import Dict, Any

from backend.gemini_service import GeminiService
from backend.chat_service import get_chat_service

app = FastAPI(
    title="SanityCheck AI API",
    description="AI-powered physical setup verification system for Opentrons experimental protocols",
    version="2.0.0"
)

# CORS settings (allow frontend access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this appropriately
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")


@app.get("/")
async def root():
    """Root endpoint - Returns frontend"""
    index_path = frontend_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "SanityCheck AI API", "status": "running"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "API is running"}


@app.post("/api/validate", response_model=Dict[str, Any])
async def validate_protocol(
    protocol_file: UploadFile = File(..., description="Opentrons protocol file (.py)"),
    image_file: UploadFile = File(..., description="Setup image file (.jpg, .png)")
):
    """
    Receives protocol file and image, validates setup
    
    Args:
        protocol_file: Opentrons protocol file (.py)
        image_file: Setup image (.jpg, .png)
    
    Returns:
        Validation result (checkpoints and judgment results)
    """
    
    # File format validation
    if not protocol_file.filename.endswith('.py'):
        raise HTTPException(
            status_code=400,
            detail="Protocol file must be in .py format"
        )
    
    allowed_image_extensions = ['.jpg', '.jpeg', '.png']
    if not any(image_file.filename.lower().endswith(ext) for ext in allowed_image_extensions):
        raise HTTPException(
            status_code=400,
            detail="Image file must be in .jpg, .jpeg, or .png format"
        )
    
    # Save to temporary files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save protocol file
        protocol_path = Path(temp_dir) / protocol_file.filename
        with open(protocol_path, "wb") as f:
            content = await protocol_file.read()
            f.write(content)
        
        # Save image file
        image_path = Path(temp_dir) / image_file.filename
        with open(image_path, "wb") as f:
            image_content = await image_file.read()
            f.write(image_content)
        
        try:
            # Read protocol file content
            with open(protocol_path, "r", encoding="utf-8") as f:
                protocol_content = f.read()
            
            # Initialize Gemini service
            gemini_service = GeminiService()
            
            # Execute validation
            result = gemini_service.full_validation(
                protocol_content=protocol_content,
                image_path=str(image_path)
            )
            
            return result
            
        except ValueError as e:
            raise HTTPException(
                status_code=500,
                detail=f"API configuration error: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error occurred during verification: {str(e)}"
            )


@app.post("/api/checkpoints", response_model=Dict[str, Any])
async def generate_checkpoints(
    protocol_file: UploadFile = File(..., description="Opentrons protocol file (.py)")
):
    """
    Generates checkpoints only from protocol file
    
    Args:
        protocol_file: Opentrons protocol file (.py)
    
    Returns:
        List of checkpoints
    """
    
    # File format validation
    if not protocol_file.filename.endswith('.py'):
        raise HTTPException(
            status_code=400,
            detail="Protocol file must be in .py format"
        )
    
    try:
        # Read protocol file content
        content = await protocol_file.read()
        protocol_content = content.decode("utf-8")
        
        # Initialize Gemini service
        gemini_service = GeminiService()
        
        # Generate checkpoints
        checkpoints_data = gemini_service.generate_checkpoints(protocol_content)
        
        return checkpoints_data
        
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail=f"API configuration error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error occurred during checkpoint generation: {str(e)}"
        )


# ============================================================================
# CHAT-BASED VERIFICATION ENDPOINTS (V2)
# ============================================================================

@app.post("/api/chat/start")
async def start_chat_session(
    protocol_file: UploadFile = File(..., description="Opentrons protocol file (.py)")
):
    """
    Start a new chat session by uploading a protocol file
    
    Args:
        protocol_file: Opentrons protocol file (.py)
        
    Returns:
        Session ID and initial AI message
    """
    # File format validation
    if not protocol_file.filename.endswith('.py'):
        raise HTTPException(
            status_code=400,
            detail="Protocol file must be in .py format"
        )
    
    # Save protocol file to temporary location
    with tempfile.TemporaryDirectory() as temp_dir:
        protocol_path = Path(temp_dir) / protocol_file.filename
        with open(protocol_path, "wb") as f:
            content = await protocol_file.read()
            f.write(content)
        
        # Read protocol content
        protocol_content = content.decode("utf-8")
        
        # Create a permanent copy for this session
        session_temp_dir = Path(tempfile.gettempdir()) / "sanitycheckAI_sessions"
        session_temp_dir.mkdir(exist_ok=True)
        
        try:
            # Create chat session
            chat_service = get_chat_service()
            session_id = chat_service.create_session(protocol_content, str(protocol_path))
            
            # Copy protocol file to session directory
            session_dir = session_temp_dir / session_id
            session_dir.mkdir(exist_ok=True)
            session_protocol_path = session_dir / protocol_file.filename
            
            with open(session_protocol_path, "w", encoding="utf-8") as f:
                f.write(protocol_content)
            
            # Update the session with permanent path
            chat_service.sessions[session_id].protocol_path = str(session_protocol_path)
            
            # Get initial message
            history = chat_service.get_history(session_id)
            initial_message = history[-1] if history else {"content": "Session started"}
            
            return {
                "session_id": session_id,
                "message": initial_message.get("content", ""),
                "protocol_name": protocol_file.filename
            }
            
        except ValueError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Configuration error: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error creating chat session: {str(e)}"
            )


@app.post("/api/chat/message")
async def send_chat_message(
    session_id: str = Form(...),
    message: str = Form(...)
):
    """
    Send a message in a chat session
    
    Args:
        session_id: Chat session ID
        message: User's message
        
    Returns:
        AI response with any actions taken
    """
    # Log the request
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Received chat message - session_id: {session_id}, message: {message}")
    
    try:
        chat_service = get_chat_service()
        response = await chat_service.send_message(session_id, message)
        logger.info(f"Response sent successfully")
        return response
        
    except ValueError as e:
        logger.error(f"ValueError: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Exception: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing message: {str(e)}"
        )


@app.get("/api/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """
    Get chat history for a session
    
    Args:
        session_id: Chat session ID
        
    Returns:
        List of messages
    """
    try:
        chat_service = get_chat_service()
        history = chat_service.get_history(session_id)
        return {"session_id": session_id, "messages": history}
        
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving history: {str(e)}"
        )


@app.get("/api/chat/image/{session_id}/{image_index}")
async def get_chat_image(session_id: str, image_index: int):
    """
    Get a captured image from chat session
    
    Args:
        session_id: Chat session ID
        image_index: Index of the image
        
    Returns:
        Image file
    """
    try:
        chat_service = get_chat_service()
        image_path = chat_service.get_image(session_id, image_index)
        
        if not os.path.exists(image_path):
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Return the image
        from PIL import Image
        import io
        
        img = Image.open(image_path)
        
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Save to bytes buffer as PNG
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        return Response(content=img_byte_arr.getvalue(), media_type="image/png")
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving image: {str(e)}"
        )


# ============================================================================
# EXPERIMENT EXECUTION ENDPOINTS
# ============================================================================

from backend.experiment_simulator import ExperimentSimulator
from backend.well_analyzer import WellAnalyzer

# Global instances
experiment_simulator = ExperimentSimulator()
well_analyzer = WellAnalyzer()


@app.post("/api/execute")
async def execute_experiment():
    """
    Start experiment execution simulation
    
    Returns:
        Experiment ID and initial data
    """
    try:
        # Create experiment with gradual contamination scenario
        experiment_id = experiment_simulator.create_experiment(
            num_timepoints=6,
            interval_seconds=10,
            contamination_scenario="gradual"
        )
        
        # Get experiment data
        experiment_data = experiment_simulator.get_experiment(experiment_id)
        
        # Analyze all wells at all timepoints
        for timepoint in experiment_data['timepoints']:
            for well in timepoint['wells']:
                # Perform dual analysis
                analysis = well_analyzer.analyze_well(
                    well['image_array'],
                    well['image_path']
                )
                
                # Add analysis results
                well['rf_prediction'] = analysis['rf_prediction']
                well['llm_prediction'] = analysis['llm_prediction']
                
                # Remove image_array (not JSON serializable)
                well.pop('image_array', None)
        
        return {
            "experiment_id": experiment_id,
            "status": "completed",
            "timepoints": experiment_data['timepoints']
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error starting experiment: {str(e)}"
        )


@app.get("/api/experiment/{experiment_id}")
async def get_experiment(experiment_id: str):
    """
    Get experiment status and results
    
    Args:
        experiment_id: Experiment ID
        
    Returns:
        Complete experiment data
    """
    try:
        experiment_data = experiment_simulator.get_experiment(experiment_id)
        return experiment_data
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving experiment: {str(e)}"
        )


@app.get("/api/well_image/{experiment_id}/{time}/{well_id}")
async def get_well_image(experiment_id: str, time: int, well_id: str):
    """
    Get well image for specific timepoint (converted to PNG for browser display)
    
    Args:
        experiment_id: Experiment ID
        time: Time in seconds
        well_id: Well ID (A1, A2, A3)
        
    Returns:
        PNG image file
    """
    try:
        image_path = experiment_simulator.get_well_image_path(
            experiment_id, time, well_id
        )
        
        if not os.path.exists(image_path):
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Convert TIFF to PNG for browser compatibility
        from PIL import Image
        import io
        
        img = Image.open(image_path)
        
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Save to bytes buffer as PNG
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        return Response(content=img_byte_arr.getvalue(), media_type="image/png")
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving image: {str(e)}"
        )


@app.post("/api/train_model")
async def train_contamination_model():
    """
    Train the Random Forest contamination detection model
    
    Returns:
        Training results
    """
    try:
        results = well_analyzer.train_rf_model()
        return {
            "status": "success",
            "results": results
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error training model: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    
    # Get port number from environment variable (default: 8000)
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )

