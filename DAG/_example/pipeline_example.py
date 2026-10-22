# PIPELINE EXAMPLE
#
# This example DAG is used to develop the boilerplate for the integration testing and could also
# be useful as an example for future DAG implementations
import logging

from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import DAG
from airflow.sdk.definitions.param import Param, ParamsDict

from toolset.file.download_from_s3 import download_from_landingzone
from toolset.tabular.converter import lowercase_column_names
from toolset.tabular.parser import parse_csv
from toolset.tabular.writer import write_to_s3tables

logger = logging.getLogger(__name__)

# Define default arguments for the DAG
default_args = {"owner": "airflow", "depends_on_past": False, "retries": 0}

namespace = "example"

dag = DAG(
    "pipeline_example",
    default_args=default_args,
    description="A pipeline just to have an example to test with",
    schedule=None,
    catchup=False,
    params=ParamsDict(
        {
            "file_key": Param(type="string", default=""),
        }
    ),
)


def first_step(file_key: str) -> None:
    with download_from_landingzone(file_key) as file_path:
        table = parse_csv(file_path, "utf-8", ",")

    table_lowercased = lowercase_column_names(table)

    write_to_s3tables(table_lowercased, "raw", namespace, "data")


# Define tasks
first_step_task = PythonOperator(
    task_id="first_step_task",
    python_callable=first_step,
    dag=dag,
    op_kwargs={
        "file_key": "{{ params.file_key }}",
    },
)

# Set dependencies between steps
first_step_task
