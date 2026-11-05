# syntax=docker/dockerfile:1

# Stage 1: run the test suite. The build fails here if any test fails,
# so a broken image can't be produced.
FROM python:3.12-slim@sha256:4840d514c583a4d3d8cad3940e68dee6f0f6f3635c12fcd0a3d74c21a5b93a54 AS test
WORKDIR /src
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY . .
RUN pytest -q

# Stage 2: byte-compile the package once, so the runtime image needs no write access to it.
FROM python:3.12-alpine@sha256:2f83d24758cf1ad4a38975d83bf48e5d10b121499bffec99daf7a07a437207b9 AS build
WORKDIR /app
COPY triage_agent ./triage_agent
RUN python -m compileall -q triage_agent

# Stage 3: the runtime image. Alpine base, the compiled package and nothing else.
FROM python:3.12-alpine@sha256:2f83d24758cf1ad4a38975d83bf48e5d10b121499bffec99daf7a07a437207b9 AS runtime

# Send logs straight to stdout so `docker logs` shows them as they happen.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

WORKDIR /app
# Only finish once tests have passed: this line makes the runtime stage depend on the test stage.
COPY --from=test /src/pytest.ini /tmp/tests-passed
COPY --from=build /app/triage_agent ./triage_agent

EXPOSE 8080

# Exec form, so the Python process is PID 1 and receives SIGTERM from `docker stop`.
CMD ["python", "-m", "triage_agent"]
