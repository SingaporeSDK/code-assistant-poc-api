"""
Google Cloud Vertex AI LLM Wrapper

Provides LangChain-compatible LLM interface for Qwen models on Vertex AI.
"""
import os
import json
from typing import Any, Dict, List, Optional

try:
    from google.cloud import aiplatform
    from langchain_core.language_models import LLM
    from langchain_core.callbacks import CallbackManagerForLLMRun
except ImportError:
    print("⚠️ google-cloud-aiplatform not installed. Install with: pip install google-cloud-aiplatform")
    aiplatform = None
    LLM = object


class VertexAIQwenLLM(LLM):
    """LangChain LLM wrapper for Qwen models on Google Cloud Vertex AI."""

    project_id: str
    location: str
    model_name: str
    temperature: float = 0.2
    max_output_tokens: int = 2048
    top_p: float = 0.9
    top_k: int = 40

    def __init__(self, **kwargs: Any):
        if aiplatform is None:
            raise ImportError(
                "google-cloud-aiplatform is required. Install with: pip install google-cloud-aiplatform"
            )
        super().__init__(**kwargs)
        # Initialize Vertex AI
        aiplatform.init(project=self.project_id, location=self.location)

    @property
    def _llm_type(self) -> str:
        return "vertex_ai_qwen"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Call the Vertex AI model."""
        from vertexai.preview.language_models import TextGenerationModel

        try:
            model = TextGenerationModel.from_pretrained(self.model_name)

            parameters = {
                "temperature": kwargs.get("temperature", self.temperature),
                "max_output_tokens": kwargs.get("max_output_tokens", self.max_output_tokens),
                "top_p": kwargs.get("top_p", self.top_p),
                "top_k": kwargs.get("top_k", self.top_k),
            }

            if stop:
                parameters["stop_sequences"] = stop

            response = model.predict(
                prompt,
                **parameters,
            )

            text = response.text if hasattr(response, "text") else str(response)
            if stop:
                for stop_token in stop:
                    if stop_token in text:
                        text = text.split(stop_token)[0]

            return text.strip()

        except Exception as e:
            error_msg = f"Vertex AI API error: {e}"
            print(f"❌ {error_msg}")
            raise RuntimeError(error_msg) from e


def create_vertex_llm(
    project_id: Optional[str] = None,
    location: Optional[str] = None,
    model_name: Optional[str] = None,
    **kwargs: Any,
) -> VertexAIQwenLLM:
    """Factory function to create a Vertex AI Qwen LLM instance."""
    project_id = project_id or os.getenv("GCP_PROJECT_ID")
    location = location or os.getenv("GCP_REGION", "us-central1")
    model_name = model_name or os.getenv("VERTEX_MODEL_NAME", "qwen-2.5-7b-instruct")

    if not project_id:
        raise ValueError(
            "GCP_PROJECT_ID must be set in environment or passed as argument"
        )

    return VertexAIQwenLLM(
        project_id=project_id,
        location=location,
        model_name=model_name,
        **kwargs,
    )

