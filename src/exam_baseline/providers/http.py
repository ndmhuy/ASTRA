"""Select the configured HTTP wire format without model or provider fallback."""

from exam_baseline.providers.anthropic_messages import AnthropicMessagesProvider
from exam_baseline.providers.chat_completions import ChatCompletionsProvider


def http_provider(settings, client):
    if settings.provider == "anthropic":
        return AnthropicMessagesProvider(settings, client)
    return ChatCompletionsProvider(settings, client)
