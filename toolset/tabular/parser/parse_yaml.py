import logging
import typing

import yaml

logger = logging.getLogger("pipeline_toolset")


def parse_yaml(stream: typing.IO[bytes]) -> dict:
    logger.info("Going to parse yaml")

    table = yaml.safe_load(stream)
    # TODO consider if closing here is the correct place, see parse_csv
    stream.close()
    return table
