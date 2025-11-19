"""
LLM Factory Module

Provides unified interface for switching between different LLM providers
(Google Cloud Vertex AI, AWS SageMaker, OpenAI).
"""
import os
from typing import Optional

from .rag_chain import SageMakerServerlessLLM, _get_llm as _get_sagemaker_llm
from .vertex_llm import create_vertex_llm, VertexAIQwenLLM

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()  # Default to OpenAI as backup

_llm_instance = None


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


def get_llm(provider: Optional[str] = None):
    """
    Get LLM instance based on configured provider.

    Args:
        provider: Override provider ("vertex", "sagemaker", or "openai")

    Returns:
        LangChain LLM instance
    """
    global _llm_instance
    provider = (provider or LLM_PROVIDER).lower()

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

    else:
        raise ValueError(
            f"Unknown LLM provider: {provider}. Use 'vertex', 'sagemaker', or 'openai'"
        )


def reset_llm():
    """Reset the cached LLM instance (useful when switching providers)."""
    global _llm_instance
    _llm_instance = None


def get_current_provider() -> str:
    """Get the currently configured provider."""
    return LLM_PROVIDER

