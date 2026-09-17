# --- Build stage: install dependencies into a clean prefix -------------------
FROM python:3.13-slim AS build
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Runtime stage: only what is needed to run ------------------------------
FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080
WORKDIR /app
COPY --from=build /install /usr/local
COPY app.py .
# Run as a non-root, non-existent-in-/etc/passwd user (matches the Pod securityContext)
USER 65532:65532
EXPOSE 8080
# gunicorn = production WSGI server (the Flask dev server is for laptops only)
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--access-logfile", "-", "app:app"]
