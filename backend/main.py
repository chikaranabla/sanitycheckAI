"""
FastAPI Application for Opentrons Protocol Sanity Check
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
import os
import tempfile
from pathlib import Path
from typing import Dict, Any

from backend.gemini_service import GeminiService

app = FastAPI(
    title="SanityCheck AI API",
    description="AI-powered physical setup verification system for Opentrons experimental protocols",
    version="1.0.0"
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


@app.get("/api/growth_analysis/{image_name}")
async def get_growth_analysis_image(image_name: str):
    """
    Serve growth analysis images from data_growth folder
    
    Args:
        image_name: Name of the image file
        
    Returns:
        Image file
    """
    # Only allow specific images
    allowed_images = [
        "plate_02_grid_layout.png",
        "A2_normal.png", 
        "A3_noisy.png",
        "A4_contamination.png"
    ]
    
    if image_name not in allowed_images:
        raise HTTPException(status_code=404, detail="Image not found")
    
    image_path = Path(__file__).parent.parent / "data_growth" / image_name
    
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image file not found")
    
    return FileResponse(str(image_path), media_type="image/png")


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

