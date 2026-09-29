import logging
import os

import psycopg
import pyarrow as pa
from psycopg import sql

logger = logging.getLogger(__name__)


def write_to_postgres(data: pa.Table, table_name: str, chunksize: int = 100) -> pa.Table:
    """Write an Arrow table to Postgres using COPY for bulk loading.

    Getting the connection data from the environment. For now, this tool is
    tighly coupled to writing to a specific database (the features database)

    The data is written via COPY statements. This isn't the fastest way of doing
    things, but it's relatively stable.

    Better ways could be to use arrow's ADBC as documented in
    https://swissgeoplatform.atlassian.net/wiki/spaces/GEOIN/pages/1090486273/Tool+set+Implementation#ADBC
    but that would require a more precise alignment of data types

    The data in the postgres table will get entirely replaced
    """

    db_endpoint = os.getenv("FEATURES_DB_ENDPOINT")
    db_port = os.getenv("FEATURES_DB_PORT")
    db_name = os.getenv("FEATURES_DB_NAME")
    db_username = os.getenv("FEATURES_DB_USER")
    db_password = os.getenv("FEATURES_DB_PASSWORD")

    logger.info("Writing data to postgres table %s", table_name)
    logger.debug("Connecting to postgres")

    with psycopg.connect(
        host=db_endpoint,
        port=db_port,
        dbname=db_name,
        user=db_username,
        password=db_password,
        # sslmode="require",
    ) as conn:
        schema_names = list(data.schema.names)
        cols = [sql.Identifier(name) for name in schema_names]
        logger.debug("Going to write columns: %s", schema_names)

        with conn.cursor() as cursor:
            logger.debug("Truncating table")
            truncate_stmt = sql.SQL("TRUNCATE TABLE {}").format(
                sql.Identifier(*table_name.split("."))
            )
            cursor.execute(truncate_stmt)

            cols_sql = sql.SQL(", ").join(cols)
            copy_sql = sql.SQL("COPY {} ({}) FROM STDIN").format(
                sql.Identifier(*table_name.split(".")), cols_sql
            )
            logger.debug("Writing to postgres in chunks of size %i", chunksize)

            for batch_counter, batch in enumerate(data.to_batches(max_chunksize=chunksize)):
                if batch_counter % 10 == 0:
                    # let's log only every 10th batch to not spam the logs
                    logger.debug("Inserting batch %s", batch_counter)

                # pass the SQL object directly (psycopg accepts a psycopg.sql.Query/Composed)
                with cursor.copy(copy_sql) as copy:
                    # write each row in batch in the column order of the table
                    for row in batch.to_pylist():
                        # ensure column order matches schema_names
                        values = tuple(row[col] for col in schema_names)
                        copy.write_row(values)

    return data
