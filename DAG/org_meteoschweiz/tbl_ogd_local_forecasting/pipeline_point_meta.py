import logging

from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import DAG
from airflow.sdk.definitions.param import Param, ParamsDict

from swissgeo_toolset.file.download_from_s3 import download_from_landingzone
from swissgeo_toolset.tabular.converter import (
    add_geometry_column,
    convert_column,
    drop_columns,
    lowercase_column_names,
)
from swissgeo_toolset.tabular.parser import parse_csv
from swissgeo_toolset.tabular.reader import read_from_s3tables
from swissgeo_toolset.tabular.writer import write_to_postgres, write_to_s3tables

NAMESPACE = "ch_meteoschweiz"

logger = logging.getLogger(__name__)

default_args = {"owner": "airflow", "depends_on_past": False, "retries": 0}

dag = DAG(
    "ch_meteoschweiz-local_forecast-points",
    default_args=default_args,
    description="Local Forecast Point Pipeline",
    schedule=None,
    catchup=False,
    params=ParamsDict(
        {
            "file_key": Param(type="string", default=""),
        }
    ),
)


def download_and_store_raw(file_key: str) -> None:
    with download_from_landingzone(file_key=file_key) as file:
        df = parse_csv(file, encoding="latin-1", delimiter=";", quote_char='"')

    df = lowercase_column_names(df)
    write_to_s3tables(df, "raw", NAMESPACE, "local_forecast_points")


def sanitize_data() -> None:
    """
    Sanitize the data

    * Simplify some data types of columns; we don't need that much precision
    * Drop unused WGS84 Columns
    """
    raw_data = read_from_s3tables("raw", NAMESPACE, "local_forecast_points")

    # simplifying the data types from long to int and double to float
    # as we're clearly not in need of that length
    postal_code = convert_column(raw_data, "postal_code", "cast", {"target_type": "int32"})
    point_height_masl = convert_column(
        postal_code, "point_height_masl", "cast", {"target_type": "float"}
    )

    point_coordinates_lv95_east = convert_column(
        point_height_masl, "point_coordinates_lv95_east", "cast", {"target_type": "float"}
    )
    point_coordinates_lv95_north = convert_column(
        point_coordinates_lv95_east,
        "point_coordinates_lv95_north",
        "cast",
        {"target_type": "float"},
    )

    without_wgs84 = drop_columns(
        point_coordinates_lv95_north, ["point_coordinates_wgs84_lat", "point_coordinates_wgs84_lon"]
    )

    write_to_s3tables(
        without_wgs84,
        "sanitize",
        NAMESPACE,
        "local_forecast_points",
    )


def export_data_to_features() -> None:
    """
    Export the data

    * Convert the geometry information to a WKT geometry
    """
    raw_data = read_from_s3tables("sanitize", NAMESPACE, "local_forecast_points")

    with_geometry = add_geometry_column(
        raw_data,
        {"north": "point_coordinates_lv95_north", "east": "point_coordinates_lv95_east"},
        "geometry",
    )

    clean_geometry = drop_columns(
        with_geometry, ["point_coordinates_lv95_north", "point_coordinates_lv95_east"]
    )

    write_to_s3tables(
        clean_geometry,
        "load",
        NAMESPACE,
        "local_forecast_points",
    )

    write_to_postgres(
        clean_geometry,
        "tbl_ogd-local-forecasting-point-meta",
    )


# Define tasks
download_and_store_raw_task = PythonOperator(
    task_id="download_and_store_raw_task",
    python_callable=download_and_store_raw,
    dag=dag,
    op_kwargs={
        "file_key": "{{ params.file_key }}",
    },
)

sanitize_task = PythonOperator(
    task_id="sanitize_task",
    python_callable=sanitize_data,
    dag=dag,
)

export_data_to_features_task = PythonOperator(
    task_id="export_data_to_features_task",
    python_callable=export_data_to_features,
    dag=dag,
)


# download_and_store_raw >> sanitize_task >> export_data_to_features_task
