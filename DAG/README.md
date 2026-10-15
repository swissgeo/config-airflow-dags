# DAG

Here are the directected acyclic graphs "DAG"s are stored.

These DAGs are specific to airflow. They are to be parsed by the Airflow instance and provided through the API and UI.

## Directory structure

The DAGs are split up into subdirectories based on the dataset provider and the dataset, e.g. `ch.bfe/erneuerbarheizen/`.

DAGs that cover more general uses cases are to be stored in `_general/`.

## Basic DAG model

In general, a DAG consist of two or three steps:

- a "raw" step
- a "sanitize" step
- an optional "load" step

The `raw` and `sanitize` steps are supposed to write their result to an s3table. The `load` step _can_ potentially also dump the data to an s3tables. We're generally undecided whether we'll want/keep this.

## Raw Step

This step downloads the data from the landing zone, converts it to tabular data _(for now we only support tabular data)_ and dumps it more or less as-is to an s3tables "raw".

## Sanitize Step

This step loads the raw data from the previous step and sanitizes it.
Sanitization can include datatype conversion (for example string -> date), column renaming, column cleansing, validation etc.

The sanitize step preparse the data as close as possible to what's needed in the end to be published to an output channel.

## Load Step

This step finally loads the data to an output channel. For now this means writing it into the database of `service-oa-features`.

This step reads the data from the sanitize step. It can potentially even read multiple s3tables and merge them into a single output.

This step _can_ also dump the result intermediarily to an s3tables - we're not yet decided on that.

Sometimes the load step is omitted; in some cases the sanitize table is the final result for a single data package. Examples are when another pipeline combines multiple sanitized data packages.
