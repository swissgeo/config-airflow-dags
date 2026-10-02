import logging
from typing import Literal

import pyarrow as pa

logger = logging.getLogger("pipeline_toolset")

JoinType = Literal[
    "left semi",
    "right semi",
    "left anti",
    "right anti",
    "inner",
    "left outer",
    "right outer",
    "full outer",
]


def join_tables(
    table1: pa.Table, table2: pa.Table, keys: list[str], join_type: JoinType
) -> pa.Table:
    """Join two tables on the given keys using the specified join type.

    Under the surface, this is simply a wrapper around pyarrow's join function with some
    additional validation.
    https://arrow.apache.org/docs/python/generated/pyarrow.Table.html#pyarrow.Table.join

    Args:
        table1: The first table to join
        table2: The second table to join
        keys: The keys to join on
        join_type: The type of join to perform

    Returns:
        The joined table.
    """

    if join_type not in JoinType.__args__:
        raise ValueError(f"Invalid join type: {join_type}")

    # build a list of the column names that aren't part of the keys to join on
    # then see if there are duplicates in the tables. Even though pyarrow technically
    # could support column name duplicates, we reject that
    table1_without_keys = table1.drop(keys)
    table2_without_keys = table2.drop(keys)

    common_keys = list(
        set(table1_without_keys.column_names) & set(table2_without_keys.column_names)
    )
    if len(common_keys) > 0:
        raise ValueError(f"Common keys found: {common_keys}")

    logger.info("Joining tables on keys: %s with join type: %s", keys, join_type)

    return table1.join(table2, keys=keys, join_type=join_type)
