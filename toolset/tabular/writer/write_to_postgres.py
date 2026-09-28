import logging
import os

import psycopg
import pyarrow as pa
from psycopg import sql
from pyarrow import csv

logger = logging.getLogger(__name__)


def write_to_postgres(arrow_table: pa.Table, table_name: str, chunksize: int = 1000) -> pa.Table:
    """Write an Arrow table to Postgres using COPY for bulk loading.

    Getting the connection data from the environment. For now, this tool is
    tightly coupled to writing to a specific database (the features database)

    The data is written via COPY statements. This isn't the fastest way of doing
    things, but it's relatively stable.

    Better ways could be to use arrow's ADBC as documented in
    https://swissgeoplatform.atlassian.net/wiki/spaces/GEOIN/pages/1090486273/Tool+set+Implementation#ADBC
    but that would require a more precise alignment of data types

    The data in the postgres table will get entirely replaced
    """

    # deliberately not having a fallback on these env variables so that
    # psycopg won't fall back to some local sockets or something
    # Instead this will reaise an error when the ENV isn't set
    db_endpoint = os.environ["FEATURES_DB_ENDPOINT"]
    db_port = os.environ["FEATURES_DB_PORT"]
    db_name = os.environ["FEATURES_DB_NAME"]
    db_username = os.environ["FEATURES_DB_USER"]
    db_password = os.environ["FEATURES_DB_PASSWORD"]

    logger.info("Writing data to postgres table %s", table_name)
    logger.debug("Connecting to postgres")

    with psycopg.connect(
        host=db_endpoint,
        port=db_port,
        dbname=db_name,
        user=db_username,
        password=db_password,
        sslmode="require"
        if os.environ.get("FEATURES_DB_SSL_REQUIRED", "True").lower() in ("true", "1")
        else "disable",
    ) as conn:
        schema_names = list(arrow_table.schema.names)
        cols = [sql.Identifier(name) for name in schema_names]
        logger.debug("Going to write columns: %s", schema_names)

        with conn.transaction(), conn.cursor() as cursor:
            logger.debug("Truncating table")
            truncate_stmt = sql.SQL("TRUNCATE TABLE {}").format(
                sql.Identifier(*table_name.split("."))
            )
            cursor.execute(truncate_stmt)

            cols_sql = sql.SQL(", ").join(cols)
            copy_sql = sql.SQL("COPY {} ({}) FROM STDIN (FORMAT csv)").format(
                sql.Identifier(*table_name.split(".")), cols_sql
            )

            write_options = csv.WriteOptions(include_header=False)

            logger.debug("Writing to postgres in chunks of size %i", chunksize)
            # a single COPY for the whole table; pyarrow serializes each batch to CSV in C++,
            # so no row ever passes through Python
            with cursor.copy(copy_sql) as copy:
                for batch in arrow_table.to_batches(max_chunksize=chunksize):
                    sink = pa.BufferOutputStream()
                    csv.write_csv(batch, sink, write_options=write_options)
                    copy.write(sink.getvalue().to_pybytes())

    return arrow_table
