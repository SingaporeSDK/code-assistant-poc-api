import json
import os
from typing import Any, Dict, List, Optional

import boto3
from botocore.config import Config
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.language_models import LLM

LOCAL_VECTOR_STORE_PATH = os.getenv("LOCAL_VECTOR_STORE_PATH", "chroma_db")
LOCAL_COLLECTION_NAME = os.getenv("LOCAL_COLLECTION_NAME", "code_assistant_local")
LOCAL_EMBEDDING_MODEL = os.getenv(
    "LOCAL_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
SAGEMAKER_ENDPOINT_NAME = os.getenv("SAGEMAKER_ENDPOINT_NAME")
SAGEMAKER_ACCEPT = os.getenv("SAGEMAKER_ACCEPT", "application/json")
SAGEMAKER_CONTENT_TYPE = os.getenv("SAGEMAKER_CONTENT_TYPE", "application/json")
SAGEMAKER_MAX_NEW_TOKENS = int(os.getenv("SAGEMAKER_MAX_NEW_TOKENS", "512"))
SAGEMAKER_TEMPERATURE = float(os.getenv("SAGEMAKER_TEMPERATURE", "0.2"))
SAGEMAKER_TOP_P = float(os.getenv("SAGEMAKER_TOP_P", "0.9"))
SAGEMAKER_STOP_SEQUENCE = os.getenv("SAGEMAKER_STOP_SEQUENCE", "")

vectorstore = None
rag_chain = None
_local_embedder = None
_remote_llm = None


class SageMakerServerlessLLM(LLM):
    """Minimal LangChain LLM wrapper that calls a SageMaker Serverless endpoint."""

    endpoint_name: str
    region_name: str
    max_new_tokens: int = 512
    temperature: float = 0.2
    top_p: float = 0.9
    stop_sequence: Optional[str] = None
    content_type: str = "application/json"
    accept: str = "application/json"
    client_kwargs: Optional[Dict[str, Any]] = None

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        client_config = Config(
            retries={"max_attempts": 3, "mode": "standard"},
            read_timeout=120,
            connect_timeout=10,
        )
        self._client = boto3.client(
            "sagemaker-runtime",
            region_name=self.region_name,
            config=client_config,
            **(self.client_kwargs or {}),
        )

    @property
    def _llm_type(self) -> str:
        return "sagemaker_serverless"

    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": kwargs.get("max_new_tokens", self.max_new_tokens),
                "temperature": kwargs.get("temperature", self.temperature),
                "top_p": kwargs.get("top_p", self.top_p),
            },
        }
        if self.stop_sequence:
            payload["parameters"]["stop_sequences"] = [self.stop_sequence]
        if stop:
            payload["parameters"]["stop_sequences"] = list(
                set(payload["parameters"].get("stop_sequences", []) + stop)
            )

        response = self._client.invoke_endpoint(
            EndpointName=self.endpoint_name,
            ContentType=self.content_type,
            Accept=self.accept,
            Body=json.dumps(payload).encode("utf-8"),
        )

        body_str = response["Body"].read().decode("utf-8")
        text = self._extract_text(body_str)
        if stop:
            text = self._enforce_stop_tokens(text, stop)
        return text.strip()

    def _extract_text(self, body: str) -> str:
        """Best-effort parser for common HF/SageMaker response formats."""
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return body

        if isinstance(data, dict):
            if "generated_text" in data:
                return data["generated_text"]
            if "outputs" in data:
                outputs = data["outputs"]
                if isinstance(outputs, list) and outputs:
                    return self._extract_text(json.dumps(outputs[0]))
        elif isinstance(data, list) and data:
            first = data[0]
            if isinstance(first, dict) and "generated_text" in first:
                return first["generated_text"]
            if isinstance(first, str):
                return first
        return body

    @staticmethod
    def _enforce_stop_tokens(text: str, stop_tokens: List[str]) -> str:
        for token in stop_tokens:
            if token and token in text:
                text = text.split(token)[0]
        return text

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
    global _remote_llm
    if SAGEMAKER_ENDPOINT_NAME is None:
        raise RuntimeError(
            "SAGEMAKER_ENDPOINT_NAME is not set. Please configure your AWS endpoint."
        )
    if _remote_llm is None:
        print(
            f"Connecting to SageMaker endpoint '{SAGEMAKER_ENDPOINT_NAME}' in {AWS_REGION}"
        )
        _remote_llm = SageMakerServerlessLLM(
            endpoint_name=SAGEMAKER_ENDPOINT_NAME,
            region_name=AWS_REGION,
            max_new_tokens=SAGEMAKER_MAX_NEW_TOKENS,
            temperature=SAGEMAKER_TEMPERATURE,
            top_p=SAGEMAKER_TOP_P,
            stop_sequence=SAGEMAKER_STOP_SEQUENCE or None,
            content_type=SAGEMAKER_CONTENT_TYPE,
            accept=SAGEMAKER_ACCEPT,
        )
    return _remote_llm


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
