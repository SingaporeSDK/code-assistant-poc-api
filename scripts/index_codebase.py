#!/usr/bin/env python3
"""
Codebase indexer using LOCAL embeddings (no OpenAI required)
This version works offline using HuggingFace sentence-transformers
"""
import os
import sys
import argparse
from dotenv import load_dotenv

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

# Load environment variables
load_dotenv()

# --- DEFAULT CONFIGURATION ---
DEFAULT_CHROMA_PATH = "./chroma_db"
DEFAULT_COLLECTION_NAME = "code_assistant_local"
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 100
DEFAULT_EMBED_MODEL = os.getenv("LOCAL_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Define source extensions
SOURCE_EXTENSIONS = [
    "js", "jsx", "ts", "tsx", "py", "json", "md", "kt", "java",
    "xml", "gradle", "swift", "m", "h", "css", "html", "yaml", "toml", "config"
]

# Directories to exclude
EXCLUDE_DIRS = {
    "node_modules", "build", "dist", "out", ".next", ".nuxt",
    "vendor", "venv", "env", ".env", "__pycache__", ".git",
    "coverage", ".pytest_cache", ".mypy_cache", "target",
    "bin", "obj", "Debug", "Release", "Pods", "DerivedData"
}

# Language mapping
LANGUAGE_MAPPING = {
    ("js", "jsx", "ts", "tsx"): Language.JS,
    ("swift", "m", "h", "plist"): Language.SWIFT,
    ("kt", "java", "gradle", "xml"): Language.KOTLIN,
    ("py"): Language.PYTHON,
    ("json", "yaml", "md", "config"): Language.JS
}

def should_exclude_path(path: str) -> bool:
    """Check if a path should be excluded"""
    path_parts = os.path.normpath(path).split(os.sep)
    return any(exclude_dir in path_parts for exclude_dir in EXCLUDE_DIRS)

def load_and_split_code(directory: str, chunk_size: int = 1000, chunk_overlap: int = 100):
    """Load and split code files"""
    all_chunks = []
    excluded_count = 0

    for extensions, lang_constant in LANGUAGE_MAPPING.items():
        documents = []

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
    """Create vector store with batch processing"""
    if not chunks:
        print("⚠️  WARNING: No code chunks were found.")
        return None

    print(f"Creating vector store with {len(chunks)} chunks using LOCAL embeddings...")
    print("(First run may take time to download the model)")
    
    BATCH_SIZE = 1000
    
    if len(chunks) > BATCH_SIZE:
        print(f"⚙️  Processing in batches of {BATCH_SIZE}...")
        
        vector_store = None
        total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE
        
        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i:i + BATCH_SIZE]
            batch_num = (i // BATCH_SIZE) + 1
            
            print(f"   Batch {batch_num}/{total_batches} ({len(batch)} chunks)...", end=" ")
            
            try:
                if vector_store is None:
                    vector_store = Chroma.from_documents(
                        documents=batch,
                        embedding=embeddings,
                        persist_directory=path,
                        collection_name=collection_name
                    )
                else:
                    vector_store.add_documents(batch)
                
                print("✓")
            except Exception as e:
                print(f"❌ Error: {e}")
                raise
        
        print(f"\n✅ Vector store created with {len(chunks)} chunks")
    else:
        vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=path,
            collection_name=collection_name
        )
        print(f"✅ Vector store created")
    
    print(f"   Collection: {collection_name}")
    print(f"   Location: {path}")
    return vector_store

def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Index codebase using LOCAL embeddings (no internet required)",
    )
    
    parser.add_argument("codebase_path", type=str, help="Path to codebase")
    parser.add_argument("-o", "--output", type=str, default=DEFAULT_CHROMA_PATH)
    parser.add_argument("-c", "--collection", type=str, default=DEFAULT_COLLECTION_NAME)
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    parser.add_argument("--chunk-overlap", type=int, default=DEFAULT_CHUNK_OVERLAP)
    
    return parser.parse_args()

def main():
    """Main function"""
    args = parse_arguments()
    
    print("\n" + "="*60)
    print("CODE ASSISTANT - LOCAL INDEXER (Offline)")
    print("="*60)
    print(f"Codebase path:  {args.codebase_path}")
    print(f"Output:         {args.output}")
    print(f"Collection:     {args.collection}")
    print(f"Embedding:      HuggingFace (Local)")
    print("="*60 + "\n")
    
    if not os.path.exists(args.codebase_path):
        print(f"❌ ERROR: Directory '{args.codebase_path}' does not exist.")
        sys.exit(1)
    
    print("Initializing local embedding model (may download on first run)...")
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name=DEFAULT_EMBED_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        print("✓ Model ready\n")
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        sys.exit(1)
    
    try:
        chunks = load_and_split_code(
            args.codebase_path,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap
        )
        
        if not chunks:
            print("\n❌ No code files found!")
            sys.exit(1)
        
        vector_store = create_vector_store(chunks, embeddings, args.output, args.collection)
        
        if vector_store:
            print("\n" + "="*60)
            print("✅ INDEXING COMPLETE (LOCAL MODE)")
            print("="*60)
            print("Your codebase is indexed with LOCAL embeddings")
            print("No internet connection required for querying!")
            print("="*60 + "\n")
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

