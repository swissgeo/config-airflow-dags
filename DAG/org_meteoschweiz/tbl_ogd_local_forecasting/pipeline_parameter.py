import logging

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
    s3tables_table_name: str, postgres_table_name: str, parameter_name: str
) -> None:  # noqa: ARG001
    point_data = read_from_s3tables("load", NAMESPACE, "tbl_ogd_local_forecasting_point_meta")
    sanitize_data = read_from_s3tables("sanitize", NAMESPACE, s3tables_table_name)

    if len(point_data) == 0 or len(sanitize_data) == 0:
        raise MissingPointMetaDataError("Point Meta Data is missing")

    joined_data = join_tables(sanitize_data, point_data, ["point_id", "point_type_id"], "inner")

    def feature_id_callback(row: dict) -> str:
        datetime = row["datetime"].strftime("%Y%m%d%H%M")
        return f"{row['point_id']}.{row['point_type_id']}.tre200px.{datetime}"

    with_feature_id = add_column(joined_data, "feature_id", "string", feature_id_callback)

    parameter_meta = with_feature_id
    for key, value in tre200px_parameter_data.items():
        parameter_meta = add_column(parameter_meta, key, "string", lambda _: value)

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
<<<<<<< HEAD
<<<<<<< HEAD
        "table_name": "local_forecasting_{{params.parameter_name}}",
||||||| parent of 176c5ab (fixup! GPS-1007: Implement parameter pipeline for meteoschweiz)
        "table_name": "tbl_ogd_local_forecasting_{{params.parameter_name}}",
=======
        "s3tables_table_name": "tbl_ogd_local_forecasting_{{params.parameter_name}}",
>>>>>>> 176c5ab (fixup! GPS-1007: Implement parameter pipeline for meteoschweiz)
||||||| parent of 245ebc9 (GPS-1007: Properly name the forecasting point tables in s3)
        "table_name": "local_forecasting_{{params.parameter_name}}",
=======
        "table_name": "tbl_ogd_local_forecasting_{{params.parameter_name}}",
>>>>>>> 245ebc9 (GPS-1007: Properly name the forecasting point tables in s3)
        "parameter_name": "{{params.parameter_name}}",
        "postgres_table_name": "tbl_ogd-local-forecasting-{{params.parameter_name}}",
    },
)


download_and_store_raw_task >> sanitize_data_task >> combine_and_export_data_task


tre200px_parameter_data = {
    "parameter_shortname": "tre200px",
    "parameter_description_de": "Lufttemperatur 2 m über Boden; Tagesmaximum 00:00 - 24:00 Lokalzeit",
    "parameter_description_fr": "Température de l'air à 2 m du sol; maximum journalier 00:00 - 24:00 heure locale",
    "parameter_description_it": "Temperatura dell'aria a 2 m dal suolo; massima giornaliera 00:00 - 24:00 ora locale",
    "parameter_description_en": "Air temperature 2 m above ground; daily maximum 00:00 - 24:00 local time",
    "parameter_group_de": "Temperatur",
    "parameter_group_fr": "Température",
    "parameter_group_it": "Temperatura",
    "parameter_group_en": "Temperature",
    "parameter_granularity": "D",
    "parameter_decimals": "1",
    "parameter_datatype": "Float",
    "parameter_unit": "°C",
}
