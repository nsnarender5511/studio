
import asyncio
import threading
import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService, State, SessionService
from google.adk.artifacts import InMemoryArtifactService, ArtifactService
from google.adk.memory import InMemoryMemoryService, MemoryService

# --- Import Agents and Tools (relative imports assuming server.py is run from the project root or similar) ---
from .agents.orchestrator import OrchestratorAgent
from .agents.orchestrator import (
    file_identification_agent, structure_designer_agent, code_parser_agent,
    code_interpreter_agent, dependency_analyzer_agent, testing_analyzer_agent,
    feature_extractor_agent, content_generator_agent, verifier_agent,
    visualizer_agent, md_formatter_agent, obsidian_writer_agent, summarizer_agent,
    fact_checker_agent, self_reflection_agent, code_execution_verifier_agent
)
from .tools import (
    read_directory_tool, read_file_tool, write_file_tool, ensure_directory_exists_tool,
    code_parser_tool, dependency_analyzer_tool, web_search_tool, visualization_tool,
    format_obsidian_links_tool, knowledge_graph_tool, memory_interaction_tool,
    fact_verification_tool, code_executor_tool
)
from .services.memory_service import get_memory_service # Example factory

import sys
import os
import pathlib
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field, asdict
from datetime import datetime

app = Flask(__name__)
CORS(app) # Allow requests from the frontend development server

# --- Global State Management (Simple In-Memory) ---
# WARNING: This is simple and not suitable for production. Lost on server restart.
# Consider using a database or persistent storage for real applications.
executor = ThreadPoolExecutor(max_workers=5) # Pool for running ADK jobs
active_jobs = {} # Dictionary to store job status: {job_id: JobStatus}

@dataclass
class JobStatus:
    job_id: str
    repo_url: str
    status: str = "pending" # pending, running, completed, failed
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: datetime | None = None
    details: str | None = None
    final_state_summary: dict | None = None # Store relevant final state parts

# --- ADK Setup ---
def create_service_factory(service_type: str = "memory", **kwargs) -> tuple[SessionService, ArtifactService, MemoryService]:
    """Create appropriate services based on configuration."""
    # Simplified for now, always using memory services
    print("Using InMemory services for ADK runner.")
    session_service = InMemorySessionService()
    artifact_service = InMemoryArtifactService()
    memory_service = get_memory_service(service_type="memory")
    return session_service, artifact_service, memory_service

def run_adk_process(job_id: str, repo_path_str: str, output_dir_str: str, use_obsidian: bool):
    """The actual function to run the ADK documentation process."""
    global active_jobs
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        active_jobs[job_id].status = "running"
        print(f"Job {job_id}: Starting ADK process for {repo_path_str}")

        session_service, artifact_service, memory_service = create_service_factory()

        sub_agents = {
            "file_identification": file_identification_agent,
            "structure_designer": structure_designer_agent,
            "code_parser": code_parser_agent,
            "code_interpreter": code_interpreter_agent,
            "dependency_analyzer": dependency_analyzer_agent,
            "testing_analyzer": testing_analyzer_agent,
            "feature_extractor": feature_extractor_agent,
            "content_generator": content_generator_agent,
            "verifier": verifier_agent,
            "visualizer": visualizer_agent,
            "md_formatter": md_formatter_agent,
            "obsidian_writer": obsidian_writer_agent,
            "summarizer": summarizer_agent,
            "fact_checker": fact_checker_agent,
            "self_reflection": self_reflection_agent,
            "code_execution_verifier": code_execution_verifier_agent,
        }
        tools = [
            read_directory_tool, read_file_tool, write_file_tool, ensure_directory_exists_tool,
            code_parser_tool, dependency_analyzer_tool, web_search_tool, visualization_tool,
            format_obsidian_links_tool, knowledge_graph_tool, memory_interaction_tool,
            fact_verification_tool, code_executor_tool
        ]

        orchestrator = OrchestratorAgent(sub_agents=sub_agents, tools=tools)
        runner = Runner(
            agent=orchestrator,
            session_service=session_service,
            artifact_service=artifact_service,
            memory_service=memory_service,
            app_name="GitDocuRunner",
        )

        initial_state = State({
            "repo_path": repo_path_str,
            "output_dir": output_dir_str,
            "use_obsidian_format": use_obsidian,
            "verbose_logging": True # Enable verbose logging from ADK agents/tools
        })

        # Run the ADK process synchronously within the asyncio loop
        final_event = loop.run_until_complete(runner.run(initial_state=initial_state))
        final_state = final_event.state if hasattr(final_event, 'state') else State({})

        # Extract summary from final state (adjust keys as needed based on SummarizerAgent output)
        plan = final_state.get('documentation_plan', [])
        summary_status = final_state.get('summary_status', 'Not run or status unavailable')
        success_count = sum(1 for item in plan if item.get('status') == 'done')
        fail_count = sum(1 for item in plan if item.get('status') == 'failed')

        active_jobs[job_id].status = "completed"
        active_jobs[job_id].details = f"Processed {len(plan)} files. {success_count} succeeded, {fail_count} failed. Summary: {summary_status}"
        active_jobs[job_id].final_state_summary = { # Store only serializable parts
             "documentation_plan": plan,
             "summary_status": summary_status
        }
        print(f"Job {job_id}: ADK process completed successfully.")

    except Exception as e:
        active_jobs[job_id].status = "failed"
        active_jobs[job_id].details = f"Error during ADK process: {str(e)}"
        print(f"Job {job_id}: ADK process failed: {e}")
        import traceback
        traceback.print_exc() # Print full traceback to server logs
    finally:
        active_jobs[job_id].end_time = datetime.utcnow()
        loop.close()


# --- API Endpoints ---

@app.route('/document', methods=['POST'])
def start_documentation():
    """
    Starts the documentation process for a given Git repository URL.
    For now, it assumes the URL points to a local path.
    In a real scenario, this would clone the repo first.
    """
    global active_jobs
    data = request.get_json()
    if not data or 'repoUrl' not in data:
        return jsonify({"error": "Missing 'repoUrl' in request body"}), 400

    repo_url = data['repoUrl']
    # --- !!! SECURITY WARNING !!! ---
    # Directly using the input URL as a path is extremely dangerous.
    # In a real application:
    # 1. Validate the URL is a git repository URL.
    # 2. Clone the repository to a secure, temporary location.
    # 3. Use the path to the temporary clone.
    # For this example, we'll *assume* repoUrl is a safe local path for now.
    # We add a basic check to prevent trivial path traversal, but this is NOT sufficient.
    if ".." in repo_url or not os.path.isabs(repo_url):
         # Basic check, needs significant improvement for security
         # A better approach is to clone to a known base directory
         print(f"Warning: Potential unsafe path requested: {repo_url}. Treating as local path for demo.")
         # For demo, treat it as local path but maybe relative to a base dir?
         # For simplicity, let's assume it's a valid path that exists where the server runs.
         # If it doesn't exist, ADK file operations will fail later.
         repo_path_str = repo_url # Still potentially unsafe
    else:
        repo_path_str = repo_url

    # Validate if the path exists (basic check)
    if not os.path.isdir(repo_path_str):
         # If not absolute, try relative to current dir (less safe)
         repo_path_str_rel = os.path.abspath(repo_url)
         if not os.path.isdir(repo_path_str_rel):
              return jsonify({"error": f"Repository path not found or not a directory: {repo_url}"}), 400
         repo_path_str = repo_path_str_rel # Use resolved absolute path


    job_id = str(uuid.uuid4())
    output_dir_base = os.path.abspath("gitdocu_output") # Base output dir
    output_dir_job = os.path.join(output_dir_base, job_id) # Job-specific output dir

    try:
        os.makedirs(output_dir_job, exist_ok=True)
    except Exception as e:
         return jsonify({"error": f"Could not create output directory: {e}"}), 500

    use_obsidian = data.get('obsidianFormat', False) # Optional flag from frontend

    # Create job status entry
    job_status = JobStatus(job_id=job_id, repo_url=repo_url)
    active_jobs[job_id] = job_status

    # Run the ADK process in a background thread
    executor.submit(run_adk_process, job_id, repo_path_str, output_dir_job, use_obsidian)

    print(f"Job {job_id}: Submitted for processing repo {repo_url}")
    return jsonify({"job_id": job_id, "status": "pending", "message": "Documentation process started."}), 202

@app.route('/status/<job_id>', methods=['GET'])
def get_status(job_id):
    """Returns the status of a specific documentation job."""
    job = active_jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    # Use asdict for easy JSON conversion, handle datetime separately if needed
    return jsonify(asdict(job))

@app.route('/history', methods=['GET'])
def get_history():
    """Returns the history of all documentation jobs."""
    # Sort jobs by start time, newest first
    sorted_jobs = sorted(active_jobs.values(), key=lambda j: j.start_time, reverse=True)
    # Convert job objects to dictionaries for JSON response
    history_list = [asdict(job) for job in sorted_jobs]
    return jsonify(history_list)


def run_server():
     # Set environment variable for Gemini API Key if needed by ADK
     # Ensure you have GOOGLE_API_KEY set in your environment where the server runs
     # if 'GOOGLE_API_KEY' not in os.environ:
     #    print("Warning: GOOGLE_API_KEY environment variable not set. ADK might fail.")

     # Determine host and port
     host = os.environ.get('FLASK_HOST', '127.0.0.1')
     port = int(os.environ.get('FLASK_PORT', 5001)) # Use 5001 to avoid potential conflicts

     print(f"Starting Flask server on http://{host}:{port}")
     app.run(host=host, port=port, debug=False) # Turn debug off for stability with threading


if __name__ == '__main__':
    # This allows running the server directly with `python -m backend.src.git_repo_documentor.server`
    # Make sure PYTHONPATH includes the project root or adjust imports accordingly.
     run_server()

# To run from project root: poetry run python -m backend.src.git_repo_documentor.server
# Ensure backend/src is in PYTHONPATH if running differently.

```