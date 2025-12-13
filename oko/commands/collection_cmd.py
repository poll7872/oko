from pathlib import Path
from oko.service.service_collection import create_collection
from oko.service.service_config import load_config
from oko.ui.prints import print_success, print_error


def add_collection(name: str):
    try:
        config = load_config()
        oko_root = Path(config["root_path"])

        path = create_collection(oko_root, name)

        print_success(
            f"Collection [highlight]{name}[/highlight] created at:\n[info]{path}[/info]",
            title="Collection Added",
        )

    except Exception as e:
        print_error(str(e), title="Collection Error")
