from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from itertools import count
from typing import Any, Iterator
import json
import threading
import time
import uuid
from urllib.parse import urlsplit

from .config import ModelConfig
from .providers import ProviderResponse, ProviderTool, chat_completion


def _coerce_responses_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        chunks: list[str] = []
        for item in value:
            if not isinstance(item, dict):
                continue
            item_type = str(item.get("type", "")).strip()
            if item_type in {"input_text", "output_text", "text"} and item.get("text"):
                chunks.append(str(item["text"]))
        return "\n".join(chunk for chunk in chunks if chunk)
    if isinstance(value, dict):
        if "text" in value:
            return str(value["text"])
        if "content" in value:
            return _coerce_responses_text(value["content"])
    return ""


def _build_chat_messages(request_body: dict[str, Any]) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    instructions = str(request_body.get("instructions", "") or "").strip()
    if instructions:
        messages.append({"role": "system", "content": instructions})

    pending_tool_calls: list[dict[str, Any]] = []

    def flush_tool_calls() -> None:
        if not pending_tool_calls:
            return
        messages.append(
            {
                "role": "assistant",
                "content": "",
                "tool_calls": list(pending_tool_calls),
            }
        )
        pending_tool_calls.clear()

    for item in request_body.get("input") or []:
        if not isinstance(item, dict):
            continue
        item_type = str(item.get("type", "")).strip()

        if item_type == "message":
            flush_tool_calls()
            role = str(item.get("role", "user") or "user")
            text = _coerce_responses_text(item.get("content"))
            messages.append({"role": role, "content": text})
            continue

        if item_type == "function_call":
            pending_tool_calls.append(
                {
                    "id": str(item.get("call_id") or item.get("id") or f"call_{len(pending_tool_calls) + 1}"),
                    "type": "function",
                    "function": {
                        "name": str(item.get("name", "") or ""),
                        "arguments": str(item.get("arguments", "") or ""),
                    },
                }
            )
            continue

        if item_type == "function_call_output":
            flush_tool_calls()
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": str(item.get("call_id", "") or ""),
                    "content": str(item.get("output", "") or ""),
                }
            )
            continue

        flush_tool_calls()
        text = _coerce_responses_text(item)
        if text:
            messages.append({"role": "user", "content": text})

    flush_tool_calls()
    return messages


def _build_provider_tools(request_body: dict[str, Any]) -> list[ProviderTool]:
    tool_choice = request_body.get("tool_choice")
    if tool_choice == "none":
        return []

    provider_tools: list[ProviderTool] = []
    for tool in request_body.get("tools") or []:
        if not isinstance(tool, dict) or str(tool.get("type", "")).strip() != "function":
            continue
        parameters = tool.get("parameters", {})
        if not isinstance(parameters, dict):
            parameters = {}
        provider_tools.append(
            ProviderTool(
                name=str(tool.get("name", "") or ""),
                description=str(tool.get("description", "") or ""),
                parameters=parameters,
            )
        )
    return [tool for tool in provider_tools if tool.name]


def _response_created_event(response_id: str, model: str, parallel_tool_calls: bool) -> dict[str, Any]:
    return {
        "type": "response.created",
        "response": {
            "id": response_id,
            "object": "response",
            "created_at": int(time.time()),
            "status": "in_progress",
            "model": model,
            "output": [],
            "parallel_tool_calls": parallel_tool_calls,
        },
    }


def _message_output_events(
    *,
    response_id: str,
    model: str,
    text: str,
    output_index: int,
    item_id: str,
    parallel_tool_calls: bool,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    item = {
        "id": item_id,
        "type": "message",
        "role": "assistant",
        "status": "completed",
        "content": [{"type": "output_text", "text": text}],
    }
    events = [
        {
            "type": "response.output_item.added",
            "response_id": response_id,
            "output_index": output_index,
            "item": {
                "id": item_id,
                "type": "message",
                "role": "assistant",
                "status": "in_progress",
                "content": [],
            },
        },
        {
            "type": "response.content_part.added",
            "response_id": response_id,
            "item_id": item_id,
            "output_index": output_index,
            "content_index": 0,
            "part": {"type": "output_text", "text": text},
        },
        {
            "type": "response.output_text.delta",
            "response_id": response_id,
            "item_id": item_id,
            "output_index": output_index,
            "content_index": 0,
            "delta": text,
        },
        {
            "type": "response.output_text.done",
            "response_id": response_id,
            "item_id": item_id,
            "output_index": output_index,
            "content_index": 0,
            "text": text,
        },
        {
            "type": "response.content_part.done",
            "response_id": response_id,
            "item_id": item_id,
            "output_index": output_index,
            "content_index": 0,
            "part": {"type": "output_text", "text": text},
        },
        {
            "type": "response.output_item.done",
            "response_id": response_id,
            "output_index": output_index,
            "item": item,
        },
    ]
    completed_response = {
        "id": response_id,
        "object": "response",
        "created_at": int(time.time()),
        "status": "completed",
        "model": model,
        "output": [item],
        "output_text": text,
        "parallel_tool_calls": parallel_tool_calls,
    }
    return events, completed_response


def _tool_call_output_events(
    *,
    response_id: str,
    model: str,
    provider_response: ProviderResponse,
    parallel_tool_calls: bool,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    events: list[dict[str, Any]] = []
    output_items: list[dict[str, Any]] = []
    for output_index, tool_call in enumerate(provider_response.tool_calls):
        item_id = f"fc_{tool_call.id or uuid.uuid4().hex}"
        item = {
            "id": item_id,
            "type": "function_call",
            "status": "completed",
            "call_id": tool_call.id or item_id,
            "name": tool_call.name,
            "arguments": tool_call.arguments_text,
        }
        output_items.append(item)
        events.append(
            {
                "type": "response.output_item.added",
                "response_id": response_id,
                "output_index": output_index,
                "item": {
                    "id": item_id,
                    "type": "function_call",
                    "status": "in_progress",
                    "call_id": tool_call.id or item_id,
                    "name": tool_call.name,
                    "arguments": "",
                },
            }
        )
        if tool_call.arguments_text:
            events.append(
                {
                    "type": "response.function_call_arguments.delta",
                    "response_id": response_id,
                    "item_id": item_id,
                    "output_index": output_index,
                    "delta": tool_call.arguments_text,
                }
            )
        events.append(
            {
                "type": "response.function_call_arguments.done",
                "response_id": response_id,
                "item_id": item_id,
                "output_index": output_index,
                "call_id": tool_call.id or item_id,
                "name": tool_call.name,
                "arguments": tool_call.arguments_text,
            }
        )
        events.append(
            {
                "type": "response.output_item.done",
                "response_id": response_id,
                "output_index": output_index,
                "item": item,
            }
        )

    completed_response = {
        "id": response_id,
        "object": "response",
        "created_at": int(time.time()),
        "status": "completed",
        "model": model,
        "output": output_items,
        "parallel_tool_calls": parallel_tool_calls,
    }
    return events, completed_response


def build_sse_events(request_body: dict[str, Any], provider_response: ProviderResponse) -> list[dict[str, Any] | str]:
    response_id = f"resp_{uuid.uuid4().hex}"
    parallel_tool_calls = bool(request_body.get("parallel_tool_calls"))
    events: list[dict[str, Any] | str] = [
        _response_created_event(response_id, provider_response.model, parallel_tool_calls)
    ]

    output_items: list[dict[str, Any]] = []
    output_index = 0

    if provider_response.text:
        item_id = f"msg_{uuid.uuid4().hex}"
        message_events, completed_message = _message_output_events(
            response_id=response_id,
            model=provider_response.model,
            text=provider_response.text,
            output_index=output_index,
            item_id=item_id,
            parallel_tool_calls=parallel_tool_calls,
        )
        events.extend(message_events)
        output_items.extend(completed_message["output"])
        output_index += 1

    if provider_response.tool_calls:
        tool_events, completed_tools = _tool_call_output_events(
            response_id=response_id,
            model=provider_response.model,
            provider_response=provider_response,
            parallel_tool_calls=parallel_tool_calls,
        )
        for event in tool_events:
            if isinstance(event, dict):
                event["output_index"] = int(event.get("output_index", 0)) + output_index
            events.append(event)
        output_items.extend(completed_tools["output"])

    completed_response: dict[str, Any] = {
        "id": response_id,
        "object": "response",
        "created_at": int(time.time()),
        "status": "completed",
        "model": provider_response.model,
        "output": output_items,
        "parallel_tool_calls": parallel_tool_calls,
    }
    if provider_response.text:
        completed_response["output_text"] = provider_response.text

    events.append({"type": "response.completed", "response": completed_response})
    events.append("[DONE]")
    return events


@dataclass(slots=True)
class RunningCodexProviderBridge:
    provider_name: str
    display_name: str
    base_url: str
    env_key: str
    env_value: str
    server: ThreadingHTTPServer
    thread: threading.Thread

    def codex_config_overrides(self) -> list[str]:
        provider_table = (
            "{"
            f"name={json.dumps(self.display_name)},"
            f"base_url={json.dumps(self.base_url)},"
            f"env_key={json.dumps(self.env_key)},"
            'wire_api="responses",'
            "supports_websockets=false,"
            "requires_openai_auth=false"
            "}"
        )
        return [
            f"model_provider={json.dumps(self.provider_name)}",
            f"model_providers.{self.provider_name}={provider_table}",
        ]

    def subprocess_env(self, base_env: dict[str, str] | None = None) -> dict[str, str]:
        env = dict(base_env or {})
        env[self.env_key] = self.env_value
        return env

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2.0)


def _make_handler(
    *,
    model_config: ModelConfig,
    valid_env_key: str,
    valid_env_value: str,
) -> type[BaseHTTPRequestHandler]:
    request_counter = count(1)

    class CodexProviderBridgeHandler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def _normalized_path(self) -> str:
            return urlsplit(self.path).path.rstrip("/") or "/"

        def _is_authorized(self) -> bool:
            auth_header = str(self.headers.get("Authorization", "") or "")
            expected_auth = f"Bearer {valid_env_value}"
            return auth_header == expected_auth

        def _send_json_payload(self, status: int, payload_obj: dict[str, Any]) -> None:
            payload = json.dumps(payload_obj, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def _json_error(self, status: int, message: str) -> None:
            self._send_json_payload(status, {"error": {"message": message, "type": "bridge_error"}})

        def _read_json(self) -> dict[str, Any]:
            raw_length = self.headers.get("Content-Length", "0") or "0"
            length = int(raw_length)
            body = self.rfile.read(length) if length > 0 else b"{}"
            loaded = json.loads(body.decode("utf-8"))
            return loaded if isinstance(loaded, dict) else {}

        def _send_stream(self, events: list[dict[str, Any] | str]) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.end_headers()
            sequence = count(1)
            for event in events:
                payload = event
                if isinstance(event, dict) and "sequence_number" not in event:
                    payload = dict(event)
                    payload["sequence_number"] = next(sequence)
                self.wfile.write(f"data: {json.dumps(payload, ensure_ascii=False)}\n\n".encode("utf-8"))
                self.wfile.flush()

        def _send_json_response(self, provider_response: ProviderResponse, request_body: dict[str, Any]) -> None:
            events = build_sse_events(request_body, provider_response)
            completed = next(
                event["response"]
                for event in reversed(events)
                if isinstance(event, dict) and event.get("type") == "response.completed"
            )
            self._send_json_payload(200, completed)

        def do_GET(self) -> None:  # noqa: N802
            _ = next(request_counter)
            if self._normalized_path() != "/v1/models":
                self._json_error(404, f"Unsupported path: {self.path}")
                return
            if not self._is_authorized():
                self._json_error(401, f"Missing or invalid bridge credential in {valid_env_key}")
                return

            self._send_json_payload(
                200,
                {
                    "object": "list",
                    "data": [
                        {
                            "id": model_config.model.strip() or "agent-sec-lab-bridge",
                            "object": "model",
                            "created": int(time.time()),
                            "owned_by": "agent-sec-lab-bridge",
                        }
                    ],
                },
            )

        def do_POST(self) -> None:  # noqa: N802
            _ = next(request_counter)
            if self._normalized_path() != "/v1/responses":
                self._json_error(404, f"Unsupported path: {self.path}")
                return

            if not self._is_authorized():
                self._json_error(401, f"Missing or invalid bridge credential in {valid_env_key}")
                return

            try:
                request_body = self._read_json()
                messages = _build_chat_messages(request_body)
                tools = _build_provider_tools(request_body)
                provider_response = chat_completion(model_config, messages, tools=tools or None)
                if bool(request_body.get("stream", True)):
                    self._send_stream(build_sse_events(request_body, provider_response))
                else:
                    self._send_json_response(provider_response, request_body)
            except Exception as exc:
                self._json_error(500, f"{type(exc).__name__}: {exc}")

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            return

    return CodexProviderBridgeHandler


@contextmanager
def start_codex_provider_bridge(
    model_config: ModelConfig,
    *,
    provider_name: str = "agent-sec-lab-bridge",
    display_name: str = "agent-sec-lab provider bridge",
    env_key: str = "CODEX_PROVIDER_BRIDGE_API_KEY",
) -> Iterator[RunningCodexProviderBridge]:
    env_value = f"bridge-{uuid.uuid4().hex}"
    handler = _make_handler(
        model_config=model_config,
        valid_env_key=env_key,
        valid_env_value=env_value,
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, name="codex-provider-bridge", daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    bridge = RunningCodexProviderBridge(
        provider_name=provider_name,
        display_name=display_name,
        base_url=f"http://{host}:{port}/v1",
        env_key=env_key,
        env_value=env_value,
        server=server,
        thread=thread,
    )
    try:
        yield bridge
    finally:
        bridge.close()
