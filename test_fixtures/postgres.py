import os
import uuid
from collections.abc import Generator

import psycopg
import pytest
from psycopg import sql
from sqlalchemy import create_engine

from models.service_oa_features.models import Base


@pytest.fixture
def postgres_connection() -> Generator[psycopg.Connection]:
    """Create a unique database and return the connection to it"""
    with psycopg.connect(
        host=os.environ["FEATURES_DB_ENDPOINT"],
        port=os.environ["FEATURES_DB_PORT"],
        dbname=os.environ["FEATURES_DB_NAME"],
        user=os.environ["FEATURES_DB_USER"],
        password=os.environ["FEATURES_DB_PASSWORD"],
    ) as admin_conn:
        db_name = f"test_{uuid.uuid4().hex[:8]}"

        # enable autocommit because CREATE/DROP cannot run inside a transaction
        admin_conn.autocommit = True

        with admin_conn.cursor() as admin_cursor:
            admin_cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))

        # Open a new connection to the unique test database
        test_conn = psycopg.connect(
            host=os.environ["FEATURES_DB_ENDPOINT"],
            port=os.environ["FEATURES_DB_PORT"],
            dbname=db_name,
            user=os.environ["FEATURES_DB_USER"],
            password=os.environ["FEATURES_DB_PASSWORD"],
        )

        with test_conn.cursor() as cursor:
            cursor.execute(sql.SQL("CREATE EXTENSION postgis"))
            test_conn.commit()

        yield test_conn

        # terminate any other backends connected to the test DB, then drop it
        with admin_conn.cursor() as cur:
            cur.execute(
                sql.SQL(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = {} "
                    "AND pid <> pg_backend_pid()"
                ).format(sql.Literal(db_name))
            )

            cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(db_name)))


@pytest.fixture
def postgres_table(
    postgres_connection: psycopg.Connection,
) -> Generator[tuple[psycopg.Connection, str]]:
    """Create a temporary table and yield (connection, qualified_table_name).

    The table has a fixed schema: id INTEGER, label TEXT.
    It is dropped after the test regardless of outcome.
    """

    # using unique names for concurrent testing
    table_name = f"test_{uuid.uuid4().hex[:8]}"

    with postgres_connection.cursor() as cur:
        query = sql.SQL("CREATE TABLE {} (id INTEGER, label TEXT)").format(
            sql.Identifier(table_name)
        )
        cur.execute(query)
        postgres_connection.commit()

    yield postgres_connection, table_name

    with postgres_connection.cursor() as cur:
        query = sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(table_name))
        cur.execute(query)
        postgres_connection.commit()


@pytest.fixture
def features_database(
    postgres_connection: psycopg.Connection, monkeypatch: pytest.MonkeyPatch
) -> Generator[psycopg.Connection]:
    """
    Create a database with the sqlalchemy models applied
    """
    conn = postgres_connection
    db_name = conn.info.dbname
    engine = create_engine("postgresql+psycopg://", creator=lambda: conn)

    # create all the sqlalchemy models
    Base.metadata.create_all(engine)

    # override the db name to be the unique one
    monkeypatch.setenv("FEATURES_DB_NAME", db_name)

    yield conn

    conn.rollback()
    engine.dispose()
    conn.close()
