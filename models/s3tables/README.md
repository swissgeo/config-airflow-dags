# s3tables Models

Here we store the model definitions for the s3tables used by the DAGs for
storing processed data.

The model definitions are written in a JSON schema that can be consumed by
the AWS cli directly (see `aws s3tables  create-table --generate-cli-skeleton`)

The main information in the model definition is the schema definition.

## Basic Model

Following is a truncated example schema for a table to be created in s3tables
with some explanation:

```json
{
  "tableBucketARN": "$RAW_TABLE_BUCKET_ARN", # this value will be substituted by script
  "namespace": "org_meteoschweiz", # the namespace. Currently created in terraform
  "name": "local_forecast_tre200px", # The tablename
  "format": "ICEBERG",
  "metadata": {
    "iceberg": {
      "schema": {
        "fields": [
          {
            "id": 1, # This is an identifier that's used for referencing the same field across various versions
            "name": "point_id",
            "type": "int", # A list of possible types can be found here:  https://iceberg.apache.org/spec/#primitive-types
            "required": true
          },
        ]
      }
    }
  }
}
```

## How to use this

In order to update the models in s3tables, you can run following script while prepending
it with summon:

```sh
summon -p ssm -f secrets.yaml -e dev make upgrade-check # Lists the diff
summon -p ssm -f secrets.yaml -e dev make upgrade-tables # Actually creates tables
```

Substitute "env" with the desired environment.

> [!WARNING]
> These commands _do not_ track the s3tables' state. This means, removing a file
> won't result in removing the table!

### Updating schema caveats

It is impossible to update the schema of an existing table in s3tables with CLI tools.
Apparently this should be [done with Athena](https://repost.aws/questions/QUfRzL_JarRTeEXeweOWODxQ/s3-tables-schema-evolution-and-data-loss)
As this process isn't entirely clear from a business requirement perspective, we don't concern
ourselves with this yet.

### Deleting existing tables

Tables cannot be delete with the AWS console but instead have to be deleted via AWS CLI like so:

```sh
PROFILE=swisstopo-swissgeo-dev
BUCKET_ARN=arn:aws:s3tables:eu-central-1:321652032171:bucket/data-ingest-load-dev-swissgeo
NAMESPACE=org_meteoschweiz
TABLE_NAME=local_forecast_tre200px

aws s3tables delete-table --table-bucket-arn $BUCKET_ARN --namespace $NAMESPACE --name $TABLE_NAME --profile $PROFILE
```
