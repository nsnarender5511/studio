import asyncio
import argparse
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService, State, SessionService
from google.adk.artifacts import InMemoryArtifactService, ArtifactService
from google.adk.memory import InMemoryMemoryService, MemoryService

# --- Import Services ---
# In a real setup, you might use VertexAI services
# from google.adk.sessions import VertexAiSessionService
# from google.adk.artifacts import GcsArtifactService
# from google.adk.memory import VertexAiRagMemoryService
from .services.memory_service import get_memory_service # Example factory

# --- Import Agents and Tools ---
# Import the main orchestrator
from .agents.orchestrator import OrchestratorAgent

# Import all placeholder sub-agents (defined within orchestrator.py for now)
from .agents.orchestrator import (
    file_identification_agent, structure_designer_agent, code_parser_agent,
    code_interpreter_agent, dependency_analyzer_agent, testing_analyzer_agent,
    feature_extractor_agent, content_generator_agent, verifier_agent,
    visualizer_agent, md_formatter_agent, obsidian_writer_agent, summarizer_agent,
    fact_checker_agent, self_reflection_agent, code_execution_verifier_agent
    # Add memory/KG agents if they are part of the main flow controlled by orchestrator
)

# Import all placeholder tools (defined within tools/__init__.py for now)
from .tools import (
    read_directory_tool, read_file_tool, write_file_tool, ensure_directory_exists_tool,
    code_parser_tool, dependency_analyzer_tool, web_search_tool, visualization_tool,
    format_obsidian_links_tool, knowledge_graph_tool, memory_interaction_tool,
    fact_verification_tool, code_executor_tool
)

import sys
import os
import pathlib

def create_service_factory(service_type: str, **kwargs) -> tuple[SessionService, ArtifactService, MemoryService]:
    """Create appropriate services based on configuration."""
    project_id = kwargs.get("project_id")
    location = kwargs.get("location")
    bucket_name = kwargs.get("bucket_name")

    if service_type == "memory":
        print("Using InMemory services.")
        session_service = InMemorySessionService()
        artifact_service = InMemoryArtifactService()
        # Use the factory from memory_service.py
        memory_service = get_memory_service(service_type="memory")
        return session_service, artifact_service, memory_service
    elif service_type == "vertex":
        # Placeholder - Uncomment and configure when using Vertex
        # print(f"Using Vertex AI services (Project: {project_id}, Location: {location}, Bucket: {bucket_name})")
        # if not project_id or not location or not bucket_name:
        #     raise ValueError("Project ID, Location, and Bucket Name are required for Vertex AI services.")
        # from google.adk.sessions import VertexAiSessionService
        # from google.adk.artifacts import GcsArtifactService
        # session_service = VertexAiSessionService(project_id=project_id, location=location)
        # artifact_service = GcsArtifactService(bucket_name=bucket_name)
        # memory_service = get_memory_service(service_type="vertex", project_id=project_id, location=location)
        # return session_service, artifact_service, memory_service
        print("Vertex services are commented out. Using InMemory services instead.")
        return create_service_factory("memory", **kwargs) # Fallback to memory for now
    else:
        raise ValueError(f"Unknown service type: {service_type}")

async def main(args):
    """Main entry point with comprehensive configuration."""
    # Create services based on configuration
    try:
        session_service, artifact_service, memory_service = create_service_factory(
            args.service_type,
            project_id=args.project_id,
            location=args.location,
            bucket_name=args.bucket_name
        )
    except ValueError as e:
        print(f"Error creating services: {e}")
        sys.exit(1)


    # --- Assemble Agents and Tools ---
    # These are currently placeholders imported above
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
        # Add memory/KG agents here if needed in the main flow
    }

    tools = [
        read_directory_tool, read_file_tool, write_file_tool, ensure_directory_exists_tool,
        code_parser_tool, dependency_analyzer_tool, web_search_tool, visualization_tool,
        format_obsidian_links_tool, knowledge_graph_tool, memory_interaction_tool,
        fact_verification_tool, code_executor_tool
    ]
    # --- End Assembly ---


    # Ensure repo path is absolute and exists
    try:
        repo_path = pathlib.Path(args.repo_path).resolve(strict=True)
    except FileNotFoundError:
        print(f"Error: Repository path not found: {args.repo_path}")
        sys.exit(1)
    except Exception as e:
         print(f"Error resolving repository path: {e}")
         sys.exit(1)

    # Ensure output directory exists and is absolute
    try:
        output_dir = pathlib.Path(args.output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Error creating output directory '{args.output_dir}': {e}")
        sys.exit(1)


    # Initialize orchestrator with all sub-agents and tools
    orchestrator = OrchestratorAgent(sub_agents=sub_agents, tools=tools)

    # Create runner with memory service
    runner = Runner(
        agent=orchestrator,
        session_service=session_service,
        artifact_service=artifact_service,
        memory_service=memory_service, # Add memory service
        app_name="GitRepoDocumentor",
    )

    # Initialize state
    initial_state = State()
    initial_state.update({
        # Use string paths as state values often need to be serializable
        "repo_path": str(repo_path),
        "output_dir": str(output_dir),
        "use_obsidian_format": args.obsidian_format,
        "verbose_logging": args.verbose
        # Add any other initial config needed by agents
    })

    # Run documentation process
    print(f"Starting documentation for repository: {repo_path}")
    print(f"Output will be generated in: {output_dir}")
    print(f"Initial state: {initial_state}")

    try:
        final_event = await runner.run(initial_state=initial_state)
        final_state = final_event.state if hasattr(final_event, 'state') else State({}) # Get final state safely
    except Exception as e:
        print(f"\n--- RUNNER FAILED ---")
        print(f"An error occurred during the documentation process: {e}")
        # You might want to log the full traceback here
        # import traceback
        # traceback.print_exc()
        sys.exit(1)


    # Print summary information
    print("\n--- Documentation Process Completed ---")
    final_plan = final_state.get('documentation_plan', []) # Get plan from final state
    print("\nFinal Documentation Plan Status:")
    success_count = 0
    fail_count = 0
    pending_count = 0 # Should be 0 if loop completed

    if not final_plan:
        print("No documentation plan found in final state.")
    else:
        for item in final_plan:
            source = item.get('source_file', 'N/A')
            output = item.get('output_file', 'N/A')
            status = item.get('status', 'unknown')
            print(f"- {source} -> {output} : {status.upper()}")
            if status == 'done':
                success_count += 1
            elif status == 'failed':
                fail_count += 1
                print(f"  Reason: {item.get('reason', 'N/A')}")
            else:
                pending_count +=1

    print(f"\nSummary: {success_count} succeeded, {fail_count} failed, {pending_count} pending/skipped.")
    summary_status = final_state.get('summary_status') # Get summary status from final state
    if summary_status:
         print(f"Overall summary generation status: {summary_status}")
    else:
         print("Overall summary generation status not found in final state.")

    print("-------------------------------------")


def run_main():
    parser = argparse.ArgumentParser(description="Document a GitHub repository using ADK")
    parser.add_argument("repo_path", help="Path to the local repository directory to document")
    parser.add_argument("--output-dir", default="gitdocu_output", help="Output directory for documentation")
    parser.add_argument("--obsidian-format", action="store_true", help="Generate Obsidian-compatible markdown")
    parser.add_argument("--service-type", choices=["memory", "vertex"], default="memory",
                      help="Type of services to use (in-memory or Vertex AI - Vertex requires setup)")
    # Add args for Vertex configuration if needed
    parser.add_argument("--project-id", help="GCP project ID (for Vertex AI services)", default=os.environ.get("GCP_PROJECT_ID"))
    parser.add_argument("--location", default="us-central1", help="GCP location (for Vertex AI services)")
    parser.add_argument("--bucket-name", help="GCS bucket name (for persistent artifacts with Vertex)", default=os.environ.get("GCS_BUCKET_NAME"))

    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging (Placeholder - currently prints info)")

    args = parser.parse_args()

    # Validate Vertex config if chosen
    if args.service_type == "vertex" and (not args.project_id or not args.location or not args.bucket_name):
         # Commenting out the error for now as Vertex is not fully implemented
        # parser.error("--project-id, --location and --bucket-name are required when using Vertex AI services")
        print("Warning: Vertex AI selected but requires project-id, location, and bucket-name. Falling back to 'memory'.")
        args.service_type = "memory"


    # Input validation moved to main() using pathlib

    asyncio.run(main(args))


if __name__ == "__main__":
    run_main()
