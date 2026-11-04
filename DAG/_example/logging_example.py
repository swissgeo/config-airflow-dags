# LOGGING EXAMPLE
#
# Simple DAG used to test logging. One task runs first, followed by two tasks in parallel.
# Every task emits a debug, info and error log message.
import logging

from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import DAG

logger = logging.getLogger(__name__)

default_args = {"owner": "airflow", "depends_on_past": False, "retries": 0}

dag = DAG(
    "logging_example",
    default_args=default_args,
    description="A simple DAG to test logging",
    schedule=None,
    catchup=False,
)


def log_messages(task_name: str) -> None:
    logger.debug("Debug message from %s", task_name)
    logger.info("Info message from %s", task_name)
    logger.error("Error message from %s", task_name)


first_task = PythonOperator(
    task_id="first_task",
    python_callable=log_messages,
    op_kwargs={"task_name": "first_task"},
    dag=dag,
)

parallel_task_a = PythonOperator(
    task_id="parallel_task_a",
    python_callable=log_messages,
    op_kwargs={"task_name": "parallel_task_a"},
    dag=dag,
)

parallel_task_b = PythonOperator(
    task_id="parallel_task_b",
    python_callable=log_messages,
    op_kwargs={"task_name": "parallel_task_b"},
    dag=dag,
)

first_task >> [parallel_task_a, parallel_task_b]
