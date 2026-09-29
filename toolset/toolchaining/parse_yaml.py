import logging

import yaml

logger = logging.getLogger("pipeline_toolset")


def parse_yaml(file_path: str) -> dict:
    """Parse a YAML file into a dict

    Args:
        file_path (str): Path to the YAML file.

    Returns:
        pa.Table: The parsed YAML data as a PyArrow Table.
    """
    logger.info("Parsing yaml file")

    with open(file_path) as file:
        return yaml.safe_load(file)
