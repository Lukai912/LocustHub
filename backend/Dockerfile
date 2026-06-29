FROM node:20-alpine AS frontend-build

WORKDIR /app

ARG VITE_API_BASE_URL=/api/v1
ARG VITE_DEMO_TOKEN=dev-token
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_DEMO_TOKEN=${VITE_DEMO_TOKEN}

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --registry=https://registry.npmjs.org/

COPY frontend/ ./
RUN npm run build

FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV FRONTEND_DIST_DIR=/app/frontend_dist

WORKDIR /app

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY backend/app /app/app
COPY --from=frontend-build /app/dist /app/frontend_dist

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
