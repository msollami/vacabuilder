from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from datetime import datetime

from services.itinerary_planner import ItineraryPlanner
from pdf.generator import PDFGenerator

app = FastAPI(title="Vacation Builder API")

# CORS middleware for Electron
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
itinerary_planner = ItineraryPlanner()
pdf_generator = PDFGenerator()

class Destination(BaseModel):
    name: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class VacationRequest(BaseModel):
    destinations: List[Destination]
    preferences: str

class VacationResponse(BaseModel):
    markdown: str
    itinerary: dict

class PDFRequest(BaseModel):
    markdown: str

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "llm_loaded": itinerary_planner.is_llm_ready()}

@app.post("/api/plan", response_model=VacationResponse)
async def plan_vacation(request: VacationRequest):
    """Generate vacation itinerary based on destinations and preferences"""
    try:
        # Check if LLM is loaded
        if not itinerary_planner.is_llm_ready():
            raise HTTPException(
                status_code=503,
                detail="LLM model not loaded. Please download a GGUF model file and place it in backend/models/ directory. See README for instructions."
            )

        result = await itinerary_planner.generate_itinerary(
            destinations=request.destinations,
            preferences=request.preferences
        )
        return VacationResponse(
            markdown=result["markdown"],
            itinerary=result["itinerary"]
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in plan_vacation: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-pdf")
async def generate_pdf(request: PDFRequest):
    """Generate PDF from markdown itinerary"""
    try:
        print(f"Generating PDF...")
        pdf_path = await pdf_generator.generate(request.markdown)
        print(f"PDF saved to: {pdf_path}")
        return {"pdf_path": pdf_path, "success": True}
    except Exception as e:
        print(f"Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("Starting Vacation Builder Backend...")
    print("Loading LLM model (this may take a moment)...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
