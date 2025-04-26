# GitDocu - AI Git Repository Documentor

This project uses AI (via Google ADK and Gemini) to automatically generate documentation for Git repositories. It consists of a Next.js frontend and a Python (Flask + ADK) backend.

## Project Structure

-   `/`: Next.js frontend application (using App Router)
-   `/backend`: Python backend service (Flask API wrapping Google ADK)

## Getting Started

### Prerequisites

-   [Node.js](https://nodejs.org/) (v18 or later recommended)
-   [Yarn](https://yarnpkg.com/) (Classic or Berry)
-   [Python](https://www.python.org/) (v3.9 or later recommended)
-   [Poetry](https://python-poetry.org/docs/#installation) (for Python package management)
-   [Git](https://git-scm.com/)
-   A Google Cloud project with the Gemini API enabled (or other compatible Generative AI service configured in ADK).
-   Set the `GOOGLE_API_KEY` environment variable (see `.env.example` or `.env`).

### Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Install Frontend Dependencies:**
    ```bash
    yarn install
    ```

3.  **Install Backend Dependencies:**
    ```bash
    cd backend
    poetry install
    cd ..
    ```

4.  **Configure Environment Variables:**
    -   Create a `.env` file in the root directory (copy from `.env.example` if provided, or create manually).
    -   Set `BACKEND_API_URL`: This should point to where your Python backend will run (default is `http://127.0.0.1:5001`).
    -   Set `GOOGLE_API_KEY`: Your API key for Google AI services (Gemini). The backend reads this directly from its environment.

### Running the Application

You need to run both the frontend and backend services concurrently.

1.  **Run the Backend Service:**
    Open a terminal in the **root project directory**:
    ```bash
    poetry run python -m backend.src.git_repo_documentor
    ```
    The backend server should start, typically on `http://127.0.0.1:5001`.

2.  **Run the Frontend Service:**
    Open *another* terminal in the **root project directory**:
    ```bash
    yarn dev
    ```
    The frontend development server should start, typically on `http://localhost:9002`.

3.  **Access the Application:**
    Open your browser and navigate to `http://localhost:9002` (or the port specified by Next.js).

## Usage

-   Enter a **GitHub repository URL** or a **local absolute path** to a Git repository on the machine *where the backend server is running*.
-   Click "Generate Documentation".
-   The request will be sent to the backend.
-   The "Execution History" table will update (you may need to refresh currently) showing the status of the documentation job. Running jobs will poll for updates.

## Development Notes

-   **Frontend**: Built with Next.js App Router, TypeScript, Tailwind CSS, and ShadCN UI components. Server Actions are used to communicate with the backend API.
-   **Backend**: Built with Python, Flask (as the API wrapper), and Google ADK (for the core multi-agent documentation logic). Uses Poetry for dependency management. Placeholder agents and tools are used in the current ADK implementation.
-   **Integration**: The Next.js frontend makes API calls to the Flask backend via Server Actions. CORS is enabled on the Flask server to allow requests from the frontend's origin during development.

## TODO / Future Improvements

-   Implement actual Git cloning in the backend instead of relying on local paths.
-   Fully implement the ADK agents and tools with real logic (currently placeholders).
-   Improve error handling and user feedback on both frontend and backend.
-   Add real-time updates to the history table (e.g., using WebSockets or Server-Sent Events) instead of polling.
-   Implement persistent storage for job history instead of in-memory storage.
-   Secure the local path input on the backend.
-   Add authentication/authorization if needed.
-   Complete ADK testing and reliability features (Checkpoints, Memory, KG).
