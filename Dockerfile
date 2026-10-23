# -------- builder stage ----------
# remember to update the pinned version in pyproject.toml
FROM apache/airflow:3.3.2-python3.14 AS builder

USER root
WORKDIR /src/

COPY pyproject.toml uv.lock ./

# install dependencies. Install them via export and pip install so that
# it won't be installed into a virtualenv, which can't be picked up
# by airflow
RUN --mount=type=cache,target=/root/.cache/uv \
    uv export --frozen --no-dev --no-hashes --no-emit-project \
    --no-emit-package apache-airflow -o requirements.txt \
    && uv pip install --python /usr/local/bin/python --target /install \
    -r requirements.txt

# install the toolbase as a python package
COPY swissgeo_toolset/ swissgeo_toolset/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --python /usr/local/bin/python --target /install \
    --no-deps .

# ----- final stage ------------------
FROM busybox:1.37.0

# copy the python deps
COPY --from=builder /install \
    /opt/airflow/dags-staging/python/

# copy the actual DAGs
COPY DAG/  /opt/airflow/dags-staging/
