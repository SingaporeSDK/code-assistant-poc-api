import os

from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFacePipeline
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline

LOCAL_VECTOR_STORE_PATH = os.getenv("LOCAL_VECTOR_STORE_PATH", "chroma_db")
LOCAL_COLLECTION_NAME = os.getenv("LOCAL_COLLECTION_NAME", "code_assistant_local")
LOCAL_EMBEDDING_MODEL = os.getenv("LOCAL_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "google/flan-t5-base")

vectorstore = None
rag_chain = None
_local_embedder = None
_local_llm = None

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


def _get_embedding_model():
    global _local_embedder
    if _local_embedder is None:
        print(f"Loading Hugging Face embedding model: {LOCAL_EMBEDDING_MODEL}")
        _local_embedder = HuggingFaceEmbeddings(model_name=LOCAL_EMBEDDING_MODEL)
    return _local_embedder


def _get_llm():
    global _local_llm
    if _local_llm is None:
        print(f"Loading local LLM model: {LOCAL_LLM_MODEL}")
        tokenizer = AutoTokenizer.from_pretrained(LOCAL_LLM_MODEL)
        model = AutoModelForSeq2SeqLM.from_pretrained(LOCAL_LLM_MODEL)
        text2text = pipeline(
            "text2text-generation",
            model=model,
            tokenizer=tokenizer,
            max_length=512,
            batch_size=1,
        )
        _local_llm = HuggingFacePipeline(pipeline=text2text)
    return _local_llm


def initialize_rag_components():
    """Initializes the vector store and the RAG chain using local models."""
    global vectorstore, rag_chain

    embedding_model = _get_embedding_model()
    vectorstore = Chroma(
        persist_directory=LOCAL_VECTOR_STORE_PATH,
        collection_name=LOCAL_COLLECTION_NAME,
        embedding_function=embedding_model,
    )
    print(f"Vector store loaded from {LOCAL_VECTOR_STORE_PATH} (collection: {LOCAL_COLLECTION_NAME})")

    llm = _get_llm()
    retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

    rag_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": QA_PROMPT},
        return_source_documents=True,
    )
    print("Local RAG chain initialized (k=10).")


def get_answer(question: str) -> dict:
    if rag_chain is None:
        return {
            "answer": "The RAG system is not initialized. Please check the backend terminal for errors.",
            "sources": [],
        }

    result = rag_chain.invoke({"query": question})
    docs = result.get("source_documents", []) or []
    sources = []
    for doc in docs:
        metadata = doc.metadata or {}
        source_path = metadata.get("source") or "unknown"
        sources.append(
            {
                "source": os.path.basename(source_path),
                "content": doc.page_content,
            }
        )

    return {
        "answer": result.get("result", "An unknown error occurred during retrieval."),
        "sources": sources,
    }


def list_all_document_sources() -> list:
    if vectorstore is None:
        return [{"error": "Vector store not initialized. Check terminal for loading errors."}]

    try:
        ids = vectorstore._collection.get(limit=1000, include=['metadatas']).get('ids', [])
        if not ids:
            return []

        results = vectorstore._collection.get(ids=ids, include=['metadatas'])
        sources = []
        for metadata in results.get('metadatas', []):
            if metadata and 'source' in metadata:
                sources.append({"source": os.path.basename(metadata['source'])})
        return sources
    except Exception as e:
        return [{"error": f"Error loading documents from vector store: {e}"}]


try:
    initialize_rag_components()
except Exception as e:
    print(
        "\n--- CRITICAL RAG INITIALIZATION ERROR ---\n"
        f"{e}\n"
        "------------------------------------------\n"
    )
