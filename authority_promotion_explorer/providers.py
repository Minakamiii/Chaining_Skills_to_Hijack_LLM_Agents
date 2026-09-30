from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import gzip
import http.client
import json
import time
import urllib.error
import urllib.request

from .config import ModelConfig


@dataclass(slots=True)
class ProviderResponse:
    model: str
    text: str
    raw: dict[str, Any]
    tool_calls: list["ProviderToolCall"] = field(default_factory=list)
    finish_reason: str = ""

    def assistant_message(self) -> dict[str, Any]:
        message: dict[str, Any] = {
            "role": "assistant",
            "content": self.text,
        }
        if self.tool_calls:
            message["tool_calls"] = [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.name,
                        "arguments": tool_call.arguments_text,
                    },
                }
                for tool_call in self.tool_calls
            ]
        return message


@dataclass(slots=True)
class ProviderTool:
    name: str
    description: str
    parameters: dict[str, Any]


@dataclass(slots=True)
class ProviderToolCall:
    id: str
    name: str
    arguments_text: str
    arguments: dict[str, Any]


def _chat_completions_url(base_url: str) -> str:
    stripped = base_url.rstrip("/")
    if stripped.endswith("/chat/completions"):
        return stripped
    return f"{stripped}/chat/completions"


def _responses_url(base_url: str) -> str:
    stripped = base_url.rstrip("/")
    if stripped.endswith("/responses"):
        return stripped
    return f"{stripped}/responses"


def _coerce_message_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        if "text" in content:
            return str(content["text"])
        if "content" in content:
            return _coerce_message_text(content["content"])
        return ""
    if isinstance(content, list):
        chunks: list[str] = []
        for item in content:
            if isinstance(item, str):
                chunks.append(item)
            elif isinstance(item, dict):
                if item.get("type") == "text" and "text" in item:
                    chunks.append(str(item["text"]))
                elif "content" in item:
                    chunks.append(_coerce_message_text(item["content"]))
                elif "text" in item:
                    chunks.append(str(item["text"]))
        return "\n".join(chunk for chunk in chunks if chunk)
    return ""


def _parse_tool_calls(message: dict[str, Any]) -> list[ProviderToolCall]:
    parsed_tool_calls: list[ProviderToolCall] = []
    for raw_call in message.get("tool_calls") or []:
        function = raw_call.get("function", {})
        name = str(function.get("name", "")).strip()
        if not name:
            continue

        arguments_text = str(function.get("arguments", "") or "")
        if arguments_text.strip():
            try:
                loaded_arguments = json.loads(arguments_text)
                arguments = loaded_arguments if isinstance(loaded_arguments, dict) else {"value": loaded_arguments}
            except json.JSONDecodeError:
                arguments = {"__raw_arguments__": arguments_text}
        else:
            arguments = {}

        parsed_tool_calls.append(
            ProviderToolCall(
                id=str(raw_call.get("id", "")),
                name=name,
                arguments_text=arguments_text,
                arguments=arguments,
            )
        )
    return parsed_tool_calls


def _coerce_response_output_text(parsed: dict[str, Any]) -> str:
    direct = parsed.get("output_text")
    if isinstance(direct, str):
        return direct

    chunks: list[str] = []
    for item in parsed.get("output") or []:
        if not isinstance(item, dict):
            continue
        content_items = item.get("content") or []
        if isinstance(content_items, dict):
            content_items = [content_items]
        for content in content_items:
            if not isinstance(content, dict):
                continue
            if content.get("type") in {"output_text", "text"} and "text" in content:
                chunks.append(str(content["text"]))
    return "\n".join(chunk for chunk in chunks if chunk)


_RETRYABLE_HTTP_CODES = {408, 409, 429, 500, 502, 503, 504}


def _sleep_before_retry(model_config: ModelConfig, attempt_index: int) -> None:
    if model_config.retry_backoff_seconds <= 0:
        return
    time.sleep(model_config.retry_backoff_seconds * attempt_index)


def _decode_response_body(response: Any) -> str:
    raw_body = response.read()
    getheader = getattr(response, "getheader", None)
    content_encoding = ""
    if callable(getheader):
        content_encoding = str(getheader("Content-Encoding", "") or "")
    if content_encoding.lower() == "gzip":
        raw_body = gzip.decompress(raw_body)
    return raw_body.decode("utf-8")


def _load_response_json_object(raw_text: str) -> dict[str, Any]:
    stripped = raw_text.lstrip()
    decoder = json.JSONDecoder()
    parsed, end_index = decoder.raw_decode(stripped)
    if not isinstance(parsed, dict):
        raise RuntimeError(f"Provider response was not a JSON object: {raw_text}")

    trailing = stripped[end_index:].strip()
    if trailing:
        parsed = dict(parsed)
        parsed["_provider_trailing_text"] = trailing
    return parsed


def chat_completion(
    model_config: ModelConfig,
    messages: list[dict[str, Any]],
    *,
    tools: list[ProviderTool] | None = None,
) -> ProviderResponse:
    if model_config.provider != "openai_compatible":
        raise ValueError(f"Unsupported provider: {model_config.provider}")

    payload: dict[str, Any] = {
        "model": model_config.model,
        "messages": messages,
        "temperature": model_config.temperature,
    }
    if tools:
        payload["tools"] = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for tool in tools
        ]
        payload["tool_choice"] = "auto"
    payload.update(model_config.extra_body)

    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {model_config.api_key()}",
        "Content-Type": "application/json",
    }
    headers.update(model_config.extra_headers)

    request = urllib.request.Request(
        _chat_completions_url(model_config.base_url),
        data=body,
        headers=headers,
        method="POST",
    )

    attempts = max(1, model_config.max_retries + 1)
    raw_text = ""
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=model_config.timeout_seconds) as response:
                raw_text = _decode_response_body(response)
            break
        except urllib.error.HTTPError as exc:
            error_text = exc.read().decode("utf-8", errors="replace")
            if exc.code in _RETRYABLE_HTTP_CODES and attempt < attempts:
                _sleep_before_retry(model_config, attempt)
                continue
            raise RuntimeError(f"Provider returned HTTP {exc.code}: {error_text}") from exc
        except (urllib.error.URLError, TimeoutError, http.client.RemoteDisconnected) as exc:
            if attempt < attempts:
                _sleep_before_retry(model_config, attempt)
                continue
            raise RuntimeError(f"Provider request failed: {exc}") from exc

    parsed = _load_response_json_object(raw_text)
    choices = parsed.get("choices") or []
    if not choices:
        raise RuntimeError(f"Provider response did not contain choices: {raw_text}")

    choice = choices[0]
    message = choice.get("message", {})
    text = _coerce_message_text(message.get("content"))
    tool_calls = _parse_tool_calls(message)

    return ProviderResponse(
        model=str(parsed.get("model", model_config.model)),
        text=text,
        raw=parsed,
        tool_calls=tool_calls,
        finish_reason=str(choice.get("finish_reason", "")),
    )


def responses_completion(
    model_config: ModelConfig,
    messages: list[dict[str, Any]],
) -> ProviderResponse:
    if model_config.provider != "openai_responses":
        raise ValueError(f"Unsupported provider: {model_config.provider}")

    payload: dict[str, Any] = {
        "model": model_config.model,
        "input": messages,
    }
    payload.update(model_config.extra_body)

    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {model_config.api_key()}",
        "Content-Type": "application/json",
    }
    headers.update(model_config.extra_headers)

    request = urllib.request.Request(
        _responses_url(model_config.base_url),
        data=body,
        headers=headers,
        method="POST",
    )

    attempts = max(1, model_config.max_retries + 1)
    raw_text = ""
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=model_config.timeout_seconds) as response:
                raw_text = _decode_response_body(response)
            break
        except urllib.error.HTTPError as exc:
            error_text = exc.read().decode("utf-8", errors="replace")
            if exc.code in _RETRYABLE_HTTP_CODES and attempt < attempts:
                _sleep_before_retry(model_config, attempt)
                continue
            raise RuntimeError(f"Provider returned HTTP {exc.code}: {error_text}") from exc
        except (urllib.error.URLError, TimeoutError, http.client.RemoteDisconnected) as exc:
            if attempt < attempts:
                _sleep_before_retry(model_config, attempt)
                continue
            raise RuntimeError(f"Provider request failed: {exc}") from exc

    parsed = _load_response_json_object(raw_text)
    text = _coerce_response_output_text(parsed)
    return ProviderResponse(
        model=str(parsed.get("model", model_config.model)),
        text=text,
        raw=parsed,
        finish_reason=str(parsed.get("status", "")),
    )
