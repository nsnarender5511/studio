from google.adk.agents import LlmAgent
from google.adk.models import Gemini # Or your chosen LLM

# Define the LLM model
common_model = Gemini(model="gemini-1.5-pro-latest") # Use Pro for potentially better generation

# Define the Agent
content_generator_agent = LlmAgent(
    name="DocContentAgent",
    model=common_model,
    instruction="Generate comprehensive documentation content in Markdown format based on the analysis provided in the state. Use the 'code_interpretation', 'dependency_analysis', 'testing_analysis', and 'feature_analysis' state variables for the file 'current_file_path'. Create detailed documentation including: \n1. A summary section based on 'code_interpretation'.\n2. A section detailing key functions/classes/components identified in 'feature_analysis' and 'code_interpretation', explaining their purpose and usage.\n3. Include relevant code snippets from the original file (you don't have direct access, describe what snippet would be relevant based on analysis). \n4. A dependencies section summarizing 'dependency_analysis'.\n5. A testing section summarizing 'testing_analysis'. \nStructure the output clearly using Markdown headings and formatting.",
    tools=[], # No external tools needed as per plan
    output_key="draft_content", # Key for the generated Markdown
    output_format="markdown", # Explicitly request Markdown output
    # Example input state:
    # {
    #   "current_file_path": "src/app.py",
    #   "code_interpretation": "This file starts the server.",
    #   "dependency_analysis": "Imports 'flask'. External: Flask.",
    #   "testing_analysis": "Uses pytest. Tests cover main function.",
    #   "feature_analysis": "Key function: main(). Uses run_server().",
    #   "parsed_code": { ... } // May or may not be directly used by LLM based on instruction
    # }
    # Example expected output in state:
    # { ..., "draft_content": "# src/app.py\n\n## Summary\nThis file starts the server.\n\n## Key Components\n### `main()`\nPurpose...\n\n## Dependencies\nImports 'flask'...\n\n## Testing\nUses pytest..." }
)

print("DocContentAgent defined.")

# Example usage (for testing purposes)
async def _test_run():
    from google.adk.sessions import State
    from google.adk.artifacts import InMemoryArtifactService

    initial_state = State({
        "current_file_path": "/path/to/repo/src/utils.py",
        "code_interpretation": "Provides utility functions for string manipulation.",
        "dependency_analysis": "No external dependencies. Imports 're'.",
        "testing_analysis": "Unit tests exist in tests/test_utils.py covering all functions.",
        "feature_analysis": "Key functions: format_name(), clean_text(). Uses regex.",
        "parsed_code": { # Example parsed code structure
            "language": "python",
            "functions": [
                {"name": "format_name", "params": ["name"], "docstring": "Formats a name."},
                {"name": "clean_text", "params": ["text"], "docstring": "Cleans text using regex."}
            ],
            "imports": ["re"]
        }
        # Other state variables
    })
    artifact_service = InMemoryArtifactService()
    result_state = await content_generator_agent.run(initial_state, artifact_service)
    print("Test run result state:", result_state)
    # Expected output contains 'draft_content' with Markdown

if __name__ == "__main__":
    import asyncio
    # asyncio.run(_test_run())
    pass
