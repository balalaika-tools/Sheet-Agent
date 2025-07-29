import os
import shutil
from pathlib import Path
from typing import List, Optional


import pandas as pd
import requests


def _download_file(url: str, save_path: Path) -> None:
    """Downloads a file from a URL and saves it locally.

    Args:
        url: The URL of the file to download.
        save_path: The path to save the downloaded file.

    Raises:
        requests.exceptions.RequestException: If the download fails.
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an exception for bad status codes
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    except requests.exceptions.RequestException as e:
        # You might want to log the error here
        raise e


def _copy_local_file(source_path: Path, save_path: Path) -> None:
    """Copies a local file to the specified save path.

    Args:
        source_path: The path to the source file.
        save_path: The path to save the copied file.

    Raises:
        FileNotFoundError: If the source file doesn't exist.
        PermissionError: If there are permission issues copying the file.
        OSError: For other file system related errors.
    """
    try:
        shutil.copy2(source_path, save_path)
    except (FileNotFoundError, PermissionError, OSError) as e:
        raise e


def copy_excel(workbook_path: Path, workbook_source: str, is_local_file: bool):
    """
    Copies an Excel file into the temporary folder specified by workbook_path,
    either by downloading it from a URL or copying it from a local file.
    """
    if is_local_file:
        # Copy local file to the sandbox
        source_path = Path(workbook_source)
        _copy_local_file(source_path, workbook_path)
    else:
        # Download from URL
        _download_file(workbook_source, workbook_path)
