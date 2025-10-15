import os
import json
import uvicorn
import litellm
import re
import datetime 
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import desc # For sorting history
from database import get_db, engine, Base
from models import ReviewReport as DBReviewReport

# Load environment variables from the .env file
load_dotenv()

# Set the LLM API key
litellm.api_key = os.getenv("OPENROUTER_API_KEY")

if not litellm.api_key:
    raise ValueError("OPENROUTER_API_KEY not set. Ensure it is in your .env file.")

app = FastAPI()

# --- DATABASE SETUP ---
@app.on_event("startup")
def on_startup():
    # Base is imported from database
    Base.metadata.create_all(bind=engine)

# Enable CORS for the frontend
origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ReviewReport(BaseModel):
    # This Pydantic model is used for API requests/responses
    filename: str
    summary: str
    suggestions: Dict[str, Any]
    potential_bugs: Dict[str, Any]
    # The ID is critical for deletion and must be included in the response
    id: int | None = None
    timestamp: str | None = None

# --- API ENDPOINTS ---

@app.post("/api/review", response_model=ReviewReport, summary="Generate Code Review")
async def review_code(code_file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Analyzes an uploaded code file using an LLM, saves the report to the database, 
    and returns the structured review report.
    """
    if not code_file.filename:
        raise HTTPException(status_code=400, detail="No file was uploaded.")

    file_size_limit_mb = 1
    if code_file.size > file_size_limit_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File size exceeds the limit of {file_size_limit_mb}MB.")

    try:
        content = await code_file.read()
        code_string = content.decode('utf-8')

        # Updated prompt for reliable structured JSON output
        prompt = (
            f"You are an expert software engineer. Review the following code from the file '{code_file.filename}'. "
            f"Analyze it for readability, modularity, best practices, performance, and potential bugs. "
            f"You MUST respond with a JSON object ONLY. The JSON must have the following structure and use the exact keys: "
            f"{{ 'filename': '...', 'summary': '...', 'suggestions': {{ 'readability': '...', 'modularity': '...', 'best_practices': '...', 'performance': '...' }}, 'potential_bugs': {{ 'reproducibility': '...', 'parameter_validation': '...' }} }} "
            f"Ensure the JSON output is well-formed and can be parsed directly. Do not include any text before or after the JSON.\n\n"
            f"Code to review:\n\n{code_string}"
        )

        litellm_response = litellm.completion(
            model="openrouter/openai/gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful and professional code review assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Get the raw response from the LLM
        raw_response = litellm_response.choices[0].message.content

        # Use regex to find and extract the JSON object from the response
        match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        if not match:
            print("Failed to find JSON object in LLM response. Raw response:\n", raw_response)
            raise HTTPException(status_code=500, detail="LLM response was not valid JSON.")
        
        json_string = match.group(0)

        # Parse the JSON string
        review_data = json.loads(json_string)
        current_time = datetime.datetime.now().isoformat()

        # --- DATABASE WRITE ---
        db_report = DBReviewReport(
            filename=review_data.get('filename', code_file.filename),
            summary=review_data.get('summary', 'No summary provided.'),
            suggestions=json.dumps(review_data.get('suggestions', {})),
            potential_bugs=json.dumps(review_data.get('potential_bugs', {})),
            timestamp=current_time
        )
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
        # --- END DATABASE WRITE ---

        return ReviewReport(
            id=db_report.id,
            filename=db_report.filename,
            summary=db_report.summary,
            suggestions=json.loads(db_report.suggestions),
            potential_bugs=json.loads(db_report.potential_bugs),
            timestamp=db_report.timestamp
        )

    except json.JSONDecodeError:
        print("Failed to parse JSON. Raw response was not valid JSON.")
        raise HTTPException(status_code=500, detail="LLM response was not valid JSON.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during code review.")


@app.get("/api/history", response_model=List[ReviewReport], summary="Get Review History")
def get_review_history(db: Session = Depends(get_db)):
    """
    Retrieves a list of all saved code review reports from the database, 
    ordered by most recent first.
    """
    # Use desc() to sort by timestamp descending (most recent first)
    reports = db.query(DBReviewReport).order_by(desc(DBReviewReport.timestamp)).all()
    
    # Convert database objects back to Pydantic models for the response
    response_reports = []
    for report in reports:
        response_reports.append(ReviewReport(
            id=report.id,
            filename=report.filename,
            summary=report.summary,
            suggestions=json.loads(report.suggestions),
            potential_bugs=json.loads(report.potential_bugs),
            timestamp=report.timestamp
        ))
    return response_reports

@app.delete("/api/review/{report_id}", summary="Delete Review Report")
def delete_review_report(report_id: int, db: Session = Depends(get_db)):
    """
    Deletes a specific review report by its ID.
    """
    report = db.query(DBReviewReport).filter(DBReviewReport.id == report_id).first()
    
    if report is None:
        raise HTTPException(status_code=404, detail="Review Report not found")
        
    db.delete(report) # Stages the object for deletion
    db.commit()      # Executes the DELETE statement on the database
    
    return {"message": f"Review Report with ID {report_id} deleted successfully."}


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
