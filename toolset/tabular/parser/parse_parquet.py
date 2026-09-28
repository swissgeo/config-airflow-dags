import io
import logging
import typing

import pyarrow as pa
import pyarrow.parquet as pq

logger = logging.getLogger("pipeline_toolset")


def parse_parquet(stream: typing.IO[bytes]) -> pa.Table:
    logger.info("Read parquet file from byte stream")

    # materialize into a seekable buffer
    buffer = io.BytesIO(stream.read())
    table = pq.read_table(buffer)

    # TODO consider if closing it here is the correct place, see parse_csv
    stream.close()
    return table
