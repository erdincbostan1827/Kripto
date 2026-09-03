FROM python:3.12.14-slim-bookworm@sha256:a116514e19457bcb7af7efe9c3dd0b9b71e85b317694e7882a1c52aa15a78134 AS base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1 PYTHONPATH=/app/backend VIRTUAL_ENV=/app/.venv PATH="/app/.venv/bin:$PATH"
RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser
COPY pyproject.toml uv.lock /app/
COPY backend /app/backend
COPY scripts /app/scripts
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini
COPY database /app/database
RUN pip install --no-cache-dir 'uv==0.12.9' \
    && uv sync --locked --no-dev \
    && pip uninstall -y uv \
    && rm -rf /root/.cache/uv /root/.cache/pip

FROM base AS test
USER root
RUN pip install --no-cache-dir 'uv==0.12.9' \
    && uv sync --locked --extra test \
    && pip uninstall -y uv \
    && rm -rf /root/.cache/uv /root/.cache/pip
COPY tests /app/tests
USER appuser
CMD ["python","-m","pytest","-q","-W","error","-p","no:cacheprovider"]

FROM base AS runtime
USER appuser
EXPOSE 8000
CMD ["python","/app/scripts/container_entrypoint.py"]
