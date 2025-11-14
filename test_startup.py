#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, '/Users/lalitkumarverma/projects-react/code-assistant-poc')

from dotenv import load_dotenv

# Load .env
load_dotenv()

print(f"✓ .env loaded")
print(f"✓ API Key present: {bool(os.getenv('OPENAI_API_KEY'))}")
print(f"✓ API Key length: {len(os.getenv('OPENAI_API_KEY', ''))}")

print("\n--- Attempting to import rag_chain ---")
try:
    from app.rag_chain import get_answer, list_all_document_sources
    print("✅ RAG chain import successful!")
    
    print("\n--- Testing list_all_document_sources() ---")
    result = list_all_document_sources()
    if result and isinstance(result, list):
        if 'error' in result[0]:
            print(f"❌ Error: {result[0]['error']}")
        else:
            print(f"✅ Documents in vector store: {len(result)}")
            if result:
                print(f"   Sample: {result[0]}")
    else:
        print("⚠️  No documents found")
        
except Exception as e:
    print(f"❌ Failed to initialize: {e}")
    import traceback
    traceback.print_exc()

