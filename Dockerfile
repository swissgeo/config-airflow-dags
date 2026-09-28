FROM apache/airflow:3.2.2 AS dependencies

COPY --chown=airflow:root pyproject.toml uv.lock /opt/airflow/dag-project/

WORKDIR /opt/airflow/dag-project
RUN uv export \
    --locked \
    --no-dev \
    --no-emit-project \
    --no-hashes \
    --format requirements-txt \
    --output-file /tmp/dag-requirements.txt \
    && uv pip install \
    --no-cache \
    --target /opt/airflow/dag-source/python \
    --requirements /tmp/dag-requirements.txt \
    && rm /tmp/dag-requirements.txt

COPY --chown=airflow:root DAG/ /opt/airflow/dag-source/
# TODO include the toolset so that it will be used by airflow when running a DAG

FROM busybox:1.37.0

COPY --from=dependencies --chown=50000:0 /opt/airflow/dag-source/ /opt/airflow/dag-source/
COPY --chown=50000:0 --chmod=0555 deploy-dags.sh /usr/local/bin/deploy-dags

USER 50000:0

ENTRYPOINT ["/usr/local/bin/deploy-dags"]
