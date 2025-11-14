# Code Assistant POC

A Retrieval-Augmented Generation (RAG) based AI code assistant that can answer questions about your codebase using semantic search and natural language processing.

## 🏗️ High-Level Architecture

### System Overview

```
┌─────────────────┐
│   User Query    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│      FastAPI Backend Server         │
│  ┌───────────────────────────────┐  │
│  │    POST /ask endpoint         │  │
│  └────────────┬──────────────────┘  │
│               │                      │
│               ▼                      │
│  ┌───────────────────────────────┐  │
│  │    RAG Chain (LangChain)     │  │
│  │  ┌─────────────────────────┐ │  │
│  │  │  1. Semantic Search     │ │  │
│  │  │  2. Context Retrieval   │ │  │
│  │  │  3. LLM Generation      │ │  │
│  │  └─────────────────────────┘ │  │
│  └───────────┬───────────────────┘  │
└──────────────┼──────────────────────┘
               │
      ┌────────┴────────┐
      │                 │
      ▼                 ▼
┌──────────────┐  ┌─────────────┐
│  ChromaDB    │  │  OpenAI     │
│  Vector DB   │  │  API        │
│              │  │             │
│ • Embeddings │  │ • LLM       │
│ • Code Chunks│  │ • Embeddings│
└──────────────┘  └─────────────┘
```

### Architecture Components

1. **FastAPI Backend** (`app/main.py`)
   - REST API server with CORS support
   - Handles user queries via `/ask` endpoint
   - Health check endpoint at `/`
   - Debug endpoint at `/debug/docs` for viewing indexed documents

2. **RAG Chain** (`app/rag_chain.py`)
   - Orchestrates the retrieval and generation pipeline
   - Uses LangChain's RetrievalQA for question answering
   - Implements semantic search over code chunks

3. **Vector Store** (ChromaDB)
   - Persistent local vector database
   - Stores code embeddings for semantic search
   - Collection: `code_assistant_index`

4. **Indexing Pipeline** (`scripts/index_codebase.py`)
   - Scans and loads code files from target directory
   - Language-aware code chunking (respects code structure)
   - Generates embeddings and populates vector store

### Data Flow

1. **Indexing Phase** (one-time setup):
   ```
   Source Code → Language Detector → Code Splitter → 
   Embedding Model → Vector Store
   ```

2. **Query Phase** (runtime):
   ```
   User Question → Embedding Model → Vector Search → 
   Relevant Code Chunks → LLM + Context → Answer
   ```

---

## 🤖 Model and Framework Choices

### Core Frameworks

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Web Framework** | FastAPI | High performance, async support, automatic API docs, type safety |
| **RAG Orchestration** | LangChain | Industry standard for RAG pipelines, extensive integrations |
| **Vector Database** | ChromaDB | Lightweight, local-first, easy setup, persistent storage |
| **Server** | Uvicorn | ASGI server with excellent performance and production-ready |

### AI Models

#### Embedding Model
- **Model**: OpenAI `text-embedding-3-small`
- **Purpose**: Convert code and queries into vector representations
- **Why**: 
  - High quality embeddings for semantic search
  - Cost-effective (smaller model)
  - Good balance of performance and accuracy
  - 1536 dimensions

#### Language Model (LLM)
- **Model**: OpenAI `gpt-3.5-turbo`
- **Purpose**: Generate natural language answers from retrieved code context
- **Why**:
  - Fast response times
  - Cost-effective for POC
  - Good code understanding capabilities
  - Suitable for production use
  - Temperature: 0.0 (deterministic, factual responses)

### Code Processing

- **Pygments**: Syntax highlighting and language detection
- **LangChain Text Splitters**: Language-aware code chunking
  - Respects code structure (functions, classes)
  - Configurable chunk size (1000 chars) and overlap (100 chars)
  - Supports multiple languages: JS, TS, Python, Swift, Kotlin, Java, etc.

### Supported Languages

The indexer currently supports:
- JavaScript/TypeScript (React, Node.js)
- Python
- Swift (iOS)
- Kotlin/Java (Android)
- Configuration files (JSON, YAML, MD)

---

## 🚀 How to Run or Test the Tool

### Prerequisites

- Python 3.9+ (preferably 3.9 for compatibility)
- OpenAI API key
- pip package manager

### 1. Initial Setup

#### Clone and navigate to the project:
```bash
cd /path/to/code-assistant-poc
```

#### Create a `.env` file with your OpenAI API key:
```bash
# Create .env file
cat > .env << 'EOF'
OPENAI_API_KEY=your_openai_api_key_here
EOF
```

Get your API key from: https://platform.openai.com/api-keys

#### Install dependencies:
```bash
pip install -r requirements.txt
```

Or using Python 3.9 specifically:
```bash
pip3.9 install -r requirements.txt
```

---

### 2. Index Your Codebase

Before running queries, you need to index your codebase. The indexer now accepts command-line arguments for flexibility:

#### Basic Usage

Index any codebase by providing the path:

```bash
python3.9 scripts/index_codebase.py /path/to/your/codebase
```

#### Examples

```bash
# Index the sample React app
python3.9 scripts/index_codebase.py ./my_codebase/mycarhub/src

# Index your own project
python3.9 scripts/index_codebase.py ~/projects/my-app/src

# Index with custom collection name
python3.9 scripts/index_codebase.py ./my_project --collection my_project_index

# Index with custom chunk size and overlap
python3.9 scripts/index_codebase.py ./my_project --chunk-size 1500 --chunk-overlap 150

# Full custom configuration
python3.9 scripts/index_codebase.py /path/to/code \
  --output ./my_vector_db \
  --collection my_collection \
  --chunk-size 2000 \
  --chunk-overlap 200
```

#### Available Options

```bash
python3.9 scripts/index_codebase.py --help
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `codebase_path` | - | *required* | Path to the codebase directory |
| `--output` | `-o` | `./chroma_db` | Output directory for vector store |
| `--collection` | `-c` | `code_assistant_index` | Collection name |
| `--chunk-size` | - | `1000` | Size of each code chunk (characters) |
| `--chunk-overlap` | - | `100` | Overlap between chunks (characters) |

**Expected Output:**
```
============================================================
CODE ASSISTANT - CODEBASE INDEXER
============================================================
Codebase path:     ./my_codebase/mycarhub/src
Output directory:  ./chroma_db
Collection name:   code_assistant_index
Chunk size:        1000 characters
Chunk overlap:     100 characters
============================================================

Starting indexing process...

✓ Loaded 16 files for JS. Created 59 chunks.
✓ Loaded 1 files for JS. Created 8 chunks.

============================================================
Total chunks created: 67
============================================================

Creating vector store with 67 chunks...
✅ Vector store created and saved to: ./chroma_db
   Collection name: code_assistant_index

============================================================
✅ INDEXING COMPLETE!
============================================================
Your codebase has been indexed and is ready for retrieval.
Start the server with: uvicorn app.main:app --host 0.0.0.0 --port 8000
============================================================
```

---

### 3. Start the Server

#### Using Python 3.9 (recommended):
```bash
python3.9 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Or using uvicorn directly:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
Vector store loaded successfully from chroma_db (collection: code_assistant_index)
RAG chain initialized.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

### 4. Test the Tool

#### Method 1: Health Check
```bash
curl http://localhost:8000/
```

**Response:**
```json
{
  "status": "ok",
  "message": "Code Assistant Backend is running."
}
```

#### Method 2: Debug - List Indexed Documents
```bash
curl http://localhost:8000/debug/docs | jq
```

**Response:**
```json
[
  {"source": "App.js"},
  {"source": "CarCard.js"},
  {"source": "Header.js"},
  ...
]
```

#### Method 3: Ask a Question
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What components are in this React app?"}'
```

**Response:**
```json
{
  "answer": "The React app contains the following components: App, Header, Footer, CarCard, CarDetails, Cars, LoginPage, AddCarPage, Sidebar, ReviewBox, and UserInformationContext..."
}
```

#### Method 4: Test Script
A test script is provided for quick verification:

```bash
python3.9 test_startup.py
```

**Expected Output:**
```
✓ .env loaded
✓ API Key present: True
✓ API Key length: 164

--- Attempting to import rag_chain ---
Vector store loaded successfully from chroma_db (collection: code_assistant_index)
RAG chain initialized.
✅ RAG chain import successful!

--- Testing list_all_document_sources() ---
✅ Documents in vector store: 201
   Sample: {'source': 'CarCard.js'}
```

---

## 📁 Project Structure

```
code-assistant-poc/
├── app/
│   ├── main.py              # FastAPI server and endpoints
│   └── rag_chain.py         # RAG pipeline implementation
├── scripts/
│   └── index_codebase.py    # Indexing script for codebase
├── chroma_db/               # Vector database storage (created after indexing)
├── my_codebase/             # Sample codebases for indexing
│   ├── mycarhub/            # React.js car dealership app
│   └── utility/             # iOS Swift project
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (API keys)
├── .gitignore              # Git ignore rules
├── test_startup.py         # Quick test/verification script
└── README.md               # This file
```

---

## 🔧 Configuration

### Vector Store Configuration
Edit `app/rag_chain.py`:
```python
VECTOR_STORE_PATH = "chroma_db"
COLLECTION_NAME = "code_assistant_index"
```

### Indexing Configuration

The indexer now accepts command-line arguments (no need to edit the script):

```bash
# Use command-line arguments for configuration
python3.9 scripts/index_codebase.py /your/codebase/path \
  --output ./chroma_db \
  --collection code_assistant_index \
  --chunk-size 1000 \
  --chunk-overlap 100
```

To change defaults permanently, edit `scripts/index_codebase.py`:
```python
DEFAULT_CHROMA_PATH = "./chroma_db"
DEFAULT_COLLECTION_NAME = "code_assistant_index"
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 100
```

### Model Configuration
Edit `app/rag_chain.py` to change models:
```python
embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.0)
```

For more powerful responses, consider:
- `gpt-4` or `gpt-4-turbo` (slower, more expensive, better quality)
- `text-embedding-3-large` (larger embeddings, better accuracy)

---

## 🧪 API Endpoints

### `GET /`
Health check endpoint.

**Response:**
```json
{"status": "ok", "message": "Code Assistant Backend is running."}
```

### `POST /ask`
Ask a question about the codebase.

**Request:**
```json
{
  "question": "How does user authentication work?"
}
```

**Response:**
```json
{
  "answer": "The user authentication is implemented using React Context API..."
}
```

### `GET /debug/docs`
List all indexed documents in the vector store.

**Response:**
```json
[
  {"source": "App.js"},
  {"source": "CarCard.js"}
]
```

---

## 🐛 Troubleshooting

### Issue: "The RAG system is not initialized"

**Cause**: Either the vector store is empty or the API key is not set.

**Solution**:
1. Check if `.env` file exists and contains `OPENAI_API_KEY`
2. Run the indexing script: `python3.9 scripts/index_codebase.py`
3. Verify documents are indexed: `curl http://localhost:8000/debug/docs`

### Issue: "ModuleNotFoundError"

**Cause**: Missing dependencies.

**Solution**:
```bash
pip3.9 install -r requirements.txt
```

### Issue: "Address already in use"

**Cause**: Port 8000 is already in use.

**Solution**:
```bash
# Kill existing server
pkill -f "uvicorn app.main"

# Or use a different port
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### Issue: PyTorch warnings

**Note**: The warnings about PyTorch are harmless for this use case. The tool uses OpenAI embeddings, not local PyTorch models.

---

## 📝 Notes

- The current indexing is configured for the sample React app in `my_codebase/mycarhub/src`
- To index a different codebase, update `CODE_DIR` in `scripts/index_codebase.py`
- The vector store persists across restarts - re-run indexing only when code changes
- Costs: Each query uses OpenAI API (embeddings + LLM tokens)
- Collection name must match between indexing and retrieval

---

## 🔐 Security

- Never commit `.env` file to version control
- Keep your OpenAI API key secure
- The `.gitignore` file excludes `.env` by default
- Use environment variables in production deployments

---

## 📈 Future Enhancements

- [ ] Add frontend UI for easier interaction
- [ ] Support for multiple codebases/collections
- [ ] Incremental indexing (update only changed files)
- [ ] Code search with filters (language, file type, etc.)
- [ ] Chat history and conversation context
- [ ] Support for local LLMs (Ollama, LLaMA)
- [ ] Authentication and rate limiting
- [ ] Docker containerization

---

## 📄 License

This is a proof-of-concept project for demonstration purposes.

---

## 🤝 Contributing

This is a POC project. For production use, consider:
- Adding proper error handling and logging
- Implementing authentication
- Adding monitoring and observability
- Using production-grade database
- Adding comprehensive tests
- Implementing rate limiting

