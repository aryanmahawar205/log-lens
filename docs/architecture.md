# Architecture

## Overview
LogLens is a modular log analytics platform consisting of a backend written in Python (FastAPI + Polars) and a frontend written in React (Vite + TailwindCSS + TypeScript).

## Components

### Backend
The backend is responsible for receiving log files, parsing them, running high-performance queries using Polars, and exposing the analytics data via a REST API.

- **Models**: Defines the unified log schema (`NormalizedLogEntry`) using Pydantic. This schema provides a standardized format that all parsers translate into.
- **Parsers**: Abstracted parser classes (e.g., `ApacheAccessParser`) capable of interpreting specific server logs. More parsers can be easily plugged in.
- **Analytics**: A high-performance analytics engine built over Polars to perform aggregates and transformations dynamically.
- **API**: FastAPI routes exposed to interact with the frontend and receive external events/files.

### Frontend
The frontend presents visual summaries of the analyzed logs.
- Built via React and Vite.
- Implements TailwindCSS v4 natively to build a clean dashboard.

### Deployment
The entire platform is orchestrated using Docker Compose.
- `docker-compose.yml` mounts code into `backend` and builds the static artifacts for the `frontend` container using Nginx.
