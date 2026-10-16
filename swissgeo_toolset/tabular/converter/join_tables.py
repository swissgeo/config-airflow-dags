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
    arrow_table1: pa.Table, arrow_table2: pa.Table, keys: list[str], join_type: JoinType
) -> pa.Table:
    """Join two tables on the given keys using the specified join type.

    Under the surface, this is simply a wrapper around pyarrow's join function with some
    additional validation.
    https://arrow.apache.org/docs/python/generated/pyarrow.Table.html#pyarrow.Table.join

    Args:
        arrow_table1: The first table to join
        arrow_table2: The second table to join
        keys: The keys to join on (column names)
        join_type: The type of join to perform

    Returns:
        The joined table. NOTE: The order of rows isn't guaranteed
    """

    if join_type not in JoinType.__args__:
        raise ValueError(f"Invalid join type: {join_type}")

    for key in keys:
        if key not in arrow_table1.column_names:
            raise KeyError(f"Key {key} not found in left table")
        if key not in arrow_table2.column_names:
            raise KeyError(f"Key {key} not found in right table")

    # build a list of the column names that aren't part of the keys to join on
    # then see if there are duplicates in the tables. Even though pyarrow technically
    # could support column name duplicates, we reject that
    table1_without_keys = arrow_table1.drop(keys)
    table2_without_keys = arrow_table2.drop(keys)

    common_keys = list(
        set(table1_without_keys.column_names) & set(table2_without_keys.column_names)
    )
    if len(common_keys) > 0:
        raise ValueError(f"Common keys found: {common_keys}")

    logger.info("Joining tables on keys: %s with join type: %s", keys, join_type)

    return arrow_table1.join(arrow_table2, keys=keys, join_type=join_type)
