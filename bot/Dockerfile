# Stage 1: Build frontend
FROM node:20-slim AS frontend
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: Python app
FROM python:3.13-slim

WORKDIR /app

COPY bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot/ .
COPY --from=frontend /frontend/dist /app/static/dashboard

RUN mkdir -p /app/data

EXPOSE 8111

CMD ["python", "main.py"]
