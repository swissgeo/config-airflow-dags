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

### Using it for actual databases

The `-prod` Make targets run Alembic operations against a remote database in AWS.
Currently, we apply database migrations manually from this repository.

To run `-prod` targets (like `make db-upgrade-prod`), first open a port forwarding to the database
and leave it running:

```bash
summon -p ssm -f secrets.yml -e services-dev make port-forwarding
```

Now in another terminal you can call the alembic operations:

```bash
summon -p ssm -f secrets.yml -e services-dev make db-upgrade-prod
```

This will read and populate the environment from `secrets.yml` (you need to be logged in to
AWS SSO for this to work).

If you want to apply it for int or prod, simply replace the `services-dev` argument accordingly in both commands.

> [!NOTE]
> You may have to adjust `K8SCONTEXT` in `secret.yml` as we have `swissgeo/prod-green` and `swissgeo/prod-blue`
> in the production environment.
