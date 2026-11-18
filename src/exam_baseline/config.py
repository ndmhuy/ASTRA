"""Environment configuration. Secrets never enter evaluation records."""

from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="EXAM_",
        env_file=".env",
        extra="ignore",
        hide_input_in_errors=True,
    )

    provider: Literal["mock", "chat_completions"] = "mock"
    model: str = Field(default="mock-fixture-v1", min_length=1)
    prompt_version: Literal["v1"] = "v1"
    api_key: SecretStr | None = None
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
    rag_corpus_ref: str = "8b8fb7b09182b3d9d1eee0b95818027f52ab004d"
    rag_pack_dir: Path | None = None

    @classmethod
    def for_offline(cls) -> "Settings":
        """Validate defaults explicitly, ignoring .env and EXAM_* environment overrides."""
        defaults = {name: field.get_default() for name, field in cls.model_fields.items()}
        return cls(_env_file=None, **defaults)

    @model_validator(mode="after")
    def complete_configuration(self):
        if self.provider == "chat_completions":
            if not self.api_key or not self.api_key.get_secret_value().strip():
                raise ValueError("EXAM_API_KEY is required for chat_completions")
            if self.model == "mock-fixture-v1":
                raise ValueError("set EXAM_MODEL for the real provider")
            url = urlsplit(self.base_url)
            if url.scheme not in {"http", "https"} or not url.hostname:
                raise ValueError("EXAM_BASE_URL must be an HTTP(S) URL")
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
