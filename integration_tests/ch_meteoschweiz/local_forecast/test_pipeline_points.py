from pathlib import Path

from psycopg.rows import dict_row

from DAG.ch_meteoschweiz.local_forecast import pipeline_points


class TestPointPipeline:
    """Encapsulating tests in a class so that certain fixtures are stable across the tests
    and we can depend one test on another. This simulates the real life situation, where one
    task is dependent on the other

    THESE TESTS ARE MEANT TO BE RUN TOGETHER IN ORDER
    """

    def test_download_and_parse_points_csv(
        self,
        raw_catalog,
        s3tables_table_raw,
        s3tables_namespace,
        landing_zone,
        monkeypatch,
    ):
        s3, bucket_name = landing_zone

        table_name = s3tables_table_raw("ch_meteoschweiz/local_forecast/raw/points.json")

        monkeypatch.setattr(pipeline_points, "NAMESPACE", s3tables_namespace)
        monkeypatch.setenv("LANDING_ZONE_BUCKET", bucket_name)

        with (
            Path(__file__).resolve().parent / "fixtures/ogd-local-forecasting_meta_point.csv"
        ).open(encoding="latin-1") as f:
            s3.put_object(
                Bucket=bucket_name,
                Key="data.csv",
                Body=f.read(),
            )

        pipeline_points.download_and_store_raw("data.csv")

        identifier = f"{s3tables_namespace}.{table_name}"
        table = raw_catalog.load_table(identifier)
        result_data = table.scan().to_arrow().to_pylist()

        assert {
            row["point_id"]: row for row in result_data if row["point_id"] in {1, 611300, 494}
        } == {
            1: {
                "point_id": 1,
                "point_type_id": 1,
                "station_abbr": "ARO",
                "postal_code": None,
                "point_name": "Arosa",
                "point_type_de": "Station",
                "point_type_fr": "Station",
                "point_type_it": "Stazione",
                "point_type_en": "Station",
                "point_height_masl": 1878.0,
                "point_coordinates_lv95_east": 2771031.0,
                "point_coordinates_lv95_north": 1184830.0,
                "point_coordinates_wgs84_lat": 46.792661,
                "point_coordinates_wgs84_lon": 9.679014,
            },
            611300: {
                "point_id": 611300,
                "point_type_id": 2,
                "station_abbr": "",
                "postal_code": 6113,
                "point_name": "Romoos",
                "point_type_de": "Zentrum Postleitzahl",
                "point_type_fr": "Centre code postal",
                "point_type_it": "Centro codice postale",
                "point_type_en": "Postal code center",
                "point_height_masl": 780.0,
                "point_coordinates_lv95_east": 2644359.0,
                "point_coordinates_lv95_north": 1206766.0,
                "point_coordinates_wgs84_lat": 47.010458,
                "point_coordinates_wgs84_lon": 8.021989,
            },
            494: {
                "point_id": 494,
                "point_type_id": 3,
                "station_abbr": "",
                "postal_code": None,
                "point_name": "Cabane Rambert CAS",
                "point_type_de": "Point of Interest",
                "point_type_fr": "Point of Interest",
                "point_type_it": "Point of Interest",
                "point_type_en": "Point of Interest",
                "point_height_masl": 2580.0,
                "point_coordinates_lv95_east": 2576517.0,
                "point_coordinates_lv95_north": 1119908.0,
                "point_coordinates_wgs84_lat": 46.230206,
                "point_coordinates_wgs84_lon": 7.134239,
            },
        }

    def test_sanitize_data(
        self, sanitize_catalog, s3tables_table_sanitize, s3tables_namespace, monkeypatch
    ) -> None:
        sanitize_table_name = s3tables_table_sanitize(
            "ch_meteoschweiz/local_forecast/sanitize/points.json"
        )

        monkeypatch.setattr(pipeline_points, "NAMESPACE", s3tables_namespace)

        pipeline_points.sanitize_data()

        identifier = f"{s3tables_namespace}.{sanitize_table_name}"
        table = sanitize_catalog.load_table(identifier)
        result_data = table.scan().to_arrow().to_pylist()

        assert {
            row["point_id"]: row for row in result_data if row["point_id"] in {1, 611300, 494}
        } == {
            1: {
                "point_id": 1,
                "point_type_id": 1,
                "station_abbr": "ARO",
                "postal_code": None,
                "point_name": "Arosa",
                "point_type_de": "Station",
                "point_type_fr": "Station",
                "point_type_it": "Stazione",
                "point_type_en": "Station",
                "point_height_masl": 1878.0,
                "point_coordinates_lv95_east": 2771031.0,
                "point_coordinates_lv95_north": 1184830.0,
            },
            611300: {
                "point_id": 611300,
                "point_type_id": 2,
                "station_abbr": "",
                "postal_code": 6113,
                "point_name": "Romoos",
                "point_type_de": "Zentrum Postleitzahl",
                "point_type_fr": "Centre code postal",
                "point_type_it": "Centro codice postale",
                "point_type_en": "Postal code center",
                "point_height_masl": 780.0,
                "point_coordinates_lv95_east": 2644359.0,
                "point_coordinates_lv95_north": 1206766.0,
            },
            494: {
                "point_id": 494,
                "point_type_id": 3,
                "station_abbr": "",
                "postal_code": None,
                "point_name": "Cabane Rambert CAS",
                "point_type_de": "Point of Interest",
                "point_type_fr": "Point of Interest",
                "point_type_it": "Point of Interest",
                "point_type_en": "Point of Interest",
                "point_height_masl": 2580.0,
                "point_coordinates_lv95_east": 2576517.0,
                "point_coordinates_lv95_north": 1119908.0,
            },
        }

    def test_export_data(
        self, load_catalog, s3tables_table_load, s3tables_namespace, features_database, monkeypatch
    ):
        load_table_name = s3tables_table_load("ch_meteoschweiz/local_forecast/load/points.json")

        monkeypatch.setattr(pipeline_points, "NAMESPACE", s3tables_namespace)

        pipeline_points.export_data_to_features()

        identifier = f"{s3tables_namespace}.{load_table_name}"
        table = load_catalog.load_table(identifier)
        result_data = table.scan().to_arrow().to_pylist()

        assert {
            row["point_id"]: row for row in result_data if row["point_id"] in {1, 611300, 494}
        } == {
            1: {
                "point_id": 1,
                "point_type_id": 1,
                "station_abbr": "ARO",
                "postal_code": None,
                "point_name": "Arosa",
                "point_type_de": "Station",
                "point_type_fr": "Station",
                "point_type_it": "Stazione",
                "point_type_en": "Station",
                "point_height_masl": 1878.0,
                "geometry": "POINT (2771031 1184830)",
            },
            611300: {
                "point_id": 611300,
                "point_type_id": 2,
                "station_abbr": "",
                "postal_code": 6113,
                "point_name": "Romoos",
                "point_type_de": "Zentrum Postleitzahl",
                "point_type_fr": "Centre code postal",
                "point_type_it": "Centro codice postale",
                "point_type_en": "Postal code center",
                "point_height_masl": 780.0,
                "geometry": "POINT (2644359 1206766)",
            },
            494: {
                "point_id": 494,
                "point_type_id": 3,
                "station_abbr": "",
                "postal_code": None,
                "point_name": "Cabane Rambert CAS",
                "point_type_de": "Point of Interest",
                "point_type_fr": "Point of Interest",
                "point_type_it": "Point of Interest",
                "point_type_en": "Point of Interest",
                "point_height_masl": 2580.0,
                "geometry": "POINT (2576517 1119908)",
            },
        }

        with features_database.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    point_id,
                    point_type_id,
                    station_abbr,
                    postal_code,
                    point_name,
                    point_type_de,
                    point_type_fr,
                    point_type_it,
                    point_type_en,
                    point_height_masl,
                    ST_asText(geometry) as geometry
                FROM ch_meteoschweiz_local_forecast_point
                WHERE point_id IN (1, 611300, 494)
            """)
            rows = cur.fetchall()

        assert rows == [
            {
                "point_id": 1,
                "point_type_id": 1,
                "station_abbr": "ARO",
                "postal_code": None,
                "point_name": "Arosa",
                "point_type_de": "Station",
                "point_type_fr": "Station",
                "point_type_it": "Stazione",
                "point_type_en": "Station",
                "point_height_masl": 1878.0,
                "geometry": "POINT(2771031 1184830)",
            },
            {
                "point_id": 611300,
                "point_type_id": 2,
                "station_abbr": "",
                "postal_code": 6113,
                "point_name": "Romoos",
                "point_type_de": "Zentrum Postleitzahl",
                "point_type_fr": "Centre code postal",
                "point_type_it": "Centro codice postale",
                "point_type_en": "Postal code center",
                "point_height_masl": 780.0,
                "geometry": "POINT(2644359 1206766)",
            },
            {
                "point_id": 494,
                "point_type_id": 3,
                "station_abbr": "",
                "postal_code": None,
                "point_name": "Cabane Rambert CAS",
                "point_type_de": "Point of Interest",
                "point_type_fr": "Point of Interest",
                "point_type_it": "Point of Interest",
                "point_type_en": "Point of Interest",
                "point_height_masl": 2580.0,
                "geometry": "POINT(2576517 1119908)",
            },
        ]
