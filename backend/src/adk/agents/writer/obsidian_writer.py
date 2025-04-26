from google.adk.agents import LlmAgent
from google.adk.models import Gemini # Or your chosen LLM
from google.adk.tools import FunctionTool
import os
import re

# --- Placeholder Tools (Replace with actual imports) ---
def placeholder_ensure_directory_exists(path: str) -> None:
    """Placeholder for ensuring a directory exists."""
    dir_path = os.path.dirname(path)
    if dir_path:
        print(f"Placeholder: Ensuring directory exists for: {dir_path}")
        # os.makedirs(dir_path, exist_ok=True)
    else:
         print(f"Placeholder: No directory part in path '{path}', assuming current dir.")

ensure_directory_exists_tool = FunctionTool(
    func=placeholder_ensure_directory_exists,
    description="Ensures that the directory for the given file path exists."
)

def placeholder_write_file(path: str, content: str) -> bool:
    """Placeholder function for writing file content."""
    print(f"Placeholder: Writing {len(content)} chars (Obsidian format) to file {path}")
    # Simulate success
    return True

write_file_tool = FunctionTool(
    func=placeholder_write_file,
    description="Writes the given content to the specified file path."
)

def placeholder_format_obsidian_links(content: str, available_docs: list[str]) -> str:
    """Placeholder for formatting Obsidian links."""
    print("Placeholder: Formatting Obsidian links...")
    # Extremely basic placeholder: find potential file names and wrap them
    # Assumes available_docs contains filenames *without* extensions like ['file1', 'file2']
    available_docs_set = set(available_docs)
    def replace_link(match):
        potential_target = match.group(1)
        # Simple check if the potential target (without extension) exists
        if potential_target in available_docs_set:
            return f"[[{potential_target}]]"
        else:
            return match.group(0) # Keep original if target not found

    # Basic regex for something that might be a link target (improve significantly in real impl)
    # This looks for markdown links and tries to convert the text part if it matches a doc
    content_with_links = re.sub(r"\[([^\]]+)\]\([^\)]+\)", replace_link, content)
     # Also try to find bare words that match (less reliable)
    # content_with_links = re.sub(r"\b(" + "|".join(re.escape(doc) for doc in available_docs_set) + r")\b", r"[[\1]]", content_with_links)

    # Basic image embedding placeholder ![[image.png]]
    content_with_links = re.sub(r"!\[([^\]]*)\]\(([^\)]+\.(?:png|jpg|jpeg|gif|svg))\)", r"![[\2]]", content_with_links)

    return content_with_links

format_obsidian_links_tool = FunctionTool(
    func=placeholder_format_obsidian_links,
    description="Formats potential internal links in Markdown content to Obsidian's [[wikilink]] syntax based on a list of available document names (without extension). Also formats image links for embedding."
)
# --- End Placeholder Tools ---

# Define the LLM model
common_model = Gemini(model="gemini-1.5-flash-latest")

# Define the Agent
obsidian_writer_agent = LlmAgent(
    name="ObsidianWriterAgent",
    model=common_model,
    instruction="""Take the verified documentation content from 'draft_content'.
1. Format it specifically for Obsidian:
    - Use the 'placeholder_format_obsidian_links' tool to convert potential internal links (based on the 'documentation_plan' state, extracting just filenames without extension) to Obsidian's [[wikilink]] syntax. Handle image embedding syntax as well (![[image.png]]).
    - Ensure standard Markdown is otherwise preserved.
2. Get the target output file path from 'output_file_path'.
3. Ensure the directory for the output file exists using 'placeholder_ensure_directory_exists'.
4. Write the final Obsidian-formatted Markdown content to 'output_file_path' using 'placeholder_write_file'.
Output a status message indicating success or failure.""",
    tools=[ensure_directory_exists_tool, write_file_tool, format_obsidian_links_tool],
    output_key="obsidian_writing_status", # Key for the status message
    output_format="text",
    # Example input state:
    # {
    #   "draft_content": "# Module A\nLinks to [Module B](module_b.md).\n![Graph](viz/graph.svg)",
    #   "output_file_path": "obsidian_vault/Module A.md",
    #   "documentation_plan": [ # Used by the tool to know valid link targets
    #       {"source_file": "...", "output_file": "obsidian_vault/Module A.md", "status": "done"},
    #       {"source_file": "...", "output_file": "obsidian_vault/Module B.md", "status": "pending"}
    #    ],
    #    "visualization_result": {"generated_visualizations": ["obsidian_vault/viz/graph.svg"]}
    # }
    # Example available_docs for the tool (extracted from plan): ['Module A', 'Module B']
    # Example expected output:
    # { ..., "obsidian_writing_status": "Successfully wrote Obsidian-formatted Markdown to obsidian_vault/Module A.md" }
    # The content written by write_file would be "# Module A\nLinks to [[Module B]].\n![[viz/graph.svg]]"
)

print("ObsidianWriterAgent defined.")

# Example usage (for testing purposes)
async def _test_run():
    from google.adk.sessions import State
    from google.adk.artifacts import InMemoryArtifactService

    initial_state = State({
        "draft_content": "# Main App\n\nThis uses the [utils](utils.md) module. See the diagram: ![dep graph](visuals/app_deps.png)",
        "output_file_path": "my_vault/Main App.md",
        "documentation_plan": [
             {"source_file": "src/app.py", "output_file": "my_vault/Main App.md", "status": "..." },
             {"source_file": "src/utils.py", "output_file": "my_vault/utils.md", "status": "..." },
        ],
        "visualization_result": {"generated_visualizations": ["my_vault/visuals/app_deps.png"]},
         # Extract available docs for the tool:
         "available_docs": ["Main App", "utils"] # Pre-processed list for the tool
    })
    artifact_service = InMemoryArtifactService()

    # --- Simulate the state processing the orchestrator might do ---
    # The orchestrator needs to prepare the 'available_docs' list for the tool
    plan = initial_state.get("documentation_plan", [])
    available_docs_for_tool = []
    if plan:
         available_docs_for_tool = [
             os.path.splitext(os.path.basename(item['output_file']))[0]
             for item in plan if item.get('output_file')
         ]
    tool_input_state = State(initial_state)
    tool_input_state["available_docs"] = available_docs_for_tool # Add list needed by tool
    # --- End Simulation ---


    result_state = await obsidian_writer_agent.run(tool_input_state, artifact_service)
    print("Test run result state:", result_state)
    # Expected output contains 'obsidian_writing_status' message. Check logs for tool output.

if __name__ == "__main__":
    import asyncio
    # asyncio.run(_test_run())
    pass

