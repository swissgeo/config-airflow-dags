import logging
import os

import psycopg
import pyarrow as pa
from psycopg import sql

logger = logging.getLogger(__name__)


def write_to_postgres(
    data: pa.Table,
    table_name: str,
) -> pa.Table:
    """Write an Arrow table to Postgres using COPY for bulk loading.

    Getting the connection data from the environment. For now, this tool is
    tighly coupled to writing to a specific database (the features database)

    The data in the postgres table will get entirely replaced
    """

    db_endpoint = os.getenv("FEATURES_DB_ENDPOINT")
    db_port = os.getenv("FEATURES_DB_PORT")
    db_name = os.getenv("FEATURES_DB_NAME")
    db_username = os.getenv("FEATURES_DB_USER")
    db_password = os.getenv("FEATURES_DB_PASSWORD")

    logger.info("Connecting to postgres")
    # psycopg.connect is psycopg3's connection factory
    conn = psycopg.connect(
        host=db_endpoint,
        port=db_port,
        dbname=db_name,
        user=db_username,
        password=db_password,
        sslmode="require",
    )

    schema_names = list(data.schema.names)
    cols = [sql.Identifier(name) for name in schema_names]
    logger.info(f"Going to write columns: {schema_names}")

    with conn.cursor() as cursor:
        logger.info("Truncating table")
        truncate_stmt = sql.SQL("TRUNCATE TABLE {}").format(sql.Identifier(*table_name.split(".")))
        cursor.execute(truncate_stmt)

        logger.info("Writing data to postgres via")
        cols_sql = sql.SQL(", ").join(cols)
        copy_sql = sql.SQL("COPY {} ({}) FROM STDIN").format(
            sql.Identifier(*table_name.split(".")), cols_sql
        )

        # Stream each Arrow record batch into COPY
        for batch_counter, batch in enumerate(data.to_batches(max_chunksize=25)):
            logger.info(f"Inserting batch {batch_counter}")
            # open a COPY context for this batch
            logger.debug("COPY query: %s", copy_sql)

            # pass the SQL object directly (psycopg accepts a psycopg.sql.Query/Composed)
            with cursor.copy(copy_sql) as copy:
                # write each row in batch in the column order of the table
                for row in batch.to_pylist():
                    # ensure column order matches schema_names
                    values = tuple(row[col] for col in schema_names)
                    copy.write_row(values)

    logger.info("Committing changes")
    conn.commit()
    conn.close()

    return data
