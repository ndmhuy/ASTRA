"""MAS transport remains closed and preserves the existing academic request."""

import asyncio

import pytest
from pydantic import ValidationError

from exam_baseline.config import Settings
from exam_baseline.core.contracts import CompletionRequest, ImageInput, ProviderError
from exam_baseline.providers.worker_mas import DisabledWorkerMasProvider, MasSettings


def test_mas_adapter_preserves_schema_images_model_and_independent_limits():
    settings = Settings.for_offline().model_copy(update={"model": "academic-fixture"})
    request = CompletionRequest(
        "academic-system", "academic-data", {"type": "object"}, (ImageInput(b"synthetic-image"),)
    )
    provider = DisabledWorkerMasProvider(settings, "solver")
    envelope = provider.prepare(request)
    assert envelope["model"] == "academic-fixture"
    assert envelope["request"]["system"] == request.system
    assert envelope["request"]["user"] == request.user
    assert envelope["request"]["images"][0]["base64"] == "c3ludGhldGljLWltYWdl"
    assert envelope["limits"]["max_output_tokens"] == 8192
    assert envelope["limits"]["timeout_seconds"] == 90
    envelope["request"]["output_schema"]["new"] = "field"
    assert request.output_schema == {"type": "object"}

    with pytest.raises(ProviderError) as error:
        asyncio.run(provider.complete(request))
    assert error.value.code == "mas_forwarding_disabled"


def test_paid_public_mas_cannot_be_enabled_by_a_local_boolean():
    with pytest.raises(ValidationError):
        MasSettings(_env_file=None, forwarding_enabled=True)
