import os
import sys
import argparse
from dotenv import load_dotenv

# Ensure these imports are correct after solving previous errors
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from langchain_community.vectorstores import Chroma

# Load environment variables
load_dotenv()

# --- DEFAULT CONFIGURATION ---
DEFAULT_CHROMA_PATH = "./chroma_db"
DEFAULT_COLLECTION_NAME = "code_assistant_index"
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 100

# Define a list of file extensions that contain useful text/code/config
# Binary files (like .png, .jpg, .zip) are explicitly excluded.
SOURCE_EXTENSIONS = [
    "js", "jsx", "ts", "tsx", "py", "json", "md", "kt", "java",
    "xml", "gradle", "swift", "m", "h", "css", "html", "yaml", "toml", "config"
]

# Directories to exclude (common build/dependency folders)
EXCLUDE_DIRS = {
    "node_modules", "build", "dist", "out", ".next", ".nuxt",
    "vendor", "venv", "env", ".env", "__pycache__", ".git",
    "coverage", ".pytest_cache", ".mypy_cache", "target",
    "bin", "obj", "Debug", "Release", "Pods", "DerivedData"
}
# -------------------------------------------

# Map extensions to their correct LangChain Language constant (assuming ALL CAPS works)
LANGUAGE_MAPPING = {
    ("js", "jsx", "ts", "tsx"): Language.JS, # React/Web Code
    ("swift", "m", "h", "plist"): Language.SWIFT,     # iOS Code
    ("kt", "java", "gradle", "xml"): Language.KOTLIN, # Android Code
    ("py"): Language.PYTHON,                          # Utility Scripts
    # For common config files, you can use a generic splitter or TEXT:
    ("json", "yaml", "md", "config"): Language.JS # Use JS parser for structural text/JSON
}

# Initialize Models (Assuming API Key is set in .env)
EMBEDDING_MODEL = OpenAIEmbeddings(model="text-embedding-3-small")
LLM = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.1)


def should_exclude_path(path: str) -> bool:
    """Check if a path should be excluded based on EXCLUDE_DIRS"""
    path_parts = os.path.normpath(path).split(os.sep)
    return any(exclude_dir in path_parts for exclude_dir in EXCLUDE_DIRS)

def load_and_split_code(directory: str, chunk_size: int = 1000, chunk_overlap: int = 100):
    """
    Load code files from a directory and split them into chunks.
    
    Args:
        directory: Path to the codebase directory
        chunk_size: Size of each code chunk (default: 1000)
        chunk_overlap: Overlap between chunks (default: 100)
    
    Returns:
        List of document chunks
    """
    all_chunks = []
    excluded_count = 0

    for extensions, lang_constant in LANGUAGE_MAPPING.items():
        documents = []

        # 1. Load Documents for the current language group
        for ext in extensions:
            glob_pattern = f"**/*.{ext}"

            try:
                loader = DirectoryLoader(
                    directory, glob=glob_pattern, recursive=True,
                    loader_cls=TextLoader, 
                    loader_kwargs={"encoding": "utf-8"},
                    silent_errors=True,
                    show_progress=False
                )
                loaded_docs = loader.load()
                
                # Filter out files from excluded directories
                filtered_docs = []
                for doc in loaded_docs:
                    source_path = doc.metadata.get('source', '')
                    if should_exclude_path(source_path):
                        excluded_count += 1
                    else:
                        filtered_docs.append(doc)
                
                documents.extend(filtered_docs)
            except Exception as e:
                print(f"Warning: Error loading {ext} files: {e}")
                continue

        if not documents:
            continue

        # 2. Split Documents using the correct language splitter
        splitter = RecursiveCharacterTextSplitter.from_language(
            language=lang_constant,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        chunks = splitter.split_documents(documents)
        all_chunks.extend(chunks)
        print(f"✓ Loaded {len(documents)} files for {lang_constant.name}. Created {len(chunks)} chunks.")

    print(f"\n{'='*60}")
    if excluded_count > 0:
        print(f"⚙️  Excluded {excluded_count} files from directories like: {', '.join(list(sorted(EXCLUDE_DIRS))[:5])}...")
    print(f"Total chunks created: {len(all_chunks)}")
    print(f"{'='*60}\n")
    return all_chunks


def create_vector_store(chunks, embeddings, path, collection_name):
    """
    Creates and persists the Chroma vector store with batch processing.
    
    Args:
        chunks: List of document chunks to index
        embeddings: Embedding model to use
        path: Path to store the vector database
        collection_name: Name of the collection
    
    Returns:
        Vector store instance or None if no chunks
    """
    if not chunks:
        print("⚠️  WARNING: No code chunks were found. Vector store not created.")
        print("   Please check if the directory contains supported file types.")
        return None

    print(f"Creating vector store with {len(chunks)} chunks...")
    
    # For large codebases, process in batches to avoid OpenAI API limits
    # OpenAI embedding API has a limit of ~300k tokens per request
    # We'll use smaller batches to be safe (1000 chunks at a time)
    BATCH_SIZE = 1000
    
    if len(chunks) > BATCH_SIZE:
        print(f"⚙️  Large codebase detected. Processing in batches of {BATCH_SIZE}...")
        
        vector_store = None
        total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE
        
        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i:i + BATCH_SIZE]
            batch_num = (i // BATCH_SIZE) + 1
            
            print(f"   Processing batch {batch_num}/{total_batches} ({len(batch)} chunks)...", end=" ")
            
            try:
                if vector_store is None:
                    # Create the vector store with the first batch
                    vector_store = Chroma.from_documents(
                        documents=batch,
                        embedding=embeddings,
                        persist_directory=path,
                        collection_name=collection_name
                    )
                else:
                    # Add subsequent batches to existing store
                    vector_store.add_documents(batch)
                
                print("✓")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                if "max_tokens" in str(e).lower():
                    print(f"   Reducing batch size may help. Try re-running with --chunk-size 500")
                raise
        
        print(f"\n✅ Vector store created with {len(chunks)} chunks across {total_batches} batches")
    else:
        # For smaller codebases, process in one go
        vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=path,
            collection_name=collection_name
        )
        print(f"✅ Vector store created and saved to: {path}")
    
    print(f"   Collection name: {collection_name}")
    return vector_store


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Index a codebase for RAG-based code assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Index a specific codebase directory
  python3.9 scripts/index_codebase.py /path/to/your/codebase

  # Index with custom collection name
  python3.9 scripts/index_codebase.py ./my_project --collection my_project_index

  # Index with custom chunk size
  python3.9 scripts/index_codebase.py ./my_project --chunk-size 1500 --chunk-overlap 150

  # Index with all custom options
  python3.9 scripts/index_codebase.py /path/to/code \\
    --output ./my_vector_db \\
    --collection my_collection \\
    --chunk-size 2000 \\
    --chunk-overlap 200
        """
    )
    
    parser.add_argument(
        "codebase_path",
        type=str,
        help="Path to the codebase directory you want to index"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=DEFAULT_CHROMA_PATH,
        help=f"Output directory for vector store (default: {DEFAULT_CHROMA_PATH})"
    )
    
    parser.add_argument(
        "-c", "--collection",
        type=str,
        default=DEFAULT_COLLECTION_NAME,
        help=f"Collection name for the vector store (default: {DEFAULT_COLLECTION_NAME})"
    )
    
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help=f"Size of each code chunk in characters (default: {DEFAULT_CHUNK_SIZE})"
    )
    
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=DEFAULT_CHUNK_OVERLAP,
        help=f"Overlap between chunks in characters (default: {DEFAULT_CHUNK_OVERLAP})"
    )
    
    return parser.parse_args()


def main():
    """Main function to run the indexing process."""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Display configuration
    print("\n" + "="*60)
    print("CODE ASSISTANT - CODEBASE INDEXER")
    print("="*60)
    print(f"Codebase path:     {args.codebase_path}")
    print(f"Output directory:  {args.output}")
    print(f"Collection name:   {args.collection}")
    print(f"Chunk size:        {args.chunk_size} characters")
    print(f"Chunk overlap:     {args.chunk_overlap} characters")
    print("="*60 + "\n")
    
    # Validate codebase directory
    if not os.path.exists(args.codebase_path):
        print(f"❌ ERROR: Directory '{args.codebase_path}' does not exist.")
        print("   Please provide a valid path to your codebase.")
        sys.exit(1)
    
    if not os.path.isdir(args.codebase_path):
        print(f"❌ ERROR: '{args.codebase_path}' is not a directory.")
        sys.exit(1)
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ ERROR: OPENAI_API_KEY environment variable not set.")
        print("   Please create a .env file with your OpenAI API key.")
        sys.exit(1)
    
    print("Starting indexing process...\n")
    
    try:
        # STEP 1: Load and split code
        chunks = load_and_split_code(
            args.codebase_path,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap
        )
        
        if not chunks:
            print("\n❌ No code files found to index!")
            print(f"   Supported extensions: {', '.join(SOURCE_EXTENSIONS)}")
            sys.exit(1)
        
        # STEP 2: Create vector store
        vector_store = create_vector_store(
            chunks,
            EMBEDDING_MODEL,
            args.output,
            args.collection
        )
        
        if vector_store:
            print("\n" + "="*60)
            print("✅ INDEXING COMPLETE!")
            print("="*60)
            print(f"Your codebase has been indexed and is ready for retrieval.")
            print(f"Start the server with: uvicorn app.main:app --host 0.0.0.0 --port 8000")
            print("="*60 + "\n")
        else:
            print("\n❌ Vector store creation failed.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Indexing interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
