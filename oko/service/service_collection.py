import json
from datetime import datetime, timezone
from pathlib import Path


def create_collection(oko_root: Path, name: str) -> Path:
    """
    Creates a collection structure:

    .oko/
      collections/
        <name>/
          collection.json
    """

    if not name or not name.strip():
        raise ValueError("Collection name cannot be empty")

    collections_dir = oko_root / "collections"
    collection_dir = collections_dir / name

    if collection_dir.exists():
        raise FileExistsError(f"Collection '{name}' already exists")

    # create directories
    collection_dir.mkdir(parents=True)

    # collection.json (metadata only)
    collection_meta = {
        "name": name,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    (collection_dir / "collection.json").write_text(
        json.dumps(collection_meta, indent=2),
        encoding="utf-8",
    )

    return collection_dir
