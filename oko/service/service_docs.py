import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from oko.service.service_config import load_config

_VARIABLE_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}")


def generate_api_readme() -> Path:
    """
    Generates .oko/README.md from current config, collections and endpoints.
    """
    config = load_config()
    root = Path(config["root_path"])
    readme_path = root / "README.md"

    project_name = config.get("project_name", root.parent.name)
    variables = config.get("variables", {})
    collections = _load_collections(root)

    lines: List[str] = []
    lines.append(f"# {project_name} API Docs")
    lines.append("")
    lines.append("> Archivo generado automáticamente por OKO.")
    lines.append(f"> Actualizado: {datetime.now().isoformat(timespec='seconds')}")
    lines.append("")

    base_url = variables.get("base_url")
    if base_url:
        lines.append(f"- **Base URL:** `{base_url}`")
    lines.append(f"- **Colecciones:** `{len(collections)}`")
    lines.append("")

    lines.append("## Variables Globales")
    lines.append("")
    if variables:
        for key in sorted(variables.keys()):
            lines.append(f"- `{key}` = `{variables[key]}`")
    else:
        lines.append("_Sin variables globales._")
    lines.append("")

    lines.append("## Colecciones y Endpoints")
    lines.append("")
    if not collections:
        lines.append("_No hay colecciones aún. Usa `oko collection add <name>`._")
        lines.append("")
    else:
        for collection_name, endpoints in collections.items():
            lines.append(f"### {collection_name}")
            lines.append("")
            if not endpoints:
                lines.append("_Sin endpoints._")
                lines.append("")
                continue

            lines.append("| Alias | Method | URL | Variables |")
            lines.append("|---|---|---|---|")
            for endpoint in endpoints:
                vars_used = _extract_variable_paths(endpoint["url"])
                vars_label = ", ".join(f"`{name}`" for name in vars_used) or "-"
                lines.append(
                    f"| `{endpoint['alias']}` | `{endpoint['method']}` | "
                    f"`{endpoint['url']}` | {vars_label} |"
                )
            lines.append("")

    readme_path.write_text("\n".join(lines), encoding="utf-8")
    return readme_path


def _load_collections(root: Path) -> Dict[str, List[Dict[str, str]]]:
    collections: Dict[str, List[Dict[str, str]]] = {}
    collections_dir = root / "collections"

    if not collections_dir.exists():
        return collections

    for collection_path in sorted(
        [item for item in collections_dir.iterdir() if item.is_dir()],
        key=lambda p: p.name.lower(),
    ):
        endpoints_file = collection_path / "endpoints.json"
        endpoints: List[Dict[str, str]] = []
        if endpoints_file.exists():
            data = json.loads(endpoints_file.read_text(encoding="utf-8"))
            for alias, meta in sorted(
                data.get("endpoints", {}).items(),
                key=lambda item: item[0].lower(),
            ):
                endpoints.append(
                    {
                        "alias": alias,
                        "method": str(meta.get("method", "")),
                        "url": str(meta.get("url", "")),
                    }
                )
        collections[collection_path.name] = endpoints

    return collections


def _extract_variable_paths(text: str) -> List[str]:
    seen = set()
    ordered = []
    for match in _VARIABLE_PATTERN.finditer(text):
        path = match.group(1)
        if path not in seen:
            seen.add(path)
            ordered.append(path)
    return ordered
