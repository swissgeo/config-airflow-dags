# Airflow DAG Configuration

Configuration and code to process data on Airflow

<!--| Branch | Status |
|--------|-----------|
| develop | ![Build Status](CODEBUILD_BADGE_URL) |
| main | ![Build Status](CODEBUILD_BADGE_URL) |-->

## Intro

This repository contains the necessary code, configuration and tooling for running pipeline jobs in airflow.
This means, for now:

- The tooling to create the init container that will be used in Airflow to read DAGs and execute the workers
- The code that the DAG executes
- The DAG definition themselves
- The model information that's used for creating the tables on s3tables as well as on the postgis database for [service-oa-features](https://github.com/swissgeo/service-oa-features)
