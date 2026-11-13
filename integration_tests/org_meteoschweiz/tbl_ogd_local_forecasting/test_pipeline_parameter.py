import csv
import datetime as dt
from pathlib import Path

import pyarrow as pa
import pytest
from _pytest.monkeypatch import MonkeyPatch
from faker import Faker
from psycopg.rows import dict_row
from pyiceberg.catalog import Catalog
from types_boto3_s3 import S3Client

from DAG.org_meteoschweiz.tbl_ogd_local_forecasting import pipeline_parameter


class TestParameterPipeline:
    """Encapsulating tests in a class so that certain fixtures are stable across the tests
    and we can depend one test on another. This simulates the real life situation, where one
    task is dependent on the other

    We're testing the parameter pipeline fix with the tre200px parameter

    THESE TESTS ARE MEANT TO BE RUN TOGETHER IN ORDER
    """

    def test_download_and_parse_points_csv(
        self,
        raw_catalog: Catalog,
        s3tables_table_raw,
        s3tables_namespace,
        landing_zone: tuple[S3Client, str],
        monkeypatch: MonkeyPatch,
    ):
        s3, bucket_name = landing_zone

        table_name = s3tables_table_raw(
            "org_meteoschweiz/tbl_ogd_local_forecasting/raw/tre200px.json"
        )

        monkeypatch.setattr(pipeline_parameter, "NAMESPACE", s3tables_namespace)
        monkeypatch.setenv("LANDING_ZONE_BUCKET", bucket_name)

        with (Path(__file__).resolve().parent / "fixtures/tre200px.csv").open(
            encoding="latin-1"
        ) as f:
            s3.put_object(
                Bucket=bucket_name,
                Key="data.csv",
                Body=f.read(),
            )

        task = pipeline_parameter.download_and_store_raw_task
        monkeypatch.setattr(task, "encoding", pipeline_parameter.csv_encoding_default)
        monkeypatch.setattr(task, "delimiter", pipeline_parameter.csv_delimiter_default)
        monkeypatch.setattr(task, "quote_char", pipeline_parameter.csv_quote_char_default)
        monkeypatch.setattr(task, "namespace", s3tables_namespace)
        monkeypatch.setattr(task, "file_key", "data.csv")
        monkeypatch.setattr(task, "table_name", table_name)

        task.execute(context={})

        identifier = f"{s3tables_namespace}.{table_name}"
        table = raw_catalog.load_table(identifier)
        result_data = table.scan().to_arrow().to_pylist()

        # there are multiple entries with the same point_id for different dates. This reflects
        # the real life setup. However, this means that this query will also return multiple entries
        # per point_id. The last entry wins, we're testing against that
        test_rows = {
            row["point_id"]: row for row in result_data if row["point_id"] in {1, 613000, 501}
        }

        assert test_rows[1]["point_id"] == 1
        assert test_rows[1]["point_type_id"] == 1
        assert test_rows[1]["date"] == "202609010000"
        assert pytest.approx(test_rows[1]["tre200px"]) == 14.4

        assert test_rows[613000]["point_id"] == 613000
        assert test_rows[613000]["point_type_id"] == 2
        assert test_rows[613000]["date"] == "202609010000"
        assert pytest.approx(test_rows[613000]["tre200px"]) == 21.4

        assert test_rows[501]["point_id"] == 501
        assert test_rows[501]["point_type_id"] == 3
        assert test_rows[501]["date"] == "202609010000"
        assert pytest.approx(test_rows[501]["tre200px"]) == 7.3

    def test_sanitize_data(
        self,
        sanitize_catalog: Catalog,
        s3tables_table_sanitize,
        s3tables_namespace,
        monkeypatch: MonkeyPatch,
    ):
        sanitize_table_name = s3tables_table_sanitize(
            "org_meteoschweiz/tbl_ogd_local_forecasting/sanitize/tre200px.json"
        )

        monkeypatch.setattr(pipeline_parameter, "NAMESPACE", s3tables_namespace)

        pipeline_parameter.sanitize_data(sanitize_table_name, "tre200px")

        identifier = f"{s3tables_namespace}.{sanitize_table_name}"
        table = sanitize_catalog.load_table(identifier)
        result_data = table.scan().to_arrow().to_pylist()

        # there are multiple entries with the same point_id for different dates. This reflects
        # the real life setup. However, this means that this query will also return multiple entries
        # per point_id. The last entry wins, we're testing against that
        test_rows = {
            row["point_id"]: row for row in result_data if row["point_id"] in {1, 613000, 501}
        }

        assert test_rows[1]["point_id"] == 1
        assert test_rows[1]["point_type_id"] == 1
        assert test_rows[1]["datetime"] == dt.datetime(2026, 9, 1, 0, 0, tzinfo=dt.UTC)
        assert pytest.approx(test_rows[1]["value"]) == 14.4

        assert test_rows[613000]["point_id"] == 613000
        assert test_rows[613000]["point_type_id"] == 2
        assert test_rows[613000]["datetime"] == dt.datetime(2026, 9, 1, 0, 0, tzinfo=dt.UTC)

        assert pytest.approx(test_rows[613000]["value"]) == 21.4

        assert test_rows[501]["point_id"] == 501
        assert test_rows[501]["point_type_id"] == 3
        assert test_rows[501]["datetime"] == dt.datetime(2026, 9, 1, 0, 0, tzinfo=dt.UTC)
        assert pytest.approx(test_rows[501]["value"]) == 7.3

    def test_combine_and_export_data(  # noqa: PLR0912, PLR0915, PLR0917
        self,
        load_catalog: Catalog,
        s3tables_table_load,
        s3tables_namespace,
        features_database,
        monkeypatch: MonkeyPatch,
        faker: Faker,
    ):
        """
        Testing the combining of point data with parameter data and exporting to
        postgres

        Since we don't have any point data in this test, we generate it manually with
        faker input.
        At first, we also check the behavior when no point data is available.
        """
        point_table_name = s3tables_table_load(
            "org_meteoschweiz/tbl_ogd_local_forecasting/load/points.json"
        )

        load_table_name = s3tables_table_load(
            "org_meteoschweiz/tbl_ogd_local_forecasting/load/tre200px.json"
        )

        monkeypatch.setattr(
            pipeline_parameter,
            "fetch_parameter_data",
            _fake_parameter_data,
        )
        monkeypatch.setattr(pipeline_parameter, "NAMESPACE", s3tables_namespace)

        # run the task without point data
        with pytest.raises(pipeline_parameter.MissingPointMetaDataError):
            # no point data available, we want to error this case
            pipeline_parameter.combine_and_export_data(
                load_table_name,
                "tbl_ogd-local-forecasting-tre200px",
                "tre200px",
                "irrelevant_since_monkepatched",
            )

        point_data = _generate_fake_point_data(
            s3tables_namespace, point_table_name, faker, load_catalog
        )

        # run the task
        pipeline_parameter.combine_and_export_data(
            load_table_name,
            "tbl_ogd-local-forecasting-tre200px",
            "tre200px",
            "irrelevant_since_monkepatched",
        )

        # asserting that the data is corret in iceberg
        identifier = f"{s3tables_namespace}.{load_table_name}"
        table = load_catalog.load_table(identifier)
        result_data = table.scan().to_arrow().to_pylist()

        # there are multiple entries with the same point_id for different dates. This reflects
        # the real life setup. However, this means that this query will also return multiple entries
        # per point_id. The last entry wins, we're testing against that
        test_rows = {
            row["point_id"]: row for row in result_data if row["point_id"] in {1, 613000, 501}
        }

        assert test_rows[1]["datetime"] == dt.datetime(2026, 9, 1, 0, 0, tzinfo=dt.UTC)
        assert test_rows[1]["feature_id"] == "1.1.tre200px.202609010000"
        assert pytest.approx(test_rows[1]["value"]) == 14.4

        for key in point_data["1_1"]:
            if key == "point_height_masl":
                assert pytest.approx(test_rows[1][key]) == point_data["1_1"][key]
            else:
                assert test_rows[1][key] == point_data["1_1"][key]

        assert pytest.approx(test_rows[1]["value"]) == 14.4

        assert test_rows[613000]["datetime"] == dt.datetime(2026, 9, 1, 0, 0, tzinfo=dt.UTC)
        assert test_rows[613000]["feature_id"] == "613000.2.tre200px.202609010000"
        assert pytest.approx(test_rows[613000]["value"]) == 21.4

        for key in point_data["613000_2"]:
            if key == "point_height_masl":
                assert pytest.approx(test_rows[613000][key]) == point_data["613000_2"][key]
            else:
                assert test_rows[613000][key] == point_data["613000_2"][key]

        assert test_rows[501]["datetime"] == dt.datetime(2026, 9, 1, 0, 0, tzinfo=dt.UTC)
        assert test_rows[501]["feature_id"] == "501.3.tre200px.202609010000"
        assert pytest.approx(test_rows[501]["value"]) == 7.3

        for key in point_data["501_3"]:
            if key == "point_height_masl":
                assert pytest.approx(test_rows[501][key]) == point_data["501_3"][key]
            else:
                assert test_rows[501][key] == point_data["501_3"][key]

        assert test_rows[501]["parameter_shortname"] == "tre200px"
        assert (
            test_rows[501]["parameter_description_de"]
            == "Lufttemperatur 2 m über Boden; Tagesmaximum 00:00 - 24:00 Lokalzeit"
        )
        assert test_rows[501]["parameter_group_de"] == "Temperatur"
        assert test_rows[501]["parameter_granularity"] == "D"
        assert test_rows[501]["parameter_decimals"] == 1
        assert test_rows[501]["parameter_datatype"] == "Float"
        assert test_rows[501]["parameter_unit"] == "°C"

        # asserting that the data is correct in the database
        with features_database.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                       SELECT
                           *,
                           ST_asText(geometry) as geometry
                       FROM "tbl_ogd-local-forecasting-tre200px"
                       WHERE point_id IN (501)
                   """)
            rows = cur.fetchall()

        test_row = rows[-1]
        assert {
            "point_id": 501,
            "point_type_id": 3,
            "datetime": dt.datetime(2026, 9, 1, 0, 0, tzinfo=dt.UTC),
            "feature_id": "501.3.tre200px.202609010000",
            "value": 7.3,
        }.items() <= test_row.items()

        for key in point_data["501_3"]:
            if key == "point_height_masl":
                assert pytest.approx(test_rows[501][key]) == point_data["501_3"][key]
            else:
                assert test_rows[501][key] == point_data["501_3"][key]

        for key in _fake_parameter_data(None, None):
            assert test_rows[501][key] == point_data["501_3"][key]


def _generate_fake_point_data(
    s3tables_namespace, point_table_name, faker, load_catalog
) -> dict[str, dict]:
    """
    Generate fake point data

    Since this task in the DAG combines the point data to the parameter data, we need to
    have the point data available before the test/task is running.
    Therefore we're generating some point data in here that will be used in this test
    """
    with (Path(__file__).resolve().parent / "fixtures/tre200px.csv").open(encoding="latin-1") as f:
        # we read the fixture file for all the point_id/point_type_id combinations
        # then we generate the fake data exactly for those
        point = [
            faker.pyfloat(min_value=2480000, max_value=2847500, right_digits=2),
            faker.pyfloat(min_value=1074000, max_value=1302000, right_digits=2),
        ]
        point_data = {
            f"{row['point_id']}_{row['point_type_id']}": {
                "point_id": int(row["point_id"]),
                "point_type_id": int(row["point_type_id"]),
                "station_abbr": faker.lexify("???").upper(),
                "postal_code": faker.random_int(1000, 9999),
                "point_name": faker.city(),
                "point_type_de": faker.word(),
                "point_type_fr": faker.word(),
                "point_type_it": faker.word(),
                "point_type_en": faker.word(),
                "point_height_masl": faker.pyfloat(min_value=190, max_value=4634, right_digits=1),
                "geometry": (f"POINT({point[0]} {point[1]})"),
            }
            for row in csv.DictReader(f, delimiter=";")
        }

        point_dataframe = pa.Table.from_pylist(list(point_data.values()))

    point_table = load_catalog.load_table((s3tables_namespace, point_table_name))

    point_table_schema = point_table.schema().as_arrow()
    point_dataframe = point_dataframe.select(point_table_schema.names).cast(point_table_schema)

    point_table.overwrite(point_dataframe)

    return point_data


def _fake_parameter_data(_, __) -> dict:
    return {
        "parameter_shortname": "tre200px",
        "parameter_description_de": "Lufttemperatur 2 m über Boden; Tagesmaximum 00:00 - 24:00",
        "parameter_description_fr": "Température de l'air à 2 m du sol; maximum journalier",
        "parameter_description_it": "Temperatura dell'aria a 2 m dal suolo; massima giornaliera",
        "parameter_description_en": "Air temperature 2 m above ground; daily maximum 00:00 ",
        "parameter_group_de": "Temperatur",
        "parameter_group_fr": "Température",
        "parameter_group_it": "Temperatura",
        "parameter_group_en": "Temperature",
        "parameter_granularity": "D",
        "parameter_decimals": "1",
        "parameter_datatype": "Float",
        "parameter_unit": "°C",
    }
