# syntax=docker/dockerfile:1

# Same pattern as the agent image: tests gate the build, the runtime is Alpine and non-root.
FROM python:3.12-slim@sha256:4840d514c583a4d3d8cad3940e68dee6f0f6f3635c12fcd0a3d74c21a5b93a54 AS test
WORKDIR /src
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY . .
RUN pytest -q

FROM python:3.12-alpine@sha256:2f83d24758cf1ad4a38975d83bf48e5d10b121499bffec99daf7a07a437207b9 AS runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080
RUN addgroup -S -g 10001 app && adduser -S -D -H -u 10001 -G app app
WORKDIR /app
# Makes the runtime stage depend on the test stage, so tests always run.
COPY --from=test /src/pytest.ini /tmp/tests-passed
COPY checkout.py .
USER 10001:10001
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD ["python", "-c", "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ['PORT'] + '/healthz', timeout=2)"]
CMD ["python", "checkout.py"]
