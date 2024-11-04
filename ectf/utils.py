"""
MIT License

Copyright (c) 2024 - "Rising Edge" Group

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import json
import click
from pathlib import Path
import stat
from typing import Dict
import re


def extract_csrf_token(html_text: str) -> str:
    """Extracts the CSRF token from an echoCTF HTML text site"""
    regex = '<meta\\s+name="csrf-token"\\s+content="([^"]+)"'
    return re.findall(regex, html_text)[0]


def has_secure_file_permissions(file_path: Path) -> bool:
    """Check if the specified file has secure permissions (600).

    Args:
        file_path (Path): The path to the file to check.

    Returns:
        bool: True if the file has secure permissions, False otherwise.
    """
    # Retrieve the current file permissions
    file_permissions = file_path.stat().st_mode

    # Check if the user has both read and write permissions
    user_can_read = file_permissions & stat.S_IRUSR != 0
    user_can_write = file_permissions & stat.S_IWUSR != 0

    # Check if the group or others have any permissions
    group_has_permissions = (
        file_permissions & (stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH)
        != 0
    )

    # The file is considered secure if:
    # - The user has read and write permissions
    # - Group and others have no permissions
    return user_can_read and user_can_write and not group_has_permissions


def load_configuration(file_path: Path) -> Dict[str, str]:
    """Load configuration settings from a JSON file.

    Args:
        file_path (Path): The path to the JSON configuration file.

    Returns:
        dict: A dictionary containing the parsed configuration data. Returns an empty
              dictionary if the file does not exist.

    Raises:
        SystemExit: Exits the program if the file is not found, has insecure permissions,
                     or contains JSON parsing errors.
    """
    # Check if the configuration file exists
    if not file_path.exists():
        click.echo(f"Configuration file not found: {file_path}")
        click.echo("Proceeding without it.")
        return {}

    # Validate the file permissions
    if not has_secure_file_permissions(file_path):
        click.secho(
            f"File permissions must be 600: {file_path}\nExiting.",
            fg="red",
        )
        raise SystemExit(1)

    # Attempt to open and parse the JSON configuration file
    try:
        with open(file_path, "r") as f:
            return json.load(f)  # Return the loaded JSON data as a dictionary
    except json.JSONDecodeError:
        click.echo(
            f"Error parsing JSON from the configuration file: {file_path}\nExiting."
        )
        raise SystemExit(1)
