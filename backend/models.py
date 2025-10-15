from sqlalchemy import Column, Integer, String, Text
from database import Base 

class ReviewReport(Base):
    # This is the name of the table in the SQLite file (reviews.db)
    __tablename__ = "review_reports"
    
    # Primary Key and Index
    id = Column(Integer, primary_key=True, index=True)
    
    # Report Metadata
    filename = Column(String, index=True)
    timestamp = Column(String) # Stored as an ISO-formatted string
    
    # LLM Generated Content
    summary = Column(Text)
    
    # JSON data is stored as large Text fields, then parsed in app.py
    suggestions = Column(Text)  
    potential_bugs = Column(Text) 
