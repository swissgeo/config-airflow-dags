# service-oa-features

## About

This is the setup for provisioning the tables in the postgres database for service-oa-features.

### `./models/`

Here we store the model definitions for every table that is supposed to be created in service-oa-features.
The models are supposed to be segmented by <provider_name>/<dataset>, e.g. `ch_meteoschweiz/local_forecast`.
Once a new model is added, it needs to be imported by `models/__init__.py`

### `./migrations`

Here alembic will store the db migrations created by `make db-revision`.

## How to use this

### Create a new revision

Once a new model has been created or an existing model has been updated, run

`make db-revision`

This will create a new migrations file.

`make db-upgrade`

Upgrades the local docker container DB to the newest revision.

> [!NOTE]
> Make sure the docker container is running
