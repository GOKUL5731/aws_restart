"""Reusable JSON file reader used by the main program."""

import json
from pathlib import Path
from typing import Any


def readJsonFile(fileName: str | Path) -> dict[str, Any] | None:
    path = Path(fileName)
    try:
        with path.open("r", encoding="utf-8") as json_file:
            data = json.load(json_file)
    except (OSError, json.JSONDecodeError) as error:
        print(f"Could not read JSON file '{path}': {error}")
        return None
    return data
