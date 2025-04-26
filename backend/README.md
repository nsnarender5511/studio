# GitDocu Backend

This directory contains the Python backend service for GitDocu, implemented using Google ADK and Flask.

## Setup

1.  Install [Poetry](https://python-poetry.org/docs/#installation).
2.  Navigate to the `backend` directory.
3.  Run `poetry install` to install dependencies, including Flask.
4.  Ensure you have necessary environment variables set, especially `GOOGLE_API_KEY` if required by your ADK configuration/Gemini usage.

## Running the Server

To start the backend API server:

```bash
# From the root project directory
poetry run python -m backend.src.git_repo_documentor

# Or, if inside the 'backend' directory
poetry run python -m src.git_repo_documentor
```

The server will typically start on `http://127.0.0.1:5001` by default. You can configure the host and port using `FLASK_HOST` and `FLASK_PORT` environment variables.

## API Endpoints

-   `POST /document`: Starts the documentation process for a given repository URL or local path.
    -   Body: `{ "repoUrl": "<url_or_path>" }`
    -   Returns: `{ "job_id": "...", "status": "pending", ... }`
-   `GET /status/<job_id>`: Gets the status of a specific job.
    -   Returns: Job details (status, start/end times, details, etc.)
-   `GET /history`: Gets a list of all processed jobs.
    -   Returns: Array of job detail objects.

## Running the ADK Runner Directly (CLI)

You can still run the ADK process directly via the CLI for testing individual runs without the server:

```bash
# From the root project directory
poetry run python backend/src/git_repo_documentor/main.py <path_to_repo> [options]
```

Refer to `main.py --help` for available command-line options.
