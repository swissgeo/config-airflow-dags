import logging

from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import DAG
from airflow.sdk.definitions.param import Param, ParamsDict
from toolset.file.download_from_s3 import download_from_s3
from toolset.tabular.converter import lowercase_column_names
from toolset.tabular.parser import parse_csv
from toolset.tabular.writer import write_to_s3tables

logger = logging.getLogger("pipeline_example")

# Define default arguments for the DAG
default_args = {"owner": "airflow", "depends_on_past": False, "retries": 0}

# Create the DAG
dag = DAG(
    "three_step_pipeline",
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
    file_path = download_from_s3(file_key, "landing_zone")

    table = parse_csv(file_path, "utf-8", ",")

    table_lowercased = lowercase_column_names(table)

    write_to_s3tables(table_lowercased, "raw", "example", "data")


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
