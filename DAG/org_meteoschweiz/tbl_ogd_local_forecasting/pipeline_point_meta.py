import logging

from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import DAG
from airflow.sdk.definitions.param import Param, ParamsDict

from swissgeo_toolset.airflow.operators.csv_from_landingzone_to_raw import (
    CsvFromLandingzoneToRawOperator,
)
from swissgeo_toolset.tabular.converter import (
    add_geometry_column,
    convert_column,
    drop_columns,
)
from swissgeo_toolset.tabular.reader import read_from_s3tables
from swissgeo_toolset.tabular.writer import write_to_postgres, write_to_s3tables

NAMESPACE = "ch_meteoschweiz"

logger = logging.getLogger(__name__)

default_args = {"owner": "airflow", "depends_on_past": False, "retries": 0}

csv_encoding_default = "latin-1"
csv_delimiter_default = ";"
csv_quote_char_default = '"'

dag = DAG(
    "ch_meteoschweiz-local_forecast-points",
    default_args=default_args,
    description="Local Forecast Point Pipeline",
    schedule=None,
    catchup=False,
    params=ParamsDict(
        {
            "file_key": Param(type="string", default=""),
            "csv_encoding": Param(type="string", default=csv_encoding_default),
            "csv_delimiter": Param(type="string", default=csv_delimiter_default),
            "csv_quote_char": Param(type="string", default=csv_quote_char_default),
        }
    ),
)


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
    sanitized_data = read_from_s3tables("sanitize", NAMESPACE, "local_forecast_points")

    with_geometry = add_geometry_column(
        sanitized_data,
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


download_and_store_raw_task = CsvFromLandingzoneToRawOperator(
    task_id="download_and_store_raw_task",
    name="download_and_store_raw_task",
    file_key="{{ params.file_key }}",
    encoding="{{ params.csv_encoding }}",
    delimiter="{{ params.csv_delimiter }}",
    quote_char="{{ params.csv_quote_char }}",
    namespace=NAMESPACE,
    table_name="local_forecast_points",
    dag=dag,
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


download_and_store_raw_task >> sanitize_task >> export_data_to_features_task
