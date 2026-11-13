import csv
import io
import logging

import pyarrow as pa
import pyarrow.compute as pc
import requests
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import DAG
from airflow.sdk.definitions.param import Param, ParamsDict

from swissgeo_toolset.airflow.operators.csv_from_landingzone_to_raw import (
    CsvFromLandingzoneToRawOperator,
)
from swissgeo_toolset.tabular.converter import (
    add_column,
    convert_column,
    join_tables,
    rename_column,
)
from swissgeo_toolset.tabular.reader import read_from_s3tables
from swissgeo_toolset.tabular.writer import write_to_postgres, write_to_s3tables

NAMESPACE = "org_meteoschweiz"

logger = logging.getLogger(__name__)

default_args = {"owner": "airflow", "depends_on_past": False, "retries": 0}

csv_encoding_default = "latin-1"
csv_delimiter_default = ";"
csv_quote_char_default = '"'

dag = DAG(
    "tbl_ogd-local-forecasting-parameter-data",
    default_args=default_args,
    description="Local Forecast Parameter Pipeline (Parametrizable)",
    schedule=None,
    catchup=False,
    params=ParamsDict(
        {
            "file_key": Param(type="string", default=""),
            "parameter_name": Param(type="string"),
            "csv_encoding": Param(type="string", default=csv_encoding_default),
            "csv_delimiter": Param(type="string", default=csv_delimiter_default),
            "csv_quote_char": Param(type="string", default=csv_quote_char_default),
            "parameter_meta_url": Param(
                type="string",
                default="https://data.geo.admin.ch/ch.meteoschweiz.ogd-local-forecasting/ogd-local-forecasting_meta_parameters.csv",
            ),
        }
    ),
)


class MissingPointMetaDataError(Exception):
    pass


def sanitize_data(table_name: str, parameter_name: str) -> None:
    """
    Parsing the date from a string to a proper datetime and renaming some columns
    """
    raw_data = read_from_s3tables("raw", NAMESPACE, table_name)

    datetimed = convert_column(raw_data, "date", "strptime", {"format": "%Y%m%d%H%M", "unit": "s"})

    # renaming this because it's actually a datetime, not just date
    datetime_renamed = rename_column(datetimed, "date", "datetime")

    # we want to uniformly call this column "value"
    value_renamed = rename_column(datetime_renamed, parameter_name, "value")

    write_to_s3tables(value_renamed, "sanitize", NAMESPACE, table_name)


def combine_and_export_data(
    s3tables_table_name: str, postgres_table_name: str, parameter_name: str, parameter_meta_url: str
) -> None:
    """Combine and export data


    Combine the parameter data with the point data (if it exists) from the corresponding load table.
    Enrich the rows with the parameter meta data that is fetched from service-stac.
    Export it to postgres' service-oa-features
    """
    point_data = read_from_s3tables("load", NAMESPACE, "tbl_ogd_local_forecasting_point_meta")
    sanitize_data = read_from_s3tables("sanitize", NAMESPACE, s3tables_table_name)

    if len(point_data) == 0 or len(sanitize_data) == 0:
        raise MissingPointMetaDataError("Point Meta Data is missing")

    joined_data = join_tables(sanitize_data, point_data, ["point_id", "point_type_id"], "inner")

    with_feature_id = add_column(
        joined_data,
        "feature_id",
        "string",
        value_callback=lambda t: pc.binary_join_element_wise(  # ty: ignore[unresolved-attribute]
            pc.cast(t["point_id"], pa.string()),
            pc.cast(t["point_type_id"], pa.string()),
            parameter_name,
            pc.strftime(t["datetime"], format="%Y%m%d%H%M"),  # ty: ignore[unresolved-attribute]
            ".",
        ),
    )

    parameter_meta = with_feature_id

    for key, value in fetch_parameter_data(parameter_meta_url, parameter_name).items():
        parameter_meta = add_column(parameter_meta, key, "string", static_value=value)

    write_to_s3tables(parameter_meta, "load", NAMESPACE, s3tables_table_name)

    write_to_postgres(parameter_meta, postgres_table_name)


download_and_store_raw_task = CsvFromLandingzoneToRawOperator(
    task_id="download_and_store_raw_task",
    name="download_and_store_raw_task",
    file_key="{{ params.file_key }}",
    encoding="{{ params.csv_encoding }}",
    delimiter="{{ params.csv_delimiter }}",
    quote_char="{{ params.csv_quote_char }}",
    namespace=NAMESPACE,
    table_name="tbl_ogd_local_forecasting_{{params.parameter_name}}",
    dag=dag,
)

sanitize_data_task = PythonOperator(
    task_id="sanitize_data_task",
    python_callable=sanitize_data,
    dag=dag,
    op_kwargs={
        "table_name": "tbl_ogd_local_forecasting_{{params.parameter_name}}",
        "parameter_name": "{{params.parameter_name}}",
    },
)

combine_and_export_data_task = PythonOperator(
    task_id="combine_and_export_data_task",
    python_callable=combine_and_export_data,
    dag=dag,
    op_kwargs={
        "s3tables_table_name": "tbl_ogd_local_forecasting_{{params.parameter_name}}",
        "parameter_name": "{{params.parameter_name}}",
        "postgres_table_name": "tbl_ogd-local-forecasting-{{params.parameter_name}}",
        "parameter_meta_url": "{{params.parameter_meta_url}}",
    },
)


download_and_store_raw_task >> sanitize_data_task >> combine_and_export_data_task


def fetch_parameter_data(url: str, parameter: str) -> dict:
    """Fetching parameter data from service-stac"""

    logger.info("Fetching parameter data from %s", url)
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    reader = csv.DictReader(
        io.StringIO(response.content.decode(csv_encoding_default)),
        delimiter=csv_delimiter_default,
        quotechar=csv_quote_char_default,
    )

    for row in reader:
        if row["parameter_shortname"] == parameter:
            return row

    raise ValueError(f"Parameter '{parameter}' not found in {url}")
