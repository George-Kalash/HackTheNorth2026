FROM node:22-alpine AS web
WORKDIR /build/web
COPY web/package*.json ./
COPY web/.npmrc ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.13-slim
RUN pip install --no-cache-dir uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY src ./src
RUN uv sync --frozen --no-dev
COPY migrations ./migrations
COPY alembic.ini ./
COPY --from=web /build/web/dist ./web/dist
RUN mkdir -p data && useradd --uid 10001 --create-home terminal && chown -R terminal:terminal /app
USER terminal
EXPOSE 8010
CMD ["uv", "run", "--no-dev", "uvicorn", "prediction_terminal.api.app:app", "--host", "0.0.0.0", "--port", "8010"]
