from airflow.sdk import BaseOperator

from swissgeo_toolset.file import download_from_landingzone
from swissgeo_toolset.tabular.converter import lowercase_column_names
from swissgeo_toolset.tabular.parser import parse_csv
from swissgeo_toolset.tabular.writer import write_to_s3tables


class CsvFromLandingzoneToRawOperator(BaseOperator):
    """This is a custom operator wrapping the standard
    file downloading from landing-zone and storing to raw

    We're intentionally still using the swissgeo_toolset functions but wrapping
    them into this custom airflow operator, since most cases will probably
    just use these few operations.

    If there are custom operations needed that go beyond what is done here,
    please use a PythonOperator in the DAG instead of bloating and/or
    overengineering this operator here.
    """

    template_fields = ("file_key", "encoding", "delimiter", "quote_char", "namespace", "table_name")

    def __init__(  # noqa: PLR0913, PLR0917
        self,
        name: str,
        file_key: str,
        encoding: str,
        delimiter: str,
        quote_char: str,
        namespace: str,
        table_name: str,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.name = name
        self.file_key = file_key
        self.encoding = encoding
        self.delimiter = delimiter
        self.quote_char = quote_char
        self.namespace = namespace
        self.table_name = table_name

    def execute(self, context) -> None:  # noqa: ANN001, ARG002
        with download_from_landingzone(file_key=self.file_key) as file:
            df = parse_csv(
                file, encoding=self.encoding, delimiter=self.delimiter, quote_char=self.quote_char
            )

        df = lowercase_column_names(df)
        write_to_s3tables(df, "raw", self.namespace, self.table_name)
