# This directory can hold prompt templates if needed,
# although instructions are often defined directly in LlmAgent.

# Example prompt file (e.g., prompts/summarize_code.prompt):
"""
Summarize the following {{language}} code:
```{{language}}
{{code_content}}
```
Focus on its main purpose and key components.
"""

# Agents would then reference these prompts if designed that way.
# Currently, the plan defines instructions directly in the agent definitions.
