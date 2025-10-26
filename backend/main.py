"""
FastAPI Application for Opentrons Protocol Sanity Check
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import tempfile
from pathlib import Path
from typing import Dict, Any

from backend.gemini_service import GeminiService

app = FastAPI(
    title="Opentrons Protocol Sanity Check API",
    description="Physical setup verification system for Opentrons experimental protocols",
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
    return {"message": "Opentrons Protocol Sanity Check API"}


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

