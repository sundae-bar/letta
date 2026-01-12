from typing import Literal

from pydantic import Field

from letta.constants import DEFAULT_EMBEDDING_CHUNK_SIZE, LLM_MAX_CONTEXT_WINDOW
from letta.log import get_logger
from letta.schemas.embedding_config import EmbeddingConfig
from letta.schemas.enums import ProviderCategory, ProviderType
from letta.schemas.llm_config import LLMConfig
from letta.schemas.providers.openai import OpenAIProvider

logger = get_logger(__name__)

DEFAULT_EMBEDDING_BATCH_SIZE = 1024


class ChutesProvider(OpenAIProvider):
    """
    Chutes provider - uses OpenAI-compatible API with CHUTES_API_KEY environment variable.
    This is essentially an OpenAIProvider with a different name and API key source.
    """
    provider_type: Literal[ProviderType.chutes] = Field(ProviderType.chutes, description="The type of the provider.")
    provider_category: ProviderCategory = Field(ProviderCategory.base, description="The category of the provider (base or byok)")
    
    # Override base_url to use Chutes endpoint (can be configured)
    base_url: str = Field("https://api.chutes.ai/v1", description="Base URL for the Chutes API.")

    async def check_api_key(self):
        from letta.llm_api.openai import openai_check_valid_api_key

        # Decrypt API key before using
        api_key = await self.api_key_enc.get_plaintext_async() if self.api_key_enc else None
        openai_check_valid_api_key(self.base_url, api_key)

    async def list_llm_models_async(self) -> list[LLMConfig]:
        """
        List LLM models from Chutes API.
        Uses the same OpenAI-compatible endpoint structure.
        """
        data = await self._get_models_async()
        return self._list_llm_models(data)

    async def list_embedding_models_async(self) -> list[EmbeddingConfig]:
        """Return known Chutes embedding models (using OpenAI-compatible format)."""

        return [
            EmbeddingConfig(
                embedding_model="text-embedding-ada-002",
                embedding_endpoint_type="openai",
                embedding_endpoint=self.base_url,
                embedding_dim=1536,
                embedding_chunk_size=DEFAULT_EMBEDDING_CHUNK_SIZE,
                handle=self.get_handle("text-embedding-ada-002", is_embedding=True),
                batch_size=DEFAULT_EMBEDDING_BATCH_SIZE,
            ),
            EmbeddingConfig(
                embedding_model="text-embedding-3-small",
                embedding_endpoint_type="openai",
                embedding_endpoint=self.base_url,
                embedding_dim=1536,
                embedding_chunk_size=DEFAULT_EMBEDDING_CHUNK_SIZE,
                handle=self.get_handle("text-embedding-3-small", is_embedding=True),
                batch_size=DEFAULT_EMBEDDING_BATCH_SIZE,
            ),
            EmbeddingConfig(
                embedding_model="text-embedding-3-large",
                embedding_endpoint_type="openai",
                embedding_endpoint=self.base_url,
                embedding_dim=3072,
                embedding_chunk_size=DEFAULT_EMBEDDING_CHUNK_SIZE,
                handle=self.get_handle("text-embedding-3-large", is_embedding=True),
                batch_size=DEFAULT_EMBEDDING_BATCH_SIZE,
            ),
        ]

