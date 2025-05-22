from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import spacy
from typing import Dict, Any
import re
from datetime import datetime

app = FastAPI(title="MoreFixes Query Processor")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

class Query(BaseModel):
    query: str

def extract_time_constraints(doc):
    """Extract time-related information from the query."""
    time_info = {
        "period": None,
        "specific_month": None,
        "specific_year": None
    }
    
    # Simple pattern matching for common time expressions
    if re.search(r"last (month|week|year)", doc.text.lower()):
        time_info["period"] = re.search(r"last (month|week|year)", doc.text.lower()).group(1)
    
    # Match specific month and year (e.g., "May 2025")
    month_year_match = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})", doc.text)
    if month_year_match:
        time_info["specific_month"] = month_year_match.group(1)
        time_info["specific_year"] = month_year_match.group(2)
    
    return time_info

def extract_severity(doc):
    """Extract severity information from the query."""
    severity_keywords = {
        "critical": "CRITICAL",
        "high": "HIGH",
        "medium": "MEDIUM",
        "low": "LOW"
    }
    
    for token in doc:
        if token.text.lower() in severity_keywords:
            return severity_keywords[token.text.lower()]
    return None

def build_sql_query(query_info: Dict[str, Any]) -> str:
    """Build SQL query based on extracted information."""
    # Base query joining necessary tables
    base_query = """
    SELECT DISTINCT
        cve.cve_id,
        cve.description,
        cve.published_date,
        to_timestamp(cve.published_date, 'YYYY-MM-DD"T"HH24:MI"Z"') as published_date_ts,
        cve.cvss3_base_score as severity_score,
        cve.cvss3_base_severity as severity,
        STRING_AGG(DISTINCT repo.repo_url, ', ') as repositories,
        STRING_AGG(DISTINCT cwe.cwe_id, ', ') as cwe_ids
    FROM cve
    LEFT JOIN fixes ON cve.cve_id = fixes.cve_id
    LEFT JOIN repository repo ON fixes.repo_url = repo.repo_url
    LEFT JOIN cwe_classification cwc ON cve.cve_id = cwc.cve_id
    LEFT JOIN cwe ON cwc.cwe_id = cwe.cwe_id
    """
    
    conditions = []
    time_info = query_info.get("time_info", {})
    
    if time_info.get("specific_month") and time_info.get("specific_year"):
        month_num = datetime.strptime(time_info["specific_month"], "%B").month
        conditions.append(
            f"to_timestamp(cve.published_date, 'YYYY-MM-DD''T''HH24:MI''Z''') >= '{time_info['specific_year']}-{month_num:02d}-01'::timestamp AND "
            f"to_timestamp(cve.published_date, 'YYYY-MM-DD''T''HH24:MI''Z''') < '{time_info['specific_year']}-{month_num:02d}-01'::timestamp + INTERVAL '1 month'"
        )
    elif time_info.get("period"):
        period = time_info["period"]
        conditions.append(f"""to_timestamp(cve.published_date, 'YYYY-MM-DD"T"HH24:MI"Z"') >= CURRENT_TIMESTAMP - INTERVAL '1 {period}'""")
    
    if query_info.get("severity"):
        conditions.append(f"cve.cvss3_base_severity = '{query_info['severity']}'")
    
    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)
    
    base_query += "\nGROUP BY cve.cve_id, cve.description, cve.published_date, published_date_ts, cve.cvss3_base_score, cve.cvss3_base_severity"
    base_query += "\nORDER BY published_date_ts DESC LIMIT 100"
    
    return base_query

@app.post("/process")
async def process_query(query: Query):
    try:
        # Process the query with spaCy
        doc = nlp(query.query)
        
        # Extract relevant information
        query_info = {
            "time_info": extract_time_constraints(doc),
            "severity": extract_severity(doc)
        }
        
        # Build SQL query
        sql_query = build_sql_query(query_info)
        
        return {
            "sql_query": sql_query,
            "extracted_info": query_info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 