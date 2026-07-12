"""File system utilities."""

import json
import shutil
from pathlib import Path
from typing import Any

import yaml

from app.exceptions.application_exception import ApplicationException


class FileHelper:
    """Helper for safe file and directory operations."""

    @staticmethod
    def ensure_directory(path: Path) -> Path:
        """Create a directory if it does not exist."""
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def read_text(path: Path, encoding: str = "utf-8") -> str:
        """Read a text file."""
        if not path.exists():
            raise ApplicationException(f"File not found: {path}")
        return path.read_text(encoding=encoding)

    @staticmethod
    def write_text(path: Path, content: str, encoding: str = "utf-8") -> None:
        """Write text to a file, creating parent directories if needed."""
        FileHelper.ensure_directory(path.parent)
        path.write_text(content, encoding=encoding)

    @staticmethod
    def read_yaml(path: Path) -> dict[str, Any]:
        """Read and parse a YAML file."""
        content = FileHelper.read_text(path)
        data = yaml.safe_load(content)
        return data if isinstance(data, dict) else {}

    @staticmethod
    def write_yaml(path: Path, data: dict[str, Any]) -> None:
        """Write a dictionary to a YAML file."""
        FileHelper.ensure_directory(path.parent)
        path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    @staticmethod
    def read_json(path: Path) -> dict[str, Any]:
        """Read and parse a JSON file."""
        content = FileHelper.read_text(path)
        data = json.loads(content)
        return data if isinstance(data, dict) else {}

    @staticmethod
    def write_json(path: Path, data: dict[str, Any], indent: int = 2) -> None:
        """Write a dictionary to a JSON file."""
        FileHelper.ensure_directory(path.parent)
        path.write_text(json.dumps(data, indent=indent), encoding="utf-8")

    @staticmethod
    def copy_file(source: Path, destination: Path) -> None:
        """Copy a file to a destination path."""
        FileHelper.ensure_directory(destination.parent)
        shutil.copy2(source, destination)
