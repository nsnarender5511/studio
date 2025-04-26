# GitDocu Backend

This directory contains the Python backend service for GitDocu, implemented using Google ADK and Flask.

## Setup

1.  Install [Poetry](https://python-poetry.org/docs/#installation).
2.  Navigate to the `backend` directory.
3.  Run `poetry install` to install dependencies, including Flask.
4.  Ensure you have necessary environment variables set, especially `GOOGLE_API_KEY`. Copy `.env.example` to `.env` if needed and populate it. (Note: You might need to create a `.env.example` file).

## Running the Server

Ensure the required environment variables are set (e.g., in a `.env` file in the `backend` directory).

Set the `FLASK_APP` environment variable:
```bash
# Option 1: Set temporarily (Bash/Zsh)
export FLASK_APP="src.app:create_app"

# Option 2: Set temporarily (Fish)
set -x FLASK_APP "src.app:create_app"

# Option 3: Use .flaskenv file
# Create a file named .flaskenv in the 'backend' directory with the line:
# FLASK_APP=src.app:create_app
```

Then, run the Flask development server from the `backend` directory:
```bash
poetry run flask run --host=$FLASK_HOST --port=$FLASK_PORT
```
(Defaults to `host=127.0.0.1` and `port=5001` if `FLASK_HOST`/`FLASK_PORT` are not set in your environment or `.env` file).

## API Endpoints

The API is versioned under `/api/v1`.

-   `POST /api/v1/jobs`: Starts the documentation generation job for a given repository URL.
    -   Body: `{ "repoUrl": "<git_repository_url>", "obsidianFormat": <boolean> }` (e.g., `{ "repoUrl": "https://github.com/user/repo.git", "obsidianFormat": false }`)
    -   Returns (on success): `{ "job_id": "...", "status": "PENDING", "message": "...", "clone_dir": "...", "output_dir": "..." }` (Status Code: 202)
    -   Returns (on error): `{ "error": "..." }` (Status Code: 400 or 500)
-   `GET /api/v1/status/<job_id>`: Gets the status and details of a specific job.
    -   Returns: `{ "job_id": "...", "repo_url": "...", "status": "...", "request_time": "...", "end_time": "...", "details": "...", "error_info": {...} }` (Status Code: 200 or 404)
-   `GET /api/v1/history`: Gets a list of recent job history records (default limit applies).
    -   Returns: `[ { "job_id": "...", "repo_url": "...", "status": "...", ... }, ... ]` (Status Code: 200)

## Running Celery Worker

To process the background jobs, a Celery worker needs to be running:

```bash
# From the 'backend' directory
poetry run celery -A src.app.celery_app worker --loglevel=info
```

## Running ADK Runner Directly (CLI)

(This section might be outdated or require a specific CLI entry point not currently implemented.)
<!--
You can still run the ADK process directly via the CLI for testing individual runs without the server:

```bash
# From the root project directory
poetry run python backend/src/git_repo_documentor/main.py <path_to_repo> [options]
```

Refer to `main.py --help` for available command-line options.
-->
