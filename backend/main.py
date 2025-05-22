from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="MoreFixes Backend API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgrescvedumper:a42a18537d74c3b7e584c769152c3d@db:5432/postgrescvedumper")
engine = create_engine(DATABASE_URL)

# Query processor URL
QUERY_PROCESSOR_URL = os.getenv("QUERY_PROCESSOR_URL", "http://query-processor:5000")

class Query(BaseModel):
    query: str

@app.get("/")
async def read_root():
    return {"message": "Welcome to MoreFixes Backend API"}

@app.get("/test-queries/{query_type}")
async def test_query(query_type: str):
    """
    Test endpoint to execute predefined queries
    query_type options: tables, sample_cve, count_cve, recent_cve
    """
    queries = {
        "tables": "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'",
        "sample_cve": "SELECT * FROM cve LIMIT 5",
        "count_cve": "SELECT COUNT(*) as total_cves FROM cve",
        "recent_cve": "SELECT cve_id, description, published_date FROM cve ORDER BY published_date DESC LIMIT 5"
    }
    
    if query_type not in queries:
        raise HTTPException(status_code=400, detail=f"Invalid query type. Available types: {list(queries.keys())}")
    
    try:
        with engine.connect() as connection:
            result = connection.execute(text(queries[query_type]))
            rows = []
            for row in result:
                # Convert SQLAlchemy Row to dict properly
                row_dict = {}
                for column, value in row._mapping.items():
                    row_dict[column] = str(value) if value is not None else None
                rows.append(row_dict)
            
            logger.info(f"Test query '{query_type}' executed successfully")
            return {
                "query_type": query_type,
                "sql_query": queries[query_type],
                "results": rows
            }
    except Exception as e:
        logger.error(f"Database error in test query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/query")
async def process_query(query: Query):
    try:
        logger.info(f"Processing query: {query.query}")
        
        # Send the query to the query processor
        async with httpx.AsyncClient() as client:
            logger.info(f"Sending request to query processor at {QUERY_PROCESSOR_URL}")
            response = await client.post(
                f"{QUERY_PROCESSOR_URL}/process",
                json={"query": query.query}
            )
            
            if response.status_code != 200:
                logger.error(f"Query processor error: {response.text}")
                raise HTTPException(status_code=500, detail="Query processing failed")
            
            processor_response = response.json()
            sql_query = processor_response["sql_query"]
            logger.info(f"Generated SQL query: {sql_query}")
            
            # Execute the SQL query
            with engine.connect() as connection:
                try:
                    result = connection.execute(text(sql_query))
                    rows = []
                    for row in result:
                        row_dict = dict(row)
                        # Convert datetime objects to ISO format strings
                        if row_dict.get('published_date'):
                            row_dict['published_date'] = row_dict['published_date']
                        rows.append(row_dict)
                    
                    logger.info(f"Query executed successfully, found {len(rows)} results")
                    return {
                        "query": query.query,
                        "sql_query": sql_query,
                        "results": rows
                    }
                except Exception as e:
                    logger.error(f"Database error: {str(e)}")
                    logger.error(f"SQL Query that failed: {sql_query}")
                    raise
            
    except httpx.RequestError as e:
        logger.error(f"Query processor connection error: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not connect to query processor")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/execute-sql")
async def execute_sql(query: Query):
    try:
        # Clean up the query: normalize whitespace and remove any problematic characters
        cleaned_query = ' '.join(query.query.split())
        logger.info(f"Executing SQL query: {cleaned_query}")
        
        # Execute the SQL query
        with engine.connect() as connection:
            try:
                result = connection.execute(text(cleaned_query))
                rows = []
                for row in result:
                    row_dict = dict(row._mapping)
                    # Convert datetime objects to ISO format strings
                    if row_dict.get('published_date'):
                        row_dict['published_date'] = row_dict['published_date']
                    rows.append(row_dict)
                
                logger.info(f"Query executed successfully, found {len(rows)} results")
                return {
                    "query": cleaned_query,
                    "results": rows
                }
            except Exception as e:
                logger.error(f"Database error: {str(e)}")
                logger.error(f"SQL Query that failed: {cleaned_query}")
                raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.get("/health")
async def health_check():
    try:
        # Test database connection
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)} 