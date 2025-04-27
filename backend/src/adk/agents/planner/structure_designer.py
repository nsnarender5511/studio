from google.adk.agents import LlmAgent
from google.adk.models import Gemini # Or your chosen LLM

# Define the LLM model (as per plan)
# Consider making this configurable or passed in
common_model = Gemini(model="gemini-1.5-flash-latest") # Use a faster model initially if desired

# Define the Agent (as per plan)
structure_designer_agent = LlmAgent(
    name="StructureDesignerAgent", # Added name
    model=common_model,
    instruction="Given a list of identified files in the 'identified_files' state variable, create a structured documentation plan. For each file, determine an appropriate output path within the 'output_dir' state variable, mirroring the source structure. Create a JSON list where each item is an object with 'source_file', 'output_file', and 'status' (set to 'pending') fields.",
    tools=[], # No external tools needed for this agent based on the plan
    output_key="documentation_plan", # Key where the plan will be stored in the state
    output_format="json", # Explicitly ask for JSON
    # Example of expected input state:
    # { "identified_files": ["src/main.py", "src/utils/helpers.py"], "output_dir": "docs_output" }
    # Example of expected output for the LLM:
    # {
    #   "documentation_plan": [
    #     { "source_file": "src/main.py", "output_file": "docs_output/src/main.md", "status": "pending" },
    #     { "source_file": "src/utils/helpers.py", "output_file": "docs_output/src/utils/helpers.md", "status": "pending" }
    #   ]
    # }
)

print("StructureDesignerAgent defined.")

# Example usage (for testing purposes, usually run via Orchestrator/Runner)
async def _test_run():
    from google.adk.sessions import State
    # Example input state based on previous agent's output
    initial_state = State({
        "repo_path": "/path/to/your/repo",
        "output_dir": "docs/generated",
        "identified_files": ["/path/to/your/repo/src/app.py", "/path/to/your/repo/lib/utils.js"]
    })
    # Need ArtifactService for agent execution, even if dummy
    from google.adk.artifacts import InMemoryArtifactService
    artifact_service = InMemoryArtifactService()
    result_state = await structure_designer_agent.run(initial_state, artifact_service)
    print("Test run result state:", result_state)
    # Expected output might look like:
    # Test run result state: { ...input_state..., 'documentation_plan': [ ... ] }

if __name__ == "__main__":
    import asyncio
    # asyncio.run(_test_run()) # Commented out as direct execution might need more setup
    pass
