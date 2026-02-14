import re
import httpx
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, List

from oko.service.service_config import load_config, save_config
from oko.service.service_variable import load_variables

SUPPORTED_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}
RUNTIME_HISTORY_LIMIT = 5

_VARIABLE_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}")


def add_endpoint(
    collection_name: str,
    alias: str,
    url: str,
    method: str = "GET",
) -> Path:
    config = load_config()
    root = Path(config["root_path"])

    method = method.upper()

    if method not in SUPPORTED_METHODS:
        raise ValueError(
            f"Unsupported HTTP method '{method}'. "
            f"Supported methods: {', '.join(SUPPORTED_METHODS)}"
        )

    collection_path = root / "collections" / collection_name
    if not collection_path.exists():
        raise FileNotFoundError(f"Collection '{collection_name}' does not exist")

    endpoints_file = collection_path / "endpoints.json"

    if endpoints_file.exists():
        data = json.loads(endpoints_file.read_text())
    else:
        data = {"endpoints": {}}

    if alias in data["endpoints"]:
        raise ValueError(
            f"Endpoint '{alias}' already exists in collection '{collection_name}'"
        )

    data["endpoints"][alias] = {
        "url": url,
        "method": method,
        "created_at": datetime.now().isoformat(),
    }

    endpoints_file.write_text(json.dumps(data, indent=2))
    return endpoints_file


def list_endpoints(collection_name: str) -> List[Dict[str, str]]:
    """
    Lists endpoints for a given collection.

    Returns:
        [
            {
                "alias": "login",
                "method": "POST",
                "url": "https://..."
            }
        ]
    """
    config = load_config()
    root = Path(config["root_path"])

    collection_path = root / "collections" / collection_name
    if not collection_path.exists():
        raise FileNotFoundError(f"Collection '{collection_name}' does not exist")

    endpoints_file = collection_path / "endpoints.json"
    if not endpoints_file.exists():
        return []

    data = json.loads(endpoints_file.read_text())
    endpoints = data.get("endpoints", {})

    results = []
    for alias, meta in endpoints.items():
        results.append(
            {
                "alias": alias,
                "method": meta.get("method", ""),
                "url": meta.get("url", ""),
            }
        )

    return results


def run_endpoint(
    collection: str,
    alias: str,
    params: Optional[Dict[str, str]] = None,
    headers: Optional[Dict[str, str]] = None,
    json_body: Optional[Dict] = None,
    timeout: int = 10,
    runtime_variables: Optional[Dict[str, str]] = None,
) -> httpx.Response:
    request_data = prepare_endpoint_request(
        collection=collection,
        alias=alias,
        params=params,
        headers=headers,
        json_body=json_body,
        runtime_variables=runtime_variables,
    )

    response = httpx.request(
        method=request_data["method"],
        url=request_data["url"],
        params=request_data["params"],
        headers=request_data["headers"],
        json=request_data["json"],
        timeout=timeout,
    )

    return response


def prepare_endpoint_request(
    collection: str,
    alias: str,
    params: Optional[Dict[str, str]] = None,
    headers: Optional[Dict[str, str]] = None,
    json_body: Optional[Dict] = None,
    runtime_variables: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    # 1. Load config
    config = load_config()
    root = Path(config["root_path"])

    # 2. Load endpoint
    endpoint = _load_endpoint(root, collection, alias)

    # 3. Load variables and merge with runtime variables
    global_variables = load_variables()
    runtime_variables = _expand_dotted_keys(runtime_variables or {})
    # Runtime variables take precedence over global variables
    variables = _deep_merge(global_variables, runtime_variables)

    # 4. Resolve variables
    url = resolve_variables(endpoint["url"], variables)
    params = resolve_variables(params, variables) if params else None
    headers = resolve_variables(headers, variables) if headers else None
    json_body = resolve_variables(json_body, variables) if json_body else None

    _assert_no_unresolved_placeholders(url, "URL")
    _assert_no_unresolved_placeholders(params, "params")
    _assert_no_unresolved_placeholders(headers, "headers")
    _assert_no_unresolved_placeholders(json_body, "json")

    return {
        "method": endpoint["method"],
        "url": url,
        "params": params,
        "headers": headers,
        "json": json_body,
    }


def list_required_variables(
    collection: str,
    alias: str,
    params: Optional[Dict[str, str]] = None,
    headers: Optional[Dict[str, str]] = None,
    json_body: Optional[Dict] = None,
) -> List[str]:
    """
    Return variable paths required by endpoint URL + runtime inputs.
    Keeps original discovery order and removes duplicates.
    """
    config = load_config()
    root = Path(config["root_path"])
    endpoint = _load_endpoint(root, collection, alias)

    required = []
    seen = set()

    for value in [endpoint["url"], params, headers, json_body]:
        for path in extract_variable_paths(value):
            if path not in seen:
                seen.add(path)
                required.append(path)

    return required


def list_missing_variables(
    collection: str,
    alias: str,
    params: Optional[Dict[str, str]] = None,
    headers: Optional[Dict[str, str]] = None,
    json_body: Optional[Dict] = None,
    runtime_variables: Optional[Dict[str, str]] = None,
) -> List[str]:
    """
    Return unresolved variable paths using global + runtime variables.
    """
    required = list_required_variables(collection, alias, params, headers, json_body)

    global_variables = load_variables()
    runtime_variables = _expand_dotted_keys(runtime_variables or {})
    available = _deep_merge(global_variables, runtime_variables)

    missing = []
    for path in required:
        if _get_variable_value(path, available) is None:
            missing.append(path)

    return missing


def extract_variable_paths(value: Any) -> List[str]:
    """
    Extract unique variable paths from strings, dicts and lists.
    """
    found = []
    seen = set()

    def walk(current: Any) -> None:
        if isinstance(current, str):
            for match in _VARIABLE_PATTERN.finditer(current):
                path = match.group(1)
                if path not in seen:
                    seen.add(path)
                    found.append(path)
            return

        if isinstance(current, dict):
            for item in current.values():
                walk(item)
            return

        if isinstance(current, list):
            for item in current:
                walk(item)

    walk(value)
    return found


def get_last_runtime_value(collection: str, alias: str, variable: str) -> Optional[str]:
    """
    Return the most recent runtime value for a variable in a specific endpoint.
    """
    config = load_config()
    history = config.get("runtime_history", {})
    endpoint_key = _endpoint_history_key(collection, alias)
    endpoint_history = history.get(endpoint_key, {})
    values = endpoint_history.get(variable, [])

    if values:
        return values[0]
    return None


def save_runtime_history(
    collection: str, alias: str, runtime_variables: Optional[Dict[str, str]]
) -> None:
    """
    Save runtime variable values for endpoint and keep the most recent entries.
    """
    if not runtime_variables:
        return

    config = load_config()
    history = config.get("runtime_history", {})
    endpoint_key = _endpoint_history_key(collection, alias)
    endpoint_history = history.get(endpoint_key, {})

    for key, value in runtime_variables.items():
        if value is None:
            continue
        text_value = str(value).strip()
        if not text_value:
            continue

        values = endpoint_history.get(key, [])
        values = [item for item in values if item != text_value]
        values.insert(0, text_value)
        endpoint_history[key] = values[:RUNTIME_HISTORY_LIMIT]

    history[endpoint_key] = endpoint_history
    config["runtime_history"] = history
    save_config(config)


def resolve_variables(value: Any, variables: dict) -> Any:
    """
    Recursively resolves variables in strings, dicts, and lists.

    Supported syntax:
        {{var}}
        {{user.id}}

    Args:
        value: Any value (str, dict, list, etc.)
        variables: Dict of available variables

    Returns:
        Value with resolved variables
    """

    if isinstance(value, str):
        return _resolve_string(value, variables)

    if isinstance(value, dict):
        return {key: resolve_variables(val, variables) for key, val in value.items()}

    if isinstance(value, list):
        return [resolve_variables(item, variables) for item in value]

    # Any other type (int, float, bool, None)
    return value


def _resolve_string(text: str, variables: dict) -> str:
    def replacer(match):
        path = match.group(1)
        resolved = _get_variable_value(path, variables)

        # If variable not found → keep original {{var}}
        return str(resolved) if resolved is not None else match.group(0)

    return _VARIABLE_PATTERN.sub(replacer, text)


def _get_variable_value(path: str, variables: dict) -> Any:
    """
    Resolves dotted variable paths like:
        token
        user.id
        user.profile.email
    """
    parts = path.split(".")
    current = variables

    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None

    return current


def _load_endpoint(root: Path, collection: str, alias: str) -> Dict[str, Any]:
    collection_path = root / "collections" / collection
    if not collection_path.exists():
        raise FileNotFoundError(f"Collection '{collection}' does not exist")

    endpoints_file = collection_path / "endpoints.json"
    if not endpoints_file.exists():
        raise FileNotFoundError(f"No endpoints defined for collection '{collection}'")

    data = json.loads(endpoints_file.read_text())

    if alias not in data.get("endpoints", {}):
        raise ValueError(f"Endpoint '{alias}' not found in collection '{collection}'")

    return data["endpoints"][alias]


def _expand_dotted_keys(values: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert {"a.b": 1} into {"a": {"b": 1}} recursively for merge/resolution.
    """
    expanded: Dict[str, Any] = {}

    for key, value in values.items():
        parts = key.split(".")
        current = expanded
        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value

    return expanded


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge dictionaries (override wins).
    """
    result = dict(base)

    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def _endpoint_history_key(collection: str, alias: str) -> str:
    return f"{collection}::{alias}"


def _assert_no_unresolved_placeholders(value: Any, field_name: str) -> None:
    unresolved = extract_variable_paths(value)
    if unresolved:
        names = ", ".join(unresolved)
        raise ValueError(
            f"Unresolved variables in {field_name}: {names}. "
            "Define them with 'oko variable add' or pass '--var/--vars'."
        )
