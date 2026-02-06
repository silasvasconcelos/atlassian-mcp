from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any


@dataclass(frozen=True)
class Operation:
    name: str
    method: str
    path: str
    description: str
    input_schema: dict[str, Any]
    path_params: list[str]
    query_params: list[str]
    header_params: list[str]
    required_params: set[str]
    request_body_required: bool
    request_body_content_type: str | None


def _resolve_ref(schema: dict[str, Any], spec: dict[str, Any], seen: set[str]) -> dict[str, Any]:
    ref = schema.get("$ref")
    if not ref or not isinstance(ref, str):
        return schema
    if ref in seen:
        return {"type": "object"}
    if not ref.startswith("#/components/"):
        return schema
    seen.add(ref)
    path = ref.lstrip("#/").split("/")
    node: Any = spec
    for part in path:
        if not isinstance(node, dict):
            return schema
        node = node.get(part)
        if node is None:
            return schema
    if not isinstance(node, dict):
        return schema
    resolved = _resolve_schema(node, spec, seen)
    return resolved


def _resolve_schema(schema: dict[str, Any], spec: dict[str, Any], seen: set[str] | None = None) -> dict[str, Any]:
    if seen is None:
        seen = set()
    if "$ref" in schema:
        return _resolve_ref(schema, spec, seen)

    if "allOf" in schema:
        merged: dict[str, Any] = {"type": "object", "properties": {}}
        required: set[str] = set()
        for subschema in schema.get("allOf", []):
            resolved = _resolve_schema(subschema, spec, seen)
            if resolved.get("type") == "object":
                merged["properties"].update(resolved.get("properties", {}))
                required.update(resolved.get("required", []))
        if required:
            merged["required"] = sorted(required)
        return merged

    if schema.get("type") == "array" and isinstance(schema.get("items"), dict):
        return {**schema, "items": _resolve_schema(schema["items"], spec, seen)}

    if schema.get("type") == "object" and isinstance(schema.get("properties"), dict):
        properties = {
            name: _resolve_schema(prop, spec, seen)
            for name, prop in schema["properties"].items()
        }
        return {**schema, "properties": properties}

    return schema


def _parameter_schema(param: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    schema = param.get("schema") or {"type": "string"}
    if not isinstance(schema, dict):
        return {"type": "string"}
    return _resolve_schema(schema, spec)


def _request_body_schema(operation: dict[str, Any], spec: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None, bool]:
    body = operation.get("requestBody")
    if not isinstance(body, dict):
        return None, None, False
    required = bool(body.get("required"))
    content = body.get("content")
    if not isinstance(content, dict):
        return None, None, required

    if "application/json" in content:
        media = content["application/json"]
        content_type = "application/json"
    else:
        content_type = next(iter(content.keys()), None)
        media = content.get(content_type, {}) if content_type else {}

    schema = media.get("schema") if isinstance(media, dict) else None
    if not isinstance(schema, dict):
        return None, content_type, required
    return _resolve_schema(schema, spec), content_type, required


def _safe_tool_name(operation_id: str, method: str, path: str) -> str:
    base = f"jira_{operation_id}"
    # Cursor counts combined server + tool length (e.g. "jira-mcp:<tool>")
    server_name = "jira-mcp"
    max_tool_len = 60 - len(server_name) - 1
    if len(base) <= max_tool_len:
        return base
    digest = hashlib.sha1(f"{method}:{path}:{operation_id}".encode("utf-8")).hexdigest()[:8]
    trimmed = base[: max_tool_len - 2 - len(digest)]
    return f"{trimmed}__{digest}"


def build_operations(spec: dict[str, Any]) -> list[Operation]:
    operations: list[Operation] = []
    paths = spec.get("paths", {})
    if not isinstance(paths, dict):
        return operations

    for path, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        for method, operation in methods.items():
            if method.lower() not in {"get", "post", "put", "delete", "patch", "head", "options"}:
                continue
            if not isinstance(operation, dict):
                continue

            operation_id = operation.get("operationId")
            if not operation_id:
                continue
            name = _safe_tool_name(operation_id, method, path)
            summary = operation.get("summary") or ""
            description = operation.get("description") or ""
            desc = (summary + "\n\n" + description).strip()

            params = operation.get("parameters", [])
            path_params: list[str] = []
            query_params: list[str] = []
            header_params: list[str] = []
            required_params: set[str] = set()
            properties: dict[str, Any] = {}

            if isinstance(params, list):
                for param in params:
                    if not isinstance(param, dict):
                        continue
                    name_param = param.get("name")
                    location = param.get("in")
                    if not name_param or not location:
                        continue
                    if location == "path":
                        path_params.append(name_param)
                    elif location == "query":
                        query_params.append(name_param)
                    elif location == "header":
                        header_params.append(name_param)

                    properties[name_param] = _parameter_schema(param, spec)
                    if param.get("required"):
                        required_params.add(name_param)

            body_schema, content_type, body_required = _request_body_schema(operation, spec)
            if body_schema is not None:
                properties["body"] = body_schema
                if body_required:
                    required_params.add("body")

            properties["headers"] = {
                "type": "object",
                "additionalProperties": {"type": "string"},
            }

            input_schema: dict[str, Any] = {
                "type": "object",
                "properties": properties,
                "additionalProperties": False,
            }
            if required_params:
                input_schema["required"] = sorted(required_params)

            operations.append(
                Operation(
                    name=name,
                    method=method,
                    path=path,
                    description=desc,
                    input_schema=input_schema,
                    path_params=path_params,
                    query_params=query_params,
                    header_params=header_params,
                    required_params=required_params,
                    request_body_required=body_required,
                    request_body_content_type=content_type,
                )
            )

    return operations
