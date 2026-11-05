FROM python:3.12-slim

# Send logs straight to stdout so `docker logs` shows them as they happen.
ENV PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app
COPY triage_agent ./triage_agent

EXPOSE 8080

# Exec form, so the Python process is PID 1 and receives SIGTERM from `docker stop`.
CMD ["python", "-m", "triage_agent"]
