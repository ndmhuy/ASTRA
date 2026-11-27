"""Real MAS via authenticated Worker; startup performs no model inference.

Load only the ignored .env.mas-worker profile, never the private legacy .env.
The Worker remains independently disabled until owner activation.
"""

import argparse
import os
from pathlib import Path

import uvicorn

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--model", help="Non-secret Gemini model ID, if absent from the profile")
    args = parser.parse_args()
    profile = ROOT / ".env.mas-worker"
    if not profile.is_file():
        parser.error("Missing ignored .env.mas-worker caller profile; see MAS_WORKER_RUNBOOK.md")

    from exam_baseline.config import Settings
    from exam_baseline.providers.worker_mas import MasSettings

    # Validate before replacing a running application or opening an inference job.
    mas = MasSettings(_env_file=profile)
    settings = Settings(
        _env_file=profile,
        provider="worker_mas",
        demo_mode=False,
        **({"model": args.model} if args.model else {}),
    )
    if not mas.forwarding_enabled or mas.transport != "worker":
        parser.error("Local MAS Worker transport is disabled; no fallback is selected")

    os.environ.update(
        ASTRA_AGENT_ENABLED="true",
        ASTRA_AGENT_TRANSPORT="worker",
        ASTRA_AGENT_SEMANTIC_CONTRACT="true",
        ASTRA_AGENT_FALLBACK_ENABLED="false",
        EXAM_DEMO_MODE="false",
        EXAM_PROVIDER="worker_mas",
        EXAM_MODEL=settings.model,
        EXAM_USE_AI_GATEWAY="false",
        EXAM_BASE_URL=mas.worker_url.rstrip("/") + "/v1",
        EXAM_TOKEN_LIMIT_FIELD="max_tokens",
        EXAM_TIMEOUT_SECONDS=str(settings.timeout_seconds),
        EXAM_MAX_OUTPUT_TOKENS=str(settings.max_output_tokens),
        EXAM_RESPONSE_FORMAT=settings.response_format,
        EXAM_SCHEMA_AS_TOOL=str(settings.schema_as_tool).lower(),
        EXAM_STRUCTURED_OUTPUT_STRICT=str(settings.structured_output_strict).lower(),
        EXAM_SUPPORTS_IMAGES=str(settings.supports_images).lower(),
        ASTRA_MAS_TRANSPORT="worker",
        ASTRA_MAS_FORWARDING_ENABLED="true",
        ASTRA_MAS_WORKER_URL=mas.worker_url,
        ASTRA_MAS_CALLER_TOKEN=mas.caller_token.get_secret_value(),
    )
    os.chdir(ROOT)

    # create_web_app normally reads legacy .env. Inject the already validated
    # isolated academic settings so unrelated local secrets cannot affect MAS.
    def create():
        from exam_baseline.api.app import configure_logging, create_app

        configure_logging()
        return create_app(
            settings.model_copy(update={"base_url": os.environ["EXAM_BASE_URL"]}),
            workspace_dir=ROOT / "astra-frontend/dist",
        )

    uvicorn.run(create(), host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
