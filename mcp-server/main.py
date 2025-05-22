from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
from typing import Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="CVE Database MCP Server",
              description="Model Context Persistence server for CVE database interactions")

def get_database_url():
    # If DATABASE_URL is explicitly set, use it
    if os.getenv("DATABASE_URL"):
        return os.getenv("DATABASE_URL")
    
    # Otherwise, construct from individual components
    return "postgresql://{}:{}@{}:{}/{}".format(
        os.getenv("DB_USER", "user"),
        os.getenv("DB_PASSWORD", "password"),
        os.getenv("DB_HOST", "localhost"),
        os.getenv("DB_PORT", "5432"),
        os.getenv("DB_NAME", "database")
    )

engine = create_engine(get_database_url())

@app.get("/schema")
async def get_schema():
    """Return the database schema for context"""
    with engine.connect() as conn:
        tables = conn.execute(text("""
            SELECT table_name, column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
        """))
        
        schema = {}
        for table, column, dtype in tables:
            if table not in schema:
                schema[table] = []
            schema[table].append({"column": column, "type": dtype})
            
        return schema

@app.post("/query")
async def execute_query(query_data: Dict[Any, Any]):
    """Execute a SQL query and return results"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query_data["query"]))
            return {"results": [dict(row) for row in result]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/tables/{table_name}/sample")
async def get_table_sample(table_name: str):
    """Get a sample of records from a table"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT 5"))
            return {"results": [dict(row) for row in result]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
