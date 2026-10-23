# Airflow DAG Configuration

Configuration and code to process data on Airflow

| Branch  | Status                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| develop | ![Build Status](https://codebuild.eu-central-1.amazonaws.com/badges?uuid=eyJlbmNyeXB0ZWREYXRhIjoicFU1SDFEbTZPMnc3SVVWM0k0NTZXZzE2blpDMFZHNXQvZ2tWcmRoNjNrb2RWWmxIcmVWazQxUVdKa3RPUUpNUEhNVlF3QkJqOUlDZHBickhvTnRaUXR3PSIsIml2UGFyYW1ldGVyU3BlYyI6ImdCZllZL2o0TXJZVkJYbk0iLCJtYXRlcmlhbFNldFNlcmlhbCI6MX0%3D&branch=develop) [![codecov](https://codecov.io/gh/swissgeo/config-airflow-dags/branch/develop/graph/badge.svg)](https://codecov.io/github/swissgeo/config-airflow-dags/tree/develop) |
| main    | ![Build Status](https://codebuild.eu-central-1.amazonaws.com/badges?uuid=eyJlbmNyeXB0ZWREYXRhIjoicFU1SDFEbTZPMnc3SVVWM0k0NTZXZzE2blpDMFZHNXQvZ2tWcmRoNjNrb2RWWmxIcmVWazQxUVdKa3RPUUpNUEhNVlF3QkJqOUlDZHBickhvTnRaUXR3PSIsIml2UGFyYW1ldGVyU3BlYyI6ImdCZllZL2o0TXJZVkJYbk0iLCJtYXRlcmlhbFNldFNlcmlhbCI6MX0%3D&branch=main) [![codecov](https://codecov.io/gh/swissgeo/config-airflow-dags/branch/main/graph/badge.svg)](https://app.codecov.io/gh/swissgeo/config-airflow-dags/tree/main)          |

## Intro

This repository contains the necessary code, configuration and tooling for running pipeline jobs in airflow.
This means, for now:

- The tooling to create the init container that will be used in Airflow to read DAGs and execute the workers
- The code that the DAG executes
- The DAG definition themselves
- The model information that's used for creating the tables on s3tables as well as on the postgis database for [service-oa-features](https://github.com/swissgeo/service-oa-features)

## Setup

### Configuration

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

## Docker Image

### Building

The content of this repo is packaged into a busybox Docker image. The container will then be used as an init-container, which will then copy it's
content to a mounted folder, which will be read by the processor and triggerer.

To create the docker container by hand, run the following commands:

```sh
make dockerbuild
make dockerlogin
make dockerpush # push to the ECR registry
```

### Airflow configuration

The airflow distribution needs to use following additional configuration for it to work (values.yaml of the helm chart):

```yaml
dagProcessor:
  # [..]
  env:
    - name: PYTHONPATH
      value: /opt/airflow/dags/python
  extraVolumes:
    - name: dags
      emptyDir: {}
    - name: tmp
      emptyDir: {}
  extraVolumeMounts:
    - name: dags
      mountPath: /opt/airflow/dags
      readOnly: true
    - name: tmp
      mountPath: /tmp
  extraInitContainers:
    - name: dag-init
      securityContext:
        allowPrivilegeEscalation: false
        capabilities:
          drop: ["ALL"]
        readOnlyRootFilesystem: true
      command:
        ["sh", "-c", "cp -r /opt/airflow/dags-staging/. /opt/airflow/dags/"]
      volumeMounts:
        - name: dags
          mountPath: /opt/airflow/dags
        - name: tmp
          mountPath: /tmp

workers:
  kubernetes:
    # same as above

triggerer:
  # same as above
```
