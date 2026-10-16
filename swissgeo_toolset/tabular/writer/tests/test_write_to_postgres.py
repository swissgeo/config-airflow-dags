import psycopg
import pyarrow as pa
import pytest
from psycopg import sql
from swissgeo_toolset.tabular.writer import write_to_postgres


def test_write_to_postgres_basic(postgres_table):
    conn, table_name = postgres_table
    data = pa.table({"id": [1, 2, 3], "label": ["a", "b", "c"]})

    write_to_postgres(data, table_name)

    with conn.cursor() as cur:
        query = sql.SQL("SELECT id, label FROM {} ORDER BY id").format(sql.Identifier(table_name))
        cur.execute(query)
        assert cur.fetchall() == [(1, "a"), (2, "b"), (3, "c")]


def test_write_to_postgres_returns_input(postgres_table):
    _, table_name = postgres_table
    data = pa.table({"id": [1], "label": ["x"]})

    result = write_to_postgres(data, table_name)

    assert result.equals(data)


def test_write_to_postgres_replaces_existing(postgres_table):
    conn, table_name = postgres_table
    initial = pa.table({"id": [1, 2], "label": ["a", "b"]})
    replacement = pa.table({"id": [99], "label": ["z"]})

    write_to_postgres(initial, table_name)
    write_to_postgres(replacement, table_name)

    with conn.cursor() as cur:
        query = sql.SQL("SELECT id, label FROM {}").format(sql.Identifier(table_name))
        cur.execute(query)
        assert cur.fetchall() == [(99, "z")]


def test_write_to_postgres_chunking(postgres_table):
    conn, table_name = postgres_table
    n = 25
    data = pa.table({"id": list(range(n)), "label": [str(i) for i in range(n)]})

    write_to_postgres(data, table_name, chunksize=7)

    with conn.cursor() as cur:
        query = sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table_name))
        cur.execute(query)
        assert cur.fetchone()[0] == n


def test_write_to_postgres_unmatching(postgres_table):
    _, table_name = postgres_table
    data = pa.table({"id": [1], "inexisting_col": ["x"]})

    with pytest.raises(psycopg.Error):
        write_to_postgres(data, table_name)


def test_write_to_postgres_unmatching_doesnt_truncate(postgres_table):
    conn, table_name = postgres_table

    data = pa.table({"id": [1], "label": ["x"]})
    write_to_postgres(data, table_name)

    wrong_data = pa.table({"id": [1], "inexisting_col": ["x"]})

    with pytest.raises(psycopg.Error):
        write_to_postgres(wrong_data, table_name)

    with conn.cursor() as cur:
        # we want to make sure that the previous data still exists when the writing fails
        query = sql.SQL("SELECT id, label FROM {}").format(sql.Identifier(table_name))
        cur.execute(query)
        assert cur.fetchall() == [(1, "x")]
