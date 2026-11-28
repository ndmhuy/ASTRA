"""Environment configuration. Secrets never enter evaluation records."""

from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from exam_baseline.providers.gateway import Gateway

DEFAULT_RAG_CORPUS_REF = "8b8fb7b09182b3d9d1eee0b95818027f52ab004d"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="EXAM_",
        env_file=".env",
        extra="ignore",
        hide_input_in_errors=True,
    )

    provider: Literal["mock", "chat_completions", "anthropic", "worker_mas", "unconfigured"] = (
        "mock"
    )
    demo_mode: bool = False
    model: str = Field(default="mock-fixture-v1", min_length=1)
    prompt_version: Literal["v1"] = "v1"
    api_key: SecretStr | None = None
    anthropic_api_key: SecretStr | None = Field(
        default=None, validation_alias="ANTHROPIC_API_KEY", exclude=True, repr=False
    )
    use_ai_gateway: bool = False
    gateway_account_id: str = ""
    gateway_id: str = ""
    gateway_token: SecretStr | None = None
    gateway_byok_alias: str = "default"
    base_url: str = "https://api.openai.com/v1"
    timeout_seconds: float = Field(default=90, gt=0, allow_inf_nan=False)
    max_output_tokens: int = Field(default=8192, gt=0)
    token_limit_field: Literal["max_completion_tokens", "max_tokens"] = "max_completion_tokens"
    response_format: Literal["json_object", "json_schema", "text"] = "json_object"
    structured_output_strict: bool = False
    schema_as_tool: bool = False
    temperature: float | None = Field(default=None, ge=0, le=2, allow_inf_nan=False)
    seed: int | None = None
    max_prompt_chars: int = Field(default=200000, gt=0)
    supports_images: bool = False
    input_price_per_million: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    output_price_per_million: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    spend_limit_usd: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    spend_ledger: Path = Path("runs/provider-spend.sqlite3")
    spend_budget_id: str = Field(default="project-total", min_length=1, max_length=100)
    evaluation_jsonl: Path | None = None
    ui_output_root: Path = Path("runs/ui")
    latex_compiler: Path | None = None
    latex_timeout_seconds: float = Field(default=300, gt=0, allow_inf_nan=False)
    latex_cache_dir: Path = Path("runs/latex-cache")
    rag_corpus_ref: str = DEFAULT_RAG_CORPUS_REF
    rag_pack_dir: Path | None = None

    @classmethod
    def for_offline(cls) -> "Settings":
        """Validate defaults explicitly, ignoring .env and EXAM_* environment overrides."""
        defaults = {name: field.get_default() for name, field in cls.model_fields.items()}
        return cls(_env_file=None, **defaults)

    def gateway(self) -> Gateway | None:
        if not self.use_ai_gateway:
            return None
        if self.gateway_token is None:
            raise ValueError("EXAM_GATEWAY_TOKEN is required for BYOK mode")
        return Gateway(
            self.gateway_account_id, self.gateway_id, self.gateway_token, self.gateway_byok_alias
        )

    def for_agent_generation(self) -> "Settings":
        # Agent prompts include the schema and Pydantic validates dynamic question maps.
        if (
            self.use_ai_gateway or urlsplit(self.base_url).hostname == "api.openai.com"
        ) and self.response_format == "json_object":
            return self
        return self.model_copy(update={"response_format": "json_schema"})

    @model_validator(mode="after")
    def complete_configuration(self):
        if self.provider == "worker_mas" and self.model == "mock-fixture-v1":
            raise ValueError("set EXAM_MODEL for the real MAS provider")
        if self.provider in {"chat_completions", "anthropic"}:
            if self.provider == "anthropic" and self.api_key is None:
                self.api_key = self.anthropic_api_key
            if self.provider == "anthropic" and self.use_ai_gateway:
                raise ValueError("Anthropic Messages requires its direct API endpoint")
            if self.use_ai_gateway:
                self.gateway()
                if not self.spend_limit_usd:
                    raise ValueError("configure EXAM_SPEND_LIMIT_USD for BYOK mode")
            elif not self.api_key or not self.api_key.get_secret_value().strip():
                raise ValueError("EXAM_API_KEY is required for chat_completions")
            if self.model == "mock-fixture-v1":
                raise ValueError("set EXAM_MODEL for the real provider")
            url = urlsplit(self.base_url)
            if url.scheme not in {"http", "https"} or not url.hostname:
                raise ValueError("EXAM_BASE_URL must be an HTTP(S) URL")
            if not self.use_ai_gateway and url.hostname in {
                "gateway.ai.cloudflare.com",
                "api.cloudflare.com",
            }:
                raise ValueError("use EXAM_USE_AI_GATEWAY for the authenticated BYOK gateway")
            if url.username or url.password or url.query or url.fragment:
                raise ValueError("EXAM_BASE_URL must not contain credentials, query, or fragment")
        if (self.input_price_per_million is None) != (self.output_price_per_million is None):
            raise ValueError("configure both input and output token prices, or neither")
        if self.spend_limit_usd is not None and (
            self.input_price_per_million is None
            or self.input_price_per_million <= 0
            or self.output_price_per_million <= 0
        ):
            raise ValueError("a spend limit requires positive input and output token prices")
        if self.structured_output_strict and self.response_format != "json_schema":
            raise ValueError("strict structured output requires response_format=json_schema")
        if self.schema_as_tool and self.structured_output_strict:
            raise ValueError("schema_as_tool cannot promise strict response-format conformance")
        return self
