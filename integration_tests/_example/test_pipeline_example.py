import datetime as dt

import pyarrow as pa
from psycopg.rows import dict_row
from pyiceberg.schema import Schema
from pyiceberg.types import IntegerType, NestedField, StringType

import DAG._example.pipeline_example as example_dag


def test_pipeline_example(raw_catalog, landing_zone, monkeypatch):
    """Download a CSV file, parse it and put the content in a s3 table"""
    s3, bucket_name = landing_zone

    catalog, namespace = raw_catalog
    table_name = "data"
    identifier = f"{namespace}.{table_name}"

    monkeypatch.setattr(example_dag, "namespace", namespace)
    monkeypatch.setenv("LANDING_ZONE_BUCKET", bucket_name)

    table_handle = catalog.create_table(
        identifier=identifier,
        schema=Schema(
            NestedField(1, "id", IntegerType()),
            NestedField(2, "name", StringType()),
            NestedField(3, "value", IntegerType()),
        ),
    )

    s3.put_object(
        Bucket=bucket_name,
        Key="data.csv",
        Body="id,name,value\n1,alice,100\n2,bob,200\n3,charlie,300\n",
    )

    example_dag.first_step("data.csv")

    table_handle.refresh()
    result_data = table_handle.scan().to_arrow().to_pylist()

    assert result_data == [
        {"id": 1, "name": "alice", "value": 100},
        {"id": 2, "name": "bob", "value": 200},
        {"id": 3, "name": "charlie", "value": 300},
    ]


def test_pipeline_example_db_writing(features_database):
    # Create a PyArrow table matching the SQLAlchemy model
    # (models/service_oa_features/models/ch_meteoschweiz/local_forecast/tre200px.py)
    data = pa.table(
        {
            "value": [12.34],
            "id": [1],
            "datetime": [dt.datetime(2026, 1, 1, 0, 0, tzinfo=dt.UTC)],
            "feature_id": ["feature_1"],
            "point_id": [100],
            "point_type_id": [1],
            "point_type_de": ["type_de"],
            "point_type_fr": ["type_fr"],
            "point_type_it": ["type_it"],
            "point_type_en": ["type_en"],
            "station_abbr": [None],
            "postal_code": [None],
            "point_name": [None],
            "point_height_masl": [None],
            "geometry": [None],
            "parameter_shortname": ["tre200px"],
            "parameter_description_de": ["desc_de"],
            "parameter_description_fr": ["desc_fr"],
            "parameter_description_it": ["desc_it"],
            "parameter_description_en": ["desc_en"],
            "parameter_group_de": ["group_de"],
            "parameter_group_fr": ["group_fr"],
            "parameter_group_it": ["group_it"],
            "parameter_group_en": ["group_en"],
            "parameter_granularity": ["200px"],
            "parameter_decimals": [2],
            "parameter_datatype": ["float"],
            "parameter_unit": [None],
        }
    )
    example_dag.write_to_db(data)

    with features_database.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT * FROM ch_meteoschweiz_local_forecast_tre200px")
        rows = cur.fetchall()

    assert data.to_pylist() == rows
