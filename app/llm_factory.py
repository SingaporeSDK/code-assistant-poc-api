"""
LLM Factory Module

Provides unified interface for switching between different LLM providers
(Local Ollama, Google Cloud Vertex AI, AWS SageMaker, OpenAI).
"""
import os
from typing import Optional

from .rag_chain import SageMakerServerlessLLM, _get_llm as _get_sagemaker_llm
from .vertex_llm import create_vertex_llm, VertexAIQwenLLM

_llm_instance = None


def _get_configured_provider() -> str:
    """Read provider from env (default to local Ollama)."""
    return os.getenv("LLM_PROVIDER", "ollama").lower()


def _get_openai_llm():
    """Create OpenAI ChatOpenAI instance."""
    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        raise ImportError(
            "langchain-openai is required for OpenAI provider. Install with: pip install langchain-openai"
        )
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY must be set in environment variables for OpenAI provider"
        )
    
    model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
    temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))
    
    return ChatOpenAI(
        model=model_name,  # Use 'model' instead of 'model_name' for newer versions
        temperature=temperature,
        openai_api_key=api_key,
    )


def _get_ollama_llm():
    """Create a ChatOllama instance for local inference."""
    try:
        from langchain_community.chat_models import ChatOllama
    except ImportError as exc:
        raise ImportError(
            "langchain-community is required for the Ollama provider. "
            "Reinstall requirements.txt or run: pip install langchain-community"
        ) from exc

    model_name = os.getenv("OLLAMA_MODEL_NAME", "llama3.1:8b-instruct-q4_1")
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    temperature = float(os.getenv("OLLAMA_TEMPERATURE", "0.1"))
    num_ctx = int(os.getenv("OLLAMA_CONTEXT", "8192"))
    keep_alive = os.getenv("OLLAMA_KEEP_ALIVE", "5m")

    return ChatOllama(
        model=model_name,
        base_url=base_url,
        temperature=temperature,
        num_ctx=num_ctx,
        keep_alive=keep_alive,
    )


def get_llm(provider: Optional[str] = None):
    """
    Get LLM instance based on configured provider.

    Args:
        provider: Override provider ("vertex", "sagemaker", or "openai")

    Returns:
        LangChain LLM instance
    """
    global _llm_instance
    provider = (provider or _get_configured_provider()).lower()

    if provider == "vertex":
        if _llm_instance is None or not isinstance(_llm_instance, VertexAIQwenLLM):
            print("🔵 Initializing Google Cloud Vertex AI LLM (Qwen)...")
            _llm_instance = create_vertex_llm()
            print(f"✅ Vertex AI LLM ready: {_llm_instance.model_name}")
        return _llm_instance

    elif provider == "sagemaker":
        if _llm_instance is None or not isinstance(_llm_instance, SageMakerServerlessLLM):
            print("🟠 Initializing AWS SageMaker LLM (Qwen)...")
            _llm_instance = _get_sagemaker_llm()
            print(f"✅ SageMaker LLM ready: {_llm_instance.endpoint_name}")
        return _llm_instance

    elif provider == "openai":
        # Check if we need to reinitialize (different provider or not initialized)
        from langchain_openai import ChatOpenAI
        if _llm_instance is None or not isinstance(_llm_instance, ChatOpenAI):
            print("⚪ Initializing OpenAI LLM...")
            _llm_instance = _get_openai_llm()
            model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
            print(f"✅ OpenAI LLM ready: {model_name}")
        return _llm_instance

    elif provider == "ollama":
        from langchain_community.chat_models import ChatOllama

        if _llm_instance is None or not isinstance(_llm_instance, ChatOllama):
            print("💻 Initializing local Ollama LLM...")
            _llm_instance = _get_ollama_llm()
            model_name = os.getenv("OLLAMA_MODEL_NAME", "llama3.1:8b-instruct-q4_1")
            print(f"✅ Ollama LLM ready: {model_name}")
        return _llm_instance

    else:
        raise ValueError(
            f"Unknown LLM provider: {provider}. Use 'ollama', 'vertex', 'sagemaker', or 'openai'"
        )


def reset_llm():
    """Reset the cached LLM instance (useful when switching providers)."""
    global _llm_instance
    _llm_instance = None


def get_current_provider() -> str:
    """Get the currently configured provider."""
    return _get_configured_provider()

