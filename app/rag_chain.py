import os
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

# --- Configuration ---
# NOTE: API key should be loaded by FastAPI via main.py using dotenv
VECTOR_STORE_PATH = "chroma_db"
COLLECTION_NAME = "code_assistant_index"  # Must match the collection name in index_codebase.py

# Initialize global variables, these will hold the loaded RAG components
# We initialize them to None, and they are loaded during application startup.
vectorstore = None
rag_chain = None

# Define the Prompt Template
CODE_QA_TEMPLATE = """
You are an expert software developer AI assistant. Your role is to answer questions about a codebase.
Use the following context (which consists of code chunks from the codebase) to answer the question.

If the context provides relevant information, use it to give a helpful and detailed answer.
If the context doesn't contain enough information, provide what you can based on the available code and indicate what information is missing.
Only state "Answer not available in the indexed codebase" if the question is completely unrelated to the provided context.

Maintain a professional and helpful tone. When showing code, preserve proper formatting.

QUESTION: {question}

CONTEXT:
{context}

ANSWER:
"""

QA_PROMPT = PromptTemplate.from_template(CODE_QA_TEMPLATE)

def initialize_rag_components():
    """Initializes the vector store and the RAG chain."""
    global vectorstore
    global rag_chain

    # --- 1. Initialize Embedding Model ---
    # The same embedding model used for indexing must be used for retrieval
    # This is initialized here (after .env is loaded) instead of at module level
    embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")
    
    # --- 2. Load the Vector Store ---
    vectorstore = Chroma(
        persist_directory=VECTOR_STORE_PATH,
        collection_name=COLLECTION_NAME,
        embedding_function=embedding_model
    )
    print(f"Vector store loaded successfully from {VECTOR_STORE_PATH} (collection: {COLLECTION_NAME})")

    # --- 3. Create the RAG Chain ---
    # The LLM model
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.0)

    # Create the RetrievalQA chain
    # Retrieve more documents (k=10) for better context coverage
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 10}
    )
    
    rag_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": QA_PROMPT},
    )
    print("RAG chain initialized with retriever (k=10).")


def get_answer(question: str) -> str:
    """Runs the question through the initialized RAG chain."""
    if rag_chain is None:
        return "The RAG system is not initialized. Please check the backend terminal for errors related to the vector store or API key."

    # Run the chain
    result = rag_chain.invoke({"query": question})
    return result.get("result", "An unknown error occurred during retrieval.")

def list_all_document_sources() -> list:
    """Returns the source metadata for all documents in the vector store."""
    if vectorstore is None:
        return [{"error": "Vector store not initialized. Check terminal for loading errors."}]

    # Chroma stores metadata for all documents. We fetch the document IDs and then their metadata.
    # Note: Chroma's API is not standardized across versions, this approach is robust.
    try:
        # Fetch up to 1000 IDs (or adjust the limit if needed)
        ids = vectorstore._collection.get(limit=1000, include=['metadatas']).get('ids', [])

        # If no IDs, return empty list
        if not ids:
            return []

        # Get the documents including the metadatas
        results = vectorstore._collection.get(ids=ids, include=['metadatas'])

        # Extract the source from metadata
        sources = []
        for metadata in results.get('metadatas', []):
            if metadata and 'source' in metadata:
                sources.append({"source": os.path.basename(metadata['source'])}) # Use basename for cleaner output

        return sources

    except Exception as e:
        return [{"error": f"Error loading documents from vector store: {e}"}]

# Initialize RAG components upon module load (during application startup)
try:
    initialize_rag_components()
except Exception as e:
    # Print a clear error message if initialization fails, but allow app to start
    # so we can use the debug endpoint.
    print(f"\n--- CRITICAL RAG INITIALIZATION ERROR ---\n{e}\n------------------------------------------\n")
