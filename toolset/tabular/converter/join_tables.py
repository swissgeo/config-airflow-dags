import pyarrow as pa


def join_tables(table1: pa.Table, table2: pa.Table, keys: list[str], join_type: str) -> pa.Table:
    return table1.join(table2, keys=keys, join_type=join_type)
