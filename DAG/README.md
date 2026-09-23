# DAG

Here are the directected acyclic graphs "DAG"s are stored.

These DAGs are specific to airflow. They are to be parsed by the Airflow instance and provided through the API and UI.

## Directory structure

The DAGs are split up into subdirectories based on the dataset provider and the dataset, e.g. `ch.bfe/erneuerbarheizen/`.

DAGs that cover more general uses cases are to be stored in `_general/`.
