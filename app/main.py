import os
import subprocess
from typing import Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from .env file FIRST
load_dotenv()

from .rag_chain import get_answer, list_all_document_sources

LOCAL_VECTOR_STORE_PATH = os.getenv("LOCAL_VECTOR_STORE_PATH", "chroma_db")
LOCAL_COLLECTION_NAME = os.getenv("LOCAL_COLLECTION_NAME", "code_assistant_local")
INDEX_SCRIPT_PATH = "scripts/index_codebase.py"

app = FastAPI(title="Code Assistant API")

# Global variables to track indexing status
indexing_in_progress = False
indexing_output = []  # Store terminal output lines
indexing_complete = False

# Add CORS middleware for frontend connection
# The persistent 400 Bad Request on OPTIONS suggests a conflict with the "*" wildcard.
# We explicitly list required methods to force the CORS handshake.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"], # <-- EXPLICITLY LISTING METHODS
    allow_headers=["*"],
)

class Question(BaseModel):
    question: str


class IndexRequest(BaseModel):
    codebase_path: str
    collection: Optional[str] = None
    output: Optional[str] = None
    chunk_size: int = 1000
    chunk_overlap: int = 100

@app.get("/")
def home():
    """Serve the frontend HTML"""
    return FileResponse("frontend/index.html")

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "Code Assistant Backend is running."}

@app.post("/index")
async def trigger_indexing(request: IndexRequest, background_tasks: BackgroundTasks):
    """Trigger indexing of a codebase"""
    global indexing_in_progress, indexing_complete, current_index_mode
    
    if indexing_in_progress:
        raise HTTPException(status_code=429, detail="Indexing already in progress")
    
    # Validate path
    if not os.path.exists(request.codebase_path):
        raise HTTPException(status_code=400, detail=f"Path does not exist: {request.codebase_path}")
    
    if not os.path.isdir(request.codebase_path):
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {request.codebase_path}")
    
    payload = {
        "script": INDEX_SCRIPT_PATH,
        "codebase_path": request.codebase_path,
        "collection": request.collection or LOCAL_COLLECTION_NAME,
        "chunk_size": request.chunk_size,
        "chunk_overlap": request.chunk_overlap,
        "output": request.output or LOCAL_VECTOR_STORE_PATH,
    }
    
    indexing_in_progress = True
    indexing_complete = False
    background_tasks.add_task(run_indexing_task, payload)
    
    return {
        "status": "started",
        "message": f"Indexing started for {request.codebase_path}. This may take a few minutes."
    }


def run_indexing_task(payload: dict):
    """Background task to run the indexing script"""
    global indexing_in_progress, indexing_output, indexing_complete
    
    try:
        indexing_output = []
        indexing_complete = False
        
        start_msg = (
            f"{'='*60}\n"
            f"Starting indexing: {payload['codebase_path']}\n"
            f"Collection: {payload['collection']} | Output: {payload['output']}\n"
            f"{'='*60}"
        )
        print(start_msg)
        indexing_output.append(start_msg)
        
        cmd = [
            "python3.9",
            payload["script"],
            payload["codebase_path"],
            "--collection", payload["collection"],
            "--chunk-size", str(payload["chunk_size"]),
            "--chunk-overlap", str(payload["chunk_overlap"]),
            "--output", payload["output"],
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=os.getcwd()
        )
        
        for line in process.stdout:
            line = line.rstrip()
            if line:
                print(line)
                indexing_output.append(line)
        
        process.wait()
        
        if process.returncode == 0:
            success_msg = "\n✅ Indexing completed successfully!"
            print(success_msg)
            indexing_output.append(success_msg)
            indexing_complete = True
        else:
            error_msg = f"\n❌ Indexing failed with exit code {process.returncode}"
            print(error_msg)
            indexing_output.append(error_msg)
            
    except Exception as e:
        error_msg = f"\n❌ Indexing error: {e}"
        print(error_msg)
        indexing_output.append(error_msg)
    finally:
        indexing_in_progress = False

@app.get("/index/status")
def indexing_status():
    """Check if indexing is in progress and get status"""
    global indexing_in_progress, indexing_complete
    return {
        "in_progress": indexing_in_progress,
        "completed": indexing_complete,
        "output_lines": len(indexing_output),
    }

@app.get("/index/output")
def get_indexing_output():
    """Get the current indexing output"""
    global indexing_output
    return {
        "output": indexing_output,
        "in_progress": indexing_in_progress,
        "completed": indexing_complete,
    }

@app.post("/ask")
async def ask_question(q: Question):
    """Ask a question about the indexed codebase"""
    try:
        # A check to ensure Pydantic model parsing succeeded
        if not q.question:
             raise ValueError("Question field is empty in the request body.")

        result = get_answer(q.question)
        return result
    except Exception as e:
        # Log the error for debugging purposes in the terminal
        print(f"--- ERROR PROCESSING /ASK REQUEST ---")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Detail: {e}")
        print(f"---------------------------------------")
        return {"error": str(e)}

@app.get("/debug/docs")
def debug_document_list():
    """Lists the source metadata for all documents currently in the vector store."""
    return list_all_document_sources()
