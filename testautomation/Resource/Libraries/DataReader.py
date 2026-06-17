"""
DataReader - Lightweight test data reader for Robot Framework suites.
"""

from __future__ import annotations

import csv
import json
import logging
import os
from typing import Any, Dict, List

from robot.api.deco import keyword

logger = logging.getLogger(__name__)


class DataReader:
    """Read JSON/CSV/environment-backed test data."""

    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    @keyword("Read Json File")
    def read_json_file(self, file_path: str) -> Dict[str, Any]:
        absolute_path = os.path.abspath(file_path)
        logger.info("Reading JSON file: %s", absolute_path)
        with open(absolute_path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    @keyword("Read Csv File")
    def read_csv_file(self, file_path: str) -> List[Dict[str, str]]:
        absolute_path = os.path.abspath(file_path)
        logger.info("Reading CSV file: %s", absolute_path)
        with open(absolute_path, "r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            return list(reader)

    @keyword("Get Environment Variable Or Default")
    def get_environment_variable_or_default(self, name: str, default: str = "") -> str:
        value = os.getenv(name, default)
        logger.info("Resolved env var %s=%s", name, value)
        return value

    @keyword("Get Value From Dictionary")
    def get_value_from_dictionary(self, data: Dict[str, Any], key: str, default: str = "") -> str:
        value = data.get(key, default)
        logger.info("Dictionary lookup key='%s' value='%s'", key, value)
        return str(value)
