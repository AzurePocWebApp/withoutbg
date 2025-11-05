"""FastAPI backend for withoutbg web application."""

import io
import os
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from PIL import Image
import uvicorn

# Import withoutbg package (install via: uv sync or pip install -e ../../../packages/python)
from withoutbg import WithoutBG, __version__
from withoutbg.exceptions import WithoutBGError
from withoutbg.api import StudioAPI

app = FastAPI(
    title="withoutbg API",
    description="AI-powered background removal API",
    version=__version__,
)

# CORS middleware for local development and deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model instance (initialized at startup, reused for all requests)
_model: Optional[WithoutBG] = None


@app.on_event("startup")
async def startup_event():
    """Initialize models at startup for optimal performance."""
    global _model
    print("Loading Open Source models...")
    _model = WithoutBG.opensource()
    print("✓ Models loaded and ready for inference!")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": __version__,
        "service": "withoutbg-api",
        "models_loaded": _model is not None
    }


@app.post("/api/remove-background")
async def remove_background_endpoint(
    file: UploadFile = File(...),
    format: str = Form("png"),
    quality: int = Form(95),
    api_key: Optional[str] = Form(None),
):
    """
    Remove background from a single image.
    
    Args:
        file: Image file to process
        format: Output format (png, jpg, webp)
        quality: Quality for JPEG output (1-100)
        api_key: Optional API key for cloud processing
    
    Returns:
        Processed image with background removed
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read uploaded file
        contents = await file.read()
        input_image = Image.open(io.BytesIO(contents))
        
        # Process image using appropriate model
        if api_key:
            # Use API for this specific request
            api_model = WithoutBG.api(api_key)
            result = api_model.remove_background(input_image)
        else:
            # Use pre-loaded opensource model (fast!)
            if _model is None:
                raise HTTPException(
                    status_code=503,
                    detail="Models not loaded. Server may still be starting up."
                )
            result = _model.remove_background(input_image)
        
        # Convert result to bytes
        output_buffer = io.BytesIO()
        
        # Handle format conversion
        if format.lower() in ["jpg", "jpeg"]:
            # Convert RGBA to RGB for JPEG
            if result.mode == "RGBA":
                rgb_image = Image.new("RGB", result.size, (255, 255, 255))
                rgb_image.paste(result, mask=result.split()[3])
                rgb_image.save(output_buffer, format="JPEG", quality=quality)
            else:
                result.save(output_buffer, format="JPEG", quality=quality)
            media_type = "image/jpeg"
        elif format.lower() == "webp":
            result.save(output_buffer, format="WEBP", quality=quality)
            media_type = "image/webp"
        else:  # PNG
            result.save(output_buffer, format="PNG")
            media_type = "image/png"
        
        output_buffer.seek(0)
        
        return Response(
            content=output_buffer.getvalue(),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename=withoutbg.{format}"
            }
        )
        
    except WithoutBGError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.get("/api/usage")
async def get_usage_endpoint(api_key: str):
    """
    Get API usage statistics.
    
    Args:
        api_key: API key for cloud service
    
    Returns:
        Usage statistics
    """
    try:
        api = StudioAPI(api_key)
        usage = api.get_usage()
        return JSONResponse(content=usage)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch usage: {str(e)}")


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
