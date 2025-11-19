#!/usr/bin/env python3
"""
Test GraphRAG directly from terminal

Usage:
    python3 test_graphrag.py "What components are in this React app?"
    python3 test_graphrag.py --health
    python3 test_graphrag.py --init

Note: Make sure to use the same Python environment as your server.
If using a virtual environment, activate it first:
    source .venv/bin/activate  # or your venv path
"""

import os
import sys
import argparse
from pathlib import Path

# Check if we're in a virtual environment
venv_paths = [
    Path(__file__).parent / ".venv" / "bin" / "python",
    Path(__file__).parent / "venv" / "bin" / "python",
    Path.home() / ".venv" / "bin" / "python",
]

if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    # Not in a virtual environment - check if one exists
    for venv_py in venv_paths:
        if venv_py.exists():
            venv_dir = venv_py.parent.parent
            print(f"\n⚠️  WARNING: You're not using a virtual environment!")
            print(f"   A virtual environment was found at: {venv_dir}")
            print(f"   Activate it first:")
            print(f"   \tsource {venv_dir}/bin/activate")
            print(f"   Then run this script again.\n")
            print(f"   Continuing with system Python anyway...\n")
            break

# Try to import dotenv, give helpful error if not available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not found.")
    print("   Make sure you're using the same Python environment as your server.")
    print("   If using a virtual environment, activate it first:")
    print("   \tsource .venv/bin/activate  # or: source venv/bin/activate")
    print("   Then install dependencies:")
    print("   \tpip install -r requirements.txt\n")
    sys.exit(1)

def test_health():
    """Test system health checks"""
    print("\n" + "="*60)
    print("🔍 SYSTEM HEALTH CHECK")
    print("="*60 + "\n")
    
    checks = {}
    
    # Check vector store
    print("1️⃣ Checking Vector Store...")
    try:
        from app.graph_rag import vectorstore
        if vectorstore is None:
            print("   ❌ Vector store not initialized")
            checks["vectorstore"] = False
        else:
            try:
                count = vectorstore._collection.count()
                print(f"   ✅ Vector store OK ({count} documents)")
                checks["vectorstore"] = True
            except Exception as e:
                print(f"   ❌ Error counting documents: {e}")
                checks["vectorstore"] = False
    except Exception as e:
        print(f"   ❌ Error loading vector store: {e}")
        checks["vectorstore"] = False
    
    # Check graph loader
    print("\n2️⃣ Checking Graph Loader...")
    try:
        from app.graph_loader import get_graph_loader
        graph_loader = get_graph_loader()
        print(f"   📡 Graph API URL: {graph_loader.graph_url}")
        if graph_loader.is_loaded():
            node_count = len(graph_loader.nodes)
            edge_count = len(graph_loader.edges)
            print(f"   ✅ Graph loaded: {node_count} nodes, {edge_count} edges")
            checks["graph"] = True
        else:
            print(f"   ❌ Graph not loaded - analytics API may not be running")
            print(f"      Try: cd my_codebase/mycarhub-fleet-analytics && npm run dev")
            checks["graph"] = False
    except Exception as e:
        print(f"   ❌ Error loading graph: {e}")
        checks["graph"] = False
    
    # Check LLM
    print("\n3️⃣ Checking LLM...")
    try:
        from app.llm_factory import get_llm, get_current_provider
        provider = get_current_provider()
        print(f"   📦 Provider: {provider}")
        llm = get_llm()
        print(f"   ✅ LLM initialized successfully")
        checks["llm"] = True
    except Exception as e:
        print(f"   ❌ Error initializing LLM: {e}")
        import traceback
        traceback.print_exc()
        checks["llm"] = False
    
    # Check GraphRAG chain
    print("\n4️⃣ Checking GraphRAG Chain...")
    try:
        from app.graph_rag import graph_rag_chain
        if graph_rag_chain is None:
            print("   ❌ GraphRAG chain not initialized")
            checks["graphrag"] = False
        else:
            print("   ✅ GraphRAG chain initialized")
            checks["graphrag"] = True
    except Exception as e:
        print(f"   ❌ Error checking GraphRAG chain: {e}")
        checks["graphrag"] = False
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    all_ok = all(checks.values())
    for name, status in checks.items():
        icon = "✅" if status else "❌"
        print(f"   {icon} {name}")
    
    if all_ok:
        print("\n✅ All systems ready!")
    else:
        print("\n⚠️  Some systems need attention")
        if not checks.get("vectorstore"):
            print("\n   💡 Fix vector store: python3.9 scripts/index_codebase.py <path>")
        if not checks.get("graph"):
            print("\n   💡 Fix graph: cd my_codebase/mycarhub-fleet-analytics && npm run dev")
        if not checks.get("llm"):
            print("\n   💡 Fix LLM: Check .env and gcloud auth")
    
    return all_ok


def test_init():
    """Test GraphRAG initialization"""
    print("\n" + "="*60)
    print("🚀 TESTING GRAPHRAG INITIALIZATION")
    print("="*60 + "\n")
    
    try:
        from app.graph_rag import initialize_graph_rag
        print("Initializing GraphRAG...\n")
        initialize_graph_rag()
        print("\n✅ GraphRAG initialized successfully!")
        return True
    except Exception as e:
        print(f"\n❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_query(question: str, use_graph_rag: bool = True):
    """Test a query"""
    print("\n" + "="*60)
    print(f"💬 TESTING QUERY: {'GraphRAG' if use_graph_rag else 'RAG'}")
    print("="*60 + "\n")
    print(f"Question: {question}\n")
    
    try:
        if use_graph_rag:
            from app.graph_rag import get_graph_rag_answer
            result = get_graph_rag_answer(question)
        else:
            from app.rag_chain import get_answer
            result = get_answer(question)
        
        print("="*60)
        print("📝 ANSWER")
        print("="*60)
        print(result.get("answer", "No answer"))
        
        if result.get("sources"):
            print("\n" + "="*60)
            print("📄 SOURCES")
            print("="*60)
            for i, src in enumerate(result["sources"][:5], 1):
                print(f"\n{i}. {src.get('source', 'Unknown')}")
                print(f"   {src.get('content', '')[:200]}...")
        
        if result.get("graph_context"):
            print("\n" + "="*60)
            print("🕸️  GRAPH CONTEXT")
            print("="*60)
            graph_ctx = result["graph_context"]
            if graph_ctx and graph_ctx != "No graph relationships found.":
                # Show first 500 chars
                print(graph_ctx[:500])
                if len(graph_ctx) > 500:
                    print(f"\n... (showing first 500 chars of {len(graph_ctx)} total)")
            else:
                print("No graph context found")
        
        if result.get("nodes_found") is not None:
            print(f"\n🕸️  Graph nodes found: {result['nodes_found']}")
        
        print("\n" + "="*60)
        print("✅ Query completed successfully!")
        print("="*60 + "\n")
        
        return True
    except Exception as e:
        print(f"\n❌ Query failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description="Test GraphRAG system")
    parser.add_argument(
        "question",
        nargs="?",
        help="Question to ask (optional if using --health or --init)",
    )
    parser.add_argument(
        "--health",
        action="store_true",
        help="Run health check only",
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Test initialization only",
    )
    parser.add_argument(
        "--rag-only",
        action="store_true",
        help="Use standard RAG instead of GraphRAG",
    )
    
    args = parser.parse_args()
    
    if args.health:
        test_health()
    elif args.init:
        test_init()
    elif args.question:
        # Run health check first
        if not test_health():
            print("\n⚠️  System health check failed. Fix issues before testing queries.\n")
            sys.exit(1)
        
        # Then test query
        test_query(args.question, use_graph_rag=not args.rag_only)
    else:
        print("Usage:")
        print("  python3 test_graphrag.py \"Your question here\"")
        print("  python3 test_graphrag.py --health")
        print("  python3 test_graphrag.py --init")
        print("  python3 test_graphrag.py \"Your question\" --rag-only  # Use standard RAG")


if __name__ == "__main__":
    main()

