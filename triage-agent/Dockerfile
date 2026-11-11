# syntax=docker/dockerfile:1

# Stage 1: run the test suite. The build fails here if any test fails,
# so a broken image can't be produced.
FROM python:3.12-slim@sha256:4840d514c583a4d3d8cad3940e68dee6f0f6f3635c12fcd0a3d74c21a5b93a54 AS test
WORKDIR /src
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY . .
RUN pytest -q

# Stage 2: install runtime dependencies into /install and byte-compile the package,
# so the runtime image needs neither pip's cache nor write access to the code.
FROM python:3.12-alpine@sha256:2f83d24758cf1ad4a38975d83bf48e5d10b121499bffec99daf7a07a437207b9 AS build
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt
COPY triage_agent ./triage_agent
RUN python -m compileall -q triage_agent

# Stage 3: the runtime image. Alpine base, the dependencies, the compiled package and nothing else.
FROM python:3.12-alpine@sha256:2f83d24758cf1ad4a38975d83bf48e5d10b121499bffec99daf7a07a437207b9 AS runtime

# Standard OCI labels. VERSION and REVISION are passed in at build time so
# `docker inspect` shows which release and commit an image was built from.
ARG VERSION=dev
ARG REVISION=unknown
LABEL org.opencontainers.image.title="triage-agent" \
      org.opencontainers.image.description="Turns an Alertmanager alert into a short triage summary for the on-call engineer" \
      org.opencontainers.image.source="https://github.com/AnuRadhaRao/sre-tools" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${REVISION}"

# Send logs straight to stdout so `docker logs` shows them as they happen.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

# A fixed, unprivileged user. The numeric uid lets Kubernetes runAsNonRoot verify it.
RUN addgroup -S -g 10001 app && adduser -S -D -H -u 10001 -G app app

WORKDIR /app
# Only finish once tests have passed: this line makes the runtime stage depend on the test stage.
COPY --from=test /src/pytest.ini /tmp/tests-passed
COPY --from=build /install /usr/local
COPY --from=build /app/triage_agent ./triage_agent

# Files stay owned by root, so the app can read its code but not change it.
USER 10001:10001

EXPOSE 8080

# Alpine has no curl, so the check uses Python's own HTTP client against /healthz.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD ["python", "-c", "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ['PORT'] + '/healthz', timeout=2)"]

# Exec form, so the Python process is PID 1 and receives SIGTERM from `docker stop`.
CMD ["python", "-m", "triage_agent"]
