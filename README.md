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

## Configuration

Following are the env variables that are required to be set:

| variable                  | Type               | scope                    | description                                                                                  |
| ------------------------- | ------------------ | ------------------------ | -------------------------------------------------------------------------------------------- |
| ICEBERG_BACKEND           | local \| s3tables  | global                   | Whether to use the local setup or s3tables                                                   |
| ICEBERG_URI               | URL                | testing setup            | The URL to iceberg. _local only_                                                             |
| AWS_ACCESS_KEY_ID         | string             | testing setup            | Key for accessing the local iceberg instance                                                 |
| AWS_SECRET_ACCESS_KEY     | string             | testing setup            | Access key for the local iceberg instance                                                    |
| AWS_ENDPOINT_URL          | URL                | testing setup            | URL to the local moto server for testing                                                     |
| AWS_REGION                | aws region(string) | global                   | The region this code is running in. Used by the test setup as well as the s3 file downloader |
| RAW_TABLE_BUCKET_ARN      | ARN (string)       | s3tables reading/writing | ARN to the s3table bucket for raw data                                                       |
| SANITIZE_TABLE_BUCKET_ARN | ARN (string)       | s3tables reading/writing | ARN to the s3table bucket for sanitize data                                                  |
| LOAD_TABLE_BUCKET_ARN     | ARN (string)       | s3tables reading/writing | ARN to the s3table bucket for load data                                                      |
| LANDING_ZONE_BUCKET       | string             | file downloader          | Name of the s3table bucket for landing zone data                                             |
| FEATURES_DB_ENDPOINT      | string             | postgres db writer       | URL to the service-oa-features database                                                      |
| FEATURES_DB_PORT          | int                | postgres db writer       | Port to the service-oa-features database                                                     |
| FEATURES_DB_NAME          | string             | postgres db writer       | Name of the service-oa-features database                                                     |
| FEATURES_DB_USER          | string             | postgres db writer       | Username for the service-oa-features database                                                |
| FEATURES_DB_PASSWORD      | string             | postgres db writer       | Password for the service-oa-features database                                                |
| FEATURES_DB_SSL_REQUIRED  | boolean            | postgres db writer       | Whether SSL is required for the service-oa-features database                                 |
