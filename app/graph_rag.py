"""
GraphRAG Implementation

Combines vector embeddings (RAG) with graph structure for enhanced code analysis.
"""
import os
from typing import Dict, List, Optional, Set

from langchain.prompts import PromptTemplate
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

from .graph_loader import get_graph_loader
from .llm_factory import get_llm

LOCAL_VECTOR_STORE_PATH = os.getenv("LOCAL_VECTOR_STORE_PATH", "chroma_db")
LOCAL_COLLECTION_NAME = os.getenv("LOCAL_COLLECTION_NAME", "code_assistant_local")
LOCAL_EMBEDDING_MODEL = os.getenv(
    "LOCAL_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)

RAG_K = int(os.getenv("RAG_K", "10"))
GRAPH_DEPTH = int(os.getenv("GRAPH_DEPTH", "2"))
GRAPH_MAX_NODES = int(os.getenv("GRAPH_MAX_NODES", "20"))

GRAPH_RAG_TEMPLATE = """
You are an expert software developer AI assistant specialized in code analysis using GraphRAG.
You have access to both semantic code embeddings and graph relationships between code components.

Use the following context to answer the question:
1. **Code Chunks**: Directly retrieved code snippets from the codebase
2. **Graph Context**: Related components, dependencies, and relationships

If the context provides relevant information, use it to give a detailed answer.
If the context doesn't contain enough information, provide what you can and indicate what's missing.
Only state "Answer not available in the indexed codebase" if the question is completely unrelated.

Maintain a professional tone. When showing code, preserve proper formatting.
When referencing relationships, mention the graph connections (e.g., "Vehicle X is SERVICED by Package Y").

QUESTION: {question}

CODE CHUNKS:
{code_context}

GRAPH RELATIONSHIPS:
{graph_context}

ANSWER:
"""

GRAPH_RAG_PROMPT = PromptTemplate.from_template(GRAPH_RAG_TEMPLATE)

vectorstore = None
graph_rag_chain = None
_embedder = None


def _get_embedding_model():
    """Get or create the embedding model."""
    global _embedder
    if _embedder is None:
        print(f"Loading embedding model: {LOCAL_EMBEDDING_MODEL}")
        _embedder = HuggingFaceEmbeddings(model_name=LOCAL_EMBEDDING_MODEL)
    return _embedder


def _extract_node_ids_from_chunks(chunks: List) -> Set[str]:
    """Extract potential node IDs from retrieved code chunks."""
    node_ids = set()
    graph_loader = get_graph_loader()

    for chunk in chunks:
        metadata = chunk.metadata or {}
        source_path = metadata.get("source", "")

        if source_path:
            # Find nodes that reference this source file (exact match)
            related_nodes = graph_loader.find_nodes_by_source(source_path)
            for node in related_nodes:
                node_ids.add(node["id"])
            
            # Also try to match by directory - if chunk is from mycarhub/src/,
            # find nodes from same directory structure
            import os
            source_dir = os.path.dirname(source_path)
            if source_dir:
                # Check if any node sources are in the same directory structure
                for node in graph_loader.nodes.values():
                    node_source = node.get("source", "")
                    if node_source:
                        node_dir = os.path.dirname(os.path.normpath(node_source))
                        # Match if directories overlap (e.g., both in mycarhub/src/)
                        if source_dir in node_dir or node_dir.endswith(source_dir) or source_dir.endswith(os.path.basename(node_dir)):
                            node_ids.add(node["id"])

        # Also try to extract vehicle IDs or other identifiers from content
        content = chunk.page_content.lower()
        # Look for common patterns (vehicle IDs, component names, etc.)
        # This is a simple heuristic - can be enhanced
        if "vehicle" in content or "car" in content:
            # Try to find vehicle nodes
            vehicle_nodes = graph_loader.get_nodes_by_type("Vehicle")
            for vnode in vehicle_nodes:
                payload = vnode.get("payload", {})
                if payload.get("id"):
                    # Check if this ID appears in the chunk
                    if str(payload["id"]).lower() in content:
                        node_ids.add(vnode["id"])
        
        # If chunk mentions "db.json" or "database", try to find FleetInventory nodes
        if "db.json" in content or "database" in content or "inventory" in content:
            fleet_nodes = graph_loader.get_nodes_by_type("FleetInventory")
            for fleet_node in fleet_nodes:
                node_ids.add(fleet_node["id"])

    return node_ids


def _get_graph_context(node_ids: Set[str]) -> str:
    """Build graph context string from node IDs."""
    if not node_ids:
        return "No graph relationships found."

    graph_loader = get_graph_loader()
    if not graph_loader.is_loaded():
        return "Graph not available."

    # Traverse graph from these nodes
    all_related = graph_loader.traverse(list(node_ids), depth=GRAPH_DEPTH)

    # Limit to max nodes
    if len(all_related) > GRAPH_MAX_NODES:
        all_related = set(list(all_related)[:GRAPH_MAX_NODES])

    context_parts = []
    for node_id in all_related:
        node = graph_loader.get_node(node_id)
        if not node:
            continue

        node_type = node.get("type", "Unknown")
        label = node.get("label", node_id)
        source = node.get("source", "")

        # Get neighbors with relations
        neighbors = graph_loader.get_neighbors(node_id)
        relations = []
        # Access node_edges through the graph_loader instance
        node_edges = getattr(graph_loader, 'node_edges', {})
        for edge in node_edges.get(node_id, []):
            other_id = edge.get("to") if edge.get("from") == node_id else edge.get("from")
            if other_id in all_related:
                other_node = graph_loader.get_node(other_id)
                if other_node:
                    rel_type = edge.get("relation", "RELATED_TO")
                    other_label = other_node.get("label", other_id)
                    relations.append(f"{rel_type}: {other_label}")

        context_parts.append(
            f"- {node_type}: {label} (from {os.path.basename(source) if source else 'unknown'})"
        )
        if relations:
            context_parts.append(f"  Relations: {', '.join(relations[:3])}")  # Limit relations

    return "\n".join(context_parts) if context_parts else "No graph relationships found."


def initialize_graph_rag():
    """Initialize the GraphRAG chain."""
    global vectorstore, graph_rag_chain

    try:
        # Load vector store
        print(f"📦 Loading vector store from {LOCAL_VECTOR_STORE_PATH}...")
        embedding_model = _get_embedding_model()
        vectorstore = Chroma(
            persist_directory=LOCAL_VECTOR_STORE_PATH,
            collection_name=LOCAL_COLLECTION_NAME,
            embedding_function=embedding_model,
        )
        
        # Check if vector store has data
        try:
            collection_count = vectorstore._collection.count()
            print(f"✅ Vector store loaded: {LOCAL_VECTOR_STORE_PATH} ({collection_count} documents)")
            if collection_count == 0:
                print("⚠️ WARNING: Vector store is empty! Index the codebase first.")
        except Exception as e:
            print(f"⚠️ Could not count documents in vector store: {e}")

        # Load graph
        print(f"🕸️ Loading graph from analytics API...")
        graph_loader = get_graph_loader()
        if not graph_loader.is_loaded():
            print("⚠️ Graph not loaded. GraphRAG will work with vectors only.")
            print(f"   Make sure analytics API is running: {graph_loader.graph_url}")

        # Get LLM instance (verify it can be created, but don't test call it)
        # The actual call will happen in get_graph_rag_answer() and errors will be handled there
        print(f"🤖 Initializing LLM ({os.getenv('LLM_PROVIDER', 'vertex')})...")
        try:
            llm = get_llm()
            # Just verify it's created successfully, don't make a test call
            # (test calls can fail due to billing, network, etc., but the LLM object is valid)
            print(f"   ✅ LLM instance created successfully")
            if hasattr(llm, 'model_name'):
                print(f"   📦 Model: {llm.model_name}")
            elif hasattr(llm, 'endpoint_name'):
                print(f"   📦 Endpoint: {llm.endpoint_name}")
        except Exception as e:
            print(f"   ⚠️ LLM initialization failed: {e}")
            print(f"   GraphRAG will still initialize, but queries will fail until LLM is fixed")
            # Don't fail initialization - let it fail on first query instead
            # This way the system can still report status via /health
        
        # Mark as initialized (we don't use a chain since we manually format the prompt)
        # get_graph_rag_answer() manually formats the prompt with graph context
        graph_rag_chain = True  # Just a flag to indicate initialization is complete

        print(f"✅ GraphRAG initialized (k={RAG_K}, graph_depth={GRAPH_DEPTH})")
    except Exception as e:
        print(f"\n❌ ERROR: GraphRAG initialization failed!")
        print(f"   Error: {type(e).__name__}: {e}")
        print(f"\n   Common issues:")
        print(f"   1. Vector store not found - Run: python3.9 scripts/index_codebase.py <path>")
        print(f"   2. Analytics API not running - Start: cd my_codebase/mycarhub-fleet-analytics && npm run dev")
        print(f"   3. LLM credentials missing - Check .env and gcloud auth")
        print(f"\n   Full traceback:")
        import traceback
        traceback.print_exc()
        graph_rag_chain = None
        raise


def get_graph_rag_answer(question: str) -> Dict:
    """
    Get answer using GraphRAG (vectors + graph).

    Args:
        question: User question

    Returns:
        Dict with answer, sources, and graph_context
    """
    global graph_rag_chain, vectorstore
    
    # Try to initialize if not already done
    if not graph_rag_chain or vectorstore is None:
        print("⚠️ GraphRAG not initialized. Attempting initialization...")
        try:
            initialize_graph_rag()
        except Exception as e:
            error_msg = str(e)
            print(f"❌ GraphRAG initialization failed: {error_msg}")
            import traceback
            traceback.print_exc()
            return {
                "answer": f"GraphRAG system not initialized. Error: {error_msg}\n\nCheck backend logs and ensure:\n1. Vector store exists (index the codebase first)\n2. Analytics API is running on port 5001\n3. LLM credentials are configured",
                "sources": [],
                "graph_context": "No graph relationships found.",
                "nodes_found": 0,
            }
    
    if not graph_rag_chain:
        return {
            "answer": "GraphRAG system not initialized. Check backend logs. Please restart the server.",
            "sources": [],
            "graph_context": "No graph relationships found.",
            "nodes_found": 0,
        }

    # Step 1: Vector search
    retriever = vectorstore.as_retriever(search_kwargs={"k": RAG_K})
    # Use invoke() instead of deprecated get_relevant_documents()
    vector_chunks = retriever.invoke(question)

    # Step 2: Extract node IDs from chunks
    node_ids = _extract_node_ids_from_chunks(vector_chunks)

    # Step 3: Format sources (do this early so it's available in error handling)
    sources = []
    for chunk in vector_chunks:
        metadata = chunk.metadata or {}
        source_path = metadata.get("source", "unknown")
        sources.append(
            {
                "source": os.path.basename(source_path),
                "content": chunk.page_content[:200] + "...",
            }
        )

    # Step 4: Get graph context
    graph_context = _get_graph_context(node_ids) if node_ids else "No graph relationships found."

    # Step 5: Build combined context
    code_context = "\n\n".join(
        [
            f"[{i+1}] {chunk.page_content[:500]}..."
            for i, chunk in enumerate(vector_chunks[:RAG_K])
        ]
    )

    # Step 6: Generate answer with LLM
    # We need to manually format the prompt with graph context since the chain doesn't know about it
    try:
        llm = get_llm()
        full_prompt = GRAPH_RAG_PROMPT.format(
            question=question,
            code_context=code_context,
            graph_context=graph_context,
        )
        response = llm.invoke(full_prompt)
        # Extract text from response (handle both string and message objects)
        if isinstance(response, str):
            answer = response
        elif hasattr(response, 'content'):
            answer = response.content
        elif hasattr(response, 'text'):
            answer = response.text
        else:
            answer = str(response)
    except Exception as e:
        error_msg = str(e)
        # Provide helpful error messages for common issues
        if "BILLING_DISABLED" in error_msg or "billing" in error_msg.lower():
            error_msg = f"❌ Billing not enabled on Google Cloud project.\n\n{error_msg}\n\nEnable billing: https://console.cloud.google.com/billing"
        elif "403" in error_msg or "permission" in error_msg.lower():
            error_msg = f"❌ Permission error accessing LLM API.\n\n{error_msg}\n\nCheck IAM roles and authentication."
        elif "404" in error_msg or "not found" in error_msg.lower():
            error_msg = f"❌ LLM endpoint/model not found.\n\n{error_msg}\n\nCheck model name and endpoint configuration.\n\nAvailable Qwen models on Vertex AI:\n- qwen-2.5-7b-instruct (may need full path)\n- qwen-7b-instruct\n- Try: @google-cloud/aiplatform Python SDK or check Model Garden"
        
        return {
            "answer": f"Error generating answer:\n\n{error_msg}",
            "sources": sources,  # Return sources even if LLM failed
            "graph_context": graph_context,
        }

    return {
        "answer": answer.strip() if isinstance(answer, str) else str(answer),
        "sources": sources,
        "graph_context": graph_context,
        "nodes_found": len(node_ids),
    }


# Initialize on import - but catch errors so the app can still start
try:
    initialize_graph_rag()
except Exception as e:
    print(f"\n❌ GraphRAG initialization failed on import.")
    print(f"   It will be retried when needed. Error: {e}\n")
    graph_rag_chain = None

