# **App Name**: GitDocu

## Core Features:

- Repository Input: Allow users to input a Git repository URL.
- Documentation Trigger: Trigger the backend documentation process using the Google ADK based on the provided Git repository URL.
- Execution History: Display the progress and history of documentation executions for a given repository.

## Style Guidelines:

- Primary color: White or light grey for a clean background.
- Secondary color: Dark grey for text to ensure readability.
- Accent: Teal (#008080) to highlight interactive elements and progress indicators.
- Use a grid-based layout for consistent alignment and spacing.
- Simple, outline-style icons to represent different actions and statuses.

## Original User Request:
create single project 
one folder for backend and one for frontend -> use next, python, yarn and poetry

frontend will be simple a simple place to put a git repo url and check history, check progress of current execution etc etc

backend is a flask server with capablietues as given with google ADK 


Git Repo Documentor - ADK Implementation Plan
This plan outlines the steps to create a multi-agent system using Google ADK for automatically documenting GitHub repositories iteratively and with verification.

1. Project Setup
 Initialize Environment:

 Create a new project directory inside src (e.g., git_repo_documentor).
 Install Dependencies:

 Install ADK: poetry install google-adk
 Install Gemini client: poetry install google-generativeai (ADK often uses Gemini)
 Install language-specific parsers (e.g., for Python): poetry install astroid (or use built-in ast)
 Install visualization libraries: poetry install graphviz matplotlib
 Project Structure:

git_repo_documentor/
|---prompts/
├── agents/
│   ├── __init__.py
│   ├── orchestrator.py
│   ├── planner/
│   │   ├── __init__.py
│   │   ├── file_identification.py
│   │   └── structure_designer.py
│   ├── processing/
│   │   ├── __init__.py
│   │   ├── code_parser.py
│   │   ├── code_interpreter.py
│   │   ├── content_generator.py
│   │   ├── verifier.py
│   │   ├── dependency_analyzer.py
│   │   ├── testing_analyzer.py
│   │   ├── feature_extractor.py
│   │   ├── fact_checker.py
│   │   ├── self_reflection.py
│   │   └── code_execution_verifier.py
│   ├── visualization/
│   │   ├── __init__.py
│   │   └── visualizer.py
│   ├── writer/
│   │   ├── __init__.py
│   │   ├── md_formatter.py
│   │   ├── obsidian_writer.py
│   │   └── summarizer.py
│   └── memory/
│       ├── __init__.py
│       ├── memory_manager.py
│       └── knowledge_graph_manager.py
├── tools/
│   ├── __init__.py
│   ├── file_system.py
│   ├── code_parser.py
│   ├── dependency_analyzer.py
│   ├── obsidian_linker.py
│   ├── visualization.py
│   ├── web_search.py
│   ├── knowledge_graph.py
│   ├── memory_tools.py
│   ├── fact_verification.py
│   └── code_executor.py
├── services/
│   ├── __init__.py
│   ├── memory_service.py
│   └── checkpoint_service.py
├── main.py
├── git_repo_documentor.md # This file
2. Core Tools Implementation
Comprehensive Tooling Approach: Implementing robust and extensible tools is critical for the entire agent ecosystem. All tools will be implemented as custom FunctionTool wrappers to provide maximum control and flexibility.

 File System Tool (tools/file_system.py):
 Implement functions for:
read_directory(path: str, recursive: bool = False) -> list[str]
read_file_content(path: str) -> str
write_file_content(path: str, content: str)
ensure_directory_exists(path: str)
 Implement error handling with retry mechanisms
 Wrap these functions using google.adk.tools.FunctionTool:
# Example for one function
from google.adk.tools import FunctionTool
import os # Or pathlib

def read_file_content_impl(path: str) -> str:
    """Reads content from a file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file {path}: {e}"

read_file_tool = FunctionTool(
    func=read_file_content_impl,
    description="Reads the entire content of a specified file path."
)

# Create similar tools for write_file, ensure_dir, read_dir
 Code Parser Tool (tools/code_parser.py):
 Design multilingual code parsing architecture
 Implement language-specific parsers for:
Python (using ast module)
JavaScript/TypeScript (using appropriate parser)
Java (using appropriate parser)
Go (using appropriate parser)
Other languages as needed
 Implement unified function parse_code(file_path: str, language: str = None) -> dict:
Detects language from extension if not provided
Uses appropriate parser to extract structure (classes, functions, imports, docstrings)
Returns structured data (e.g., JSON serializable dictionary)
Handles errors gracefully with detailed diagnostics
 Wrap using FunctionTool
 Dependency Analyzer Tool (tools/dependency_analyzer.py):
 Implement language-specific dependency analysis:
Python (parse requirements.txt, setup.py, pyproject.toml)
JavaScript (parse package.json)
Other languages as appropriate
 Create function to extract import statements from code
 Create function to build dependency graph
 Wrap using FunctionTool
 Visualization Tool (tools/visualization.py):
 Implement function to generate dependency graphs
 Implement function to create class/module relationship diagrams
 Save visualizations as SVG/PNG for inclusion in documentation
 Wrap using FunctionTool
 Obsidian Linker Tool (tools/obsidian_linker.py):
 Implement function format_obsidian_links(content: str, available_docs: list[str]) -> str:
Takes Markdown content and a list of known generated document paths.
Uses regex or parsing to find potential internal links and formats them as [[filename_without_extension]] if the target exists in available_docs.
 Add support for embedding images and other Obsidian-specific features
 Wrap using FunctionTool
 Web Search Tool (tools/web_search.py):
 Implement function to search for documentation of external libraries
 Create wrappers for available web search APIs
 Add caching to avoid repeated queries
 Wrap using FunctionTool
 Memory and Knowledge Graph Tools:
 Knowledge Graph Tool (tools/knowledge_graph.py):
 Implement graph building and querying functionality
 Create functions for entity and relationship management
 Add visualization of knowledge graphs
 Wrap using FunctionTool
 Memory Interaction Tool (tools/memory_tools.py):
 Implement functions for storing and retrieving from memory
 Create semantic search capability for memory contents
 Add context-aware memory filtering
 Wrap using FunctionTool
 Fact Verification Tool (tools/fact_verification.py):
 Implement code execution verification for examples
 Create claim extraction and validation functions
 Add metrics-based factual grounding
 Wrap using FunctionTool
3. Agent Architecture Implementation
Common Setup for LlmAgents:

from google.adk.agents import LlmAgent, BaseAgent
from google.adk.models import Gemini # Or your chosen LLM

common_model = Gemini(model="gemini-1.5-pro-latest") # Using the most capable model for complex tasks
3.1 Planner Agents
 File Identification Agent (agents/planner/file_identification.py):
 Define FileIdentificationAgent(LlmAgent):
instruction: "Analyze the repository structure provided from 'repo_path' state. Identify primary code files suitable for documentation. Filter out test files, configuration files, and generated code unless explicitly requested."
tools: [read_directory_tool]
output_key: "identified_files"
 Structure Designer Agent (agents/planner/structure_designer.py):
 Define StructureDesignerAgent(LlmAgent):
instruction: "Given a list of identified files in 'identified_files', create a structured documentation plan. For each file, determine an appropriate output path within 'output_dir' based on logical organization. Create a JSON list with 'source_file', 'output_file', and 'status' ('pending') fields."
tools: []
output_key: "documentation_plan"
3.2 Processing Agents
 Code Parser Agent (agents/processing/code_parser.py):
 Define CodeParserAgent(LlmAgent):
instruction: "Parse the code file at 'current_file_path' using 'code_parser_tool'. Identify the programming language from the file extension."
tools: [read_file_tool, code_parser_tool]
output_key: "parsed_code"
 Code Interpreter Agent (agents/processing/code_interpreter.py):
 Define CodeInterpreterAgent(LlmAgent):
instruction: "Analyze the parsed code structure in 'parsed_code' for the file 'current_file_path'. Provide a concise summary of the file's purpose, its main components, and their roles."
tools: [read_file_tool] (for additional context if needed)
output_key: "code_interpretation"
 Dependency Analyzer Agent (agents/processing/dependency_analyzer.py):
 Define DependencyAnalyzerAgent(LlmAgent):
instruction: "Analyze the dependencies of the file at 'current_file_path'. Identify imported modules, external packages, and their relationships. Use 'web_search_tool' to gather information about external libraries if necessary."
tools: [read_file_tool, dependency_analyzer_tool, web_search_tool]
output_key: "dependency_analysis"
 Testing Analyzer Agent (agents/processing/testing_analyzer.py):
 Define TestingAnalyzerAgent(LlmAgent):
instruction: "Identify and analyze test files related to 'current_file_path'. Summarize the testing approach, test coverage, and key test cases."
tools: [read_directory_tool, read_file_tool]
output_key: "testing_analysis"
 Feature Extractor Agent (agents/processing/feature_extractor.py):
 Define FeatureExtractorAgent(LlmAgent):
instruction: "Extract key features, algorithms, and patterns from the file at 'current_file_path'. Identify design patterns, algorithms, and unique implementation details."
tools: [read_file_tool]
output_key: "feature_analysis"
 Content Generator Agent (agents/processing/content_generator.py):
 Define DocContentAgent(LlmAgent):
instruction: "Generate comprehensive documentation content based on the code analysis. Use 'code_interpretation', 'dependency_analysis', 'testing_analysis', and 'feature_analysis' to create detailed Markdown documentation. Include code snippets, explanations, and usage examples."
tools: []
output_key: "draft_content"
 Verifier Agent (agents/processing/verifier.py):
 Define VerifierAgent(LlmAgent):
instruction: "Verify the generated documentation against the source file and analysis results. Check for accuracy, completeness, and clarity. Verify code snippets, descriptions, and technical details. Implement style checks and link verification. Output a JSON object with 'status' and 'reason' fields."
tools: [read_file_tool]
output_key: "verification_result"
3.3 Visualization Agents
 Visualization Agent (agents/visualization/visualizer.py):
 Define VisualizationAgent(LlmAgent):
instruction: "Create visualizations for the documentation. Generate dependency graphs, class hierarchies, and component relationships based on the analysis. Save visualizations to the output directory for inclusion in the documentation."
tools: [visualization_tool, ensure_directory_exists_tool]
output_key: "visualization_result"
3.4 Writer Agents
 Markdown Formatter Agent (agents/writer/md_formatter.py):
 Define MarkdownFormatterAgent(LlmAgent):
instruction: "Format verified documentation content for standard Markdown. Ensure proper heading hierarchy, code formatting, and image links. Write the formatted content to the output file."
tools: [ensure_directory_exists_tool, write_file_tool]
output_key: "formatting_status"
 Obsidian Writer Agent (agents/writer/obsidian_writer.py):
 Define ObsidianWriterAgent(LlmAgent):
instruction: "Format the documentation for Obsidian. Convert internal links to Obsidian's link syntax, handle image embedding, and implement other Obsidian-specific features. Write the formatted content to the output file."
tools: [ensure_directory_exists_tool, write_file_tool, format_obsidian_links_tool]
output_key: "obsidian_writing_status"
 Summarizer Agent (agents/writer/summarizer.py):
 Define SummarizerAgent(LlmAgent):
instruction: "Generate a comprehensive summary document for the entire repository. Analyze all successfully documented files, create a high-level overview, and include links to individual documents. Generate a table of contents and introduction section."
tools: [read_file_tool, write_file_tool]
output_key: "summary_status"
3.5 Reliability Enhancement Agents
 Fact-Checking Agent (agents/processing/fact_checker.py):
 Define FactCheckingAgent(LlmAgent):
instruction: "Validate all factual claims in the generated documentation against the source code. Extract specific claims about functionality, structure, and behavior and verify each against the actual implementation. Flag any unsupported claims or potential hallucinations."
tools: [read_file_tool, fact_verification_tool]
output_key: "fact_check_result"
 Self-Reflection Agent (agents/processing/self_reflection.py):
 Define SelfReflectionAgent(LlmAgent):
instruction: "Review the generated documentation and reasoning process to identify potential logical errors, inconsistencies, or overreach in conclusions. Apply critical thinking to your own analysis, highlighting areas of uncertainty."
tools: []
planner: BuiltInPlanner(thinking_config=ThinkingConfig(enabled=True))
output_key: "self_reflection_result"
 Code Execution Verifier (agents/processing/code_execution_verifier.py):
 Define CodeExecutionVerifierAgent(LlmAgent):
instruction: "Extract code examples from the documentation and verify them by execution when possible. Test that the documented behavior matches actual execution results. Flag any discrepancies between documented and actual behavior."
tools: [code_executor_tool]
output_key: "code_verification_result"
4. Orchestration and Workflow Implementation
 Design Custom Orchestrator (agents/orchestrator.py):
 Implement a robust OrchestratorAgent as a custom class extending BaseAgent:
class OrchestratorAgent(BaseAgent):
    """Custom orchestrator agent with robust workflow management."""
    def __init__(self, sub_agents, tools):
        super().__init__(name="GitRepoDocumentorOrchestrator")
        self.sub_agents = sub_agents
        self.tools = tools
        # Additional initialization for loop control
    
    async def run(self, state, artifact_service):
        """Implement the complete documentation workflow with retry logic."""
        # 1. Planning Phase
        file_identification_result = await self._invoke_agent(
            self.sub_agents["file_identification"], state, artifact_service)
        structure_design_result = await self._invoke_agent(
            self.sub_agents["structure_designer"], file_identification_result, artifact_service)
        
        # 2. Documentation Loop with retries and error handling
        documentation_plan = structure_design_result.state.get("documentation_plan", [])
        for item in documentation_plan:
            # Track state for this iteration
            iteration_state = State(structure_design_result.state)
            iteration_state.update({"current_file_path": item["source_file"]})
            
            # Processing pipeline with robust error handling and retries
            try:
                # Code Analysis
                parsed_code_result = await self._invoke_agent(
                    self.sub_agents["code_parser"], iteration_state, artifact_service)
                
                interpretation_result = await self._invoke_agent(
                    self.sub_agents["code_interpreter"], parsed_code_result, artifact_service)
                
                # Parallel specialized analysis
                dependency_result, testing_result, feature_result = await asyncio.gather(
                    self._invoke_agent(self.sub_agents["dependency_analyzer"], 
                                      interpretation_result, artifact_service),
                    self._invoke_agent(self.sub_agents["testing_analyzer"], 
                                      interpretation_result, artifact_service),
                    self._invoke_agent(self.sub_agents["feature_extractor"], 
                                      interpretation_result, artifact_service)
                )
                
                # Combine all analysis results
                combined_state = self._merge_states(
                    interpretation_result, dependency_result, testing_result, feature_result)
                
                # Generate content and visualizations in parallel
                content_result, visualization_result = await asyncio.gather(
                    self._invoke_agent(self.sub_agents["content_generator"], 
                                      combined_state, artifact_service),
                    self._invoke_agent(self.sub_agents["visualizer"], 
                                      combined_state, artifact_service)
                )
                
                # Verification
                verification_state = content_result
                verification_state.update({"visualization_result": visualization_result.state.get("visualization_result")})
                verification_result = await self._invoke_agent(
                    self.sub_agents["verifier"], verification_state, artifact_service)
                
                # Handle verification result
                verification_status = verification_result.state.get("verification_result", {}).get("status")
                if verification_status == "pass":
                    # Write documentation
                    if verification_result.state.get("use_obsidian_format", False):
                        await self._invoke_agent(self.sub_agents["obsidian_writer"], 
                                               verification_result, artifact_service)
                    else:
                        await self._invoke_agent(self.sub_agents["md_formatter"], 
                                               verification_result, artifact_service)
                    item["status"] = "done"
                else:
                    # Store failure reason and continue
                    item["status"] = "failed"
                    item["reason"] = verification_result.state.get("verification_result", {}).get("reason", "Unknown error")
                    
            except Exception as e:
                # Handle exceptions, log details, and continue to next file
                item["status"] = "failed"
                item["reason"] = f"Exception: {str(e)}"
        
        # 3. Summary generation
        final_state = structure_design_result
        final_state.update({"documentation_plan": documentation_plan})
        summary_result = await self._invoke_agent(
            self.sub_agents["summarizer"], final_state, artifact_service)
        
        return summary_result
        
    # Helper methods for agent invocation, state merging, etc.
    async def _invoke_agent(self, agent, state, artifact_service):
        """Invoke an agent with retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return await agent.run(state, artifact_service)
            except Exception as e:
                if attempt < max_retries - 1:
                    # Log retry and continue
                    pass
                else:
                    # Log failure and re-raise
                    raise
                    
    def _merge_states(self, *states):
        """Merge multiple states into one."""
        # Implementation...
5. State Management and Data Flow
 Comprehensive State Design:
 Define core state keys:
state['repo_path']: Input repository path
state['output_dir']: Target directory for docs
state['use_obsidian_format']: Boolean config
 Define planning state:
state['identified_files']: List of files to document
state['documentation_plan']: Structured plan with file mappings and status
 Define per-file processing state:
state['current_file_path']: Current file being processed
state['parsed_code']: Raw parsed structure
state['code_interpretation']: High-level code understanding
state['dependency_analysis']: Dependency information
state['testing_analysis']: Test coverage and approach
state['feature_analysis']: Key features and patterns
state['draft_content']: Generated documentation content
state['verification_result']: Verification status and feedback
state['visualization_result']: Generated visualizations
 Define output state:
state['formatting_status']: Standard Markdown output status
state['obsidian_writing_status']: Obsidian-specific output status
state['summary_status']: Overall summary generation status
 State Persistence:
 Implement checkpointing to allow resuming documentation process
 Design state serialization for persistent storage
 Long-Term Memory Integration:
 Multi-Layered Memory Architecture:
 Configure MemoryService for long-term knowledge storage
 Implement working memory for session-specific context
 Create documentation knowledge base for cross-file awareness
 Design memory lifecycle management with ingestion, scoring, and decay
 Knowledge Graph Integration:
 Maintain relationship graph of code entities and documentation
 Enable traversal of code relationships for context-aware documentation
 Integrate graph-based memory with semantic search capabilities
 Session-Based Learning:
 Store successful documentation patterns for future reference
 Implement continuous improvement through feedback loops
 Create documentation quality metrics based on verification results
6. System Integration and Execution
 Advanced Runner Configuration (main.py):
 Import necessary ADK components
 Create service factories for memory, sessions, and artifacts
 Implement CLI with rich configuration options
 Add support for both in-memory and persistent services
# main.py
import asyncio
import argparse
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService, State
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory import InMemoryMemoryService
# For production:
# from google.adk.sessions import VertexAiSessionService
# from google.adk.artifacts import GcsArtifactService
# from google.adk.memory import VertexAiRagMemoryService
from agents.orchestrator import OrchestratorAgent
# Import all sub-agents
import sys
import os

def create_service_factory(service_type, **kwargs):
    """Create appropriate service based on configuration."""
    if service_type == "memory":
        return InMemorySessionService(), InMemoryArtifactService(), InMemoryMemoryService()
    elif service_type == "vertex":
        # Production services with persistent storage
        return (VertexAiSessionService(kwargs.get("project_id"), kwargs.get("location")),
               GcsArtifactService(kwargs.get("bucket_name")),
               VertexAiRagMemoryService(kwargs.get("project_id"), kwargs.get("location")))
    else:
        raise ValueError(f"Unknown service type: {service_type}")

async def main(args):
    """Main entry point with comprehensive configuration."""
    # Create services based on configuration
    session_service, artifact_service, memory_service = create_service_factory(
        args.service_type,
        project_id=args.project_id,
        location=args.location,
        bucket_name=args.bucket_name
    )

    # Ensure output directory exists
    abs_output_dir = os.path.abspath(args.output_dir)
    os.makedirs(abs_output_dir, exist_ok=True)

    # Instantiate all agents
    # (Code to initialize all sub-agents)
    
    # Initialize orchestrator with all sub-agents
    orchestrator = OrchestratorAgent(
        sub_agents={
            "file_identification": file_identification_agent,
            "structure_designer": structure_designer_agent,
            # Include all other agents
        },
        tools=[
            # Include all tools
        ]
    )

    # Create runner with memory service
    runner = Runner(
        agent=orchestrator,
        session_service=session_service,
        artifact_service=artifact_service,
        memory_service=memory_service,  # Add memory service
        app_name="GitRepoDocumentor",
    )

    # Initialize state
    initial_state = State()
    initial_state.update({
        "repo_path": os.path.abspath(args.repo_path),
        "output_dir": abs_output_dir,
        "use_obsidian_format": args.obsidian_format,
        "verbose_logging": args.verbose
    })

    # Run documentation process
    print(f"Starting documentation for repository: {args.repo_path}")
    print(f"Output will be generated in: {abs_output_dir}")
    final_event = await runner.run(initial_state=initial_state)

    # Print summary information
    print("\nDocumentation process completed.")
    final_plan = final_event.state.get('documentation_plan', [])
    print("\nFinal Documentation Plan Status:")
    success_count = 0
    fail_count = 0
    pending_count = 0
    for item in final_plan:
        print(f"- {item['source_file']} -> {item['output_file']} : {item['status']}")
        if item['status'] == 'done':
            success_count += 1
        elif item['status'] == 'failed':
            fail_count += 1
            print(f"  Reason: {item.get('reason', 'N/A')}")
        else:
            pending_count +=1

    print(f"\nSummary: {success_count} succeeded, {fail_count} failed, {pending_count} pending/skipped.")
    summary_status = final_event.state.get('summary_status')
    if summary_status:
         print(f"Overall summary generation status: {summary_status}")
    else:
         print("Overall summary agent did not run or report status.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Document a GitHub repository using ADK")
    parser.add_argument("repo_path", help="Path to the repository to document")
    parser.add_argument("--output-dir", default="docs", help="Output directory for documentation")
    parser.add_argument("--obsidian-format", action="store_true", help="Generate Obsidian-compatible markdown")
    parser.add_argument("--service-type", choices=["memory", "vertex"], default="memory", 
                      help="Type of services to use (in-memory or Vertex AI)")
    parser.add_argument("--project-id", help="GCP project ID (for Vertex AI services)")
    parser.add_argument("--location", default="us-central1", help="GCP location (for Vertex AI services)")
    parser.add_argument("--bucket-name", help="GCS bucket name (for persistent artifacts)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.service_type == "vertex" and (not args.project_id or not args.bucket_name):
        parser.error("--project-id and --bucket-name are required when using Vertex AI services")
        
    if not os.path.isdir(args.repo_path):
        print(f"Error: Repository path not found: {args.repo_path}")
        sys.exit(1)

    asyncio.run(main(args))
7. Testing and Quality Assurance
 Comprehensive Testing Strategy:
 Unit Tests:
 Test all tool functions with robust test cases
 Test language-specific code parsers with various input files
 Test dependency analysis tools with different project structures
 Test visualization generation with controlled inputs
 Agent Tests:
 Create google.adk.evaluation.AgentEvaluator test suite
 Generate test fixtures for each agent type
 Test specialized analysis agents with diverse code samples
 Validate writer agents with different output formats
 Integration Tests:
 Test parallel execution of analysis agents
 Verify state consistency across the pipeline
 Test error handling and recovery mechanisms
 Validate visualization integration in documentation
 End-to-End Tests:
 Test with repositories of different languages
 Test with repositories of varying sizes and complexities
 Validate Obsidian-specific features
 Test with repositories containing errors or unusual structures
 Benchmark performance and resource utilization
 Hallucination Prevention Tests:
 Develop benchmark suites for hallucination detection
 Test fact checking mechanisms across diverse code bases
 Validate memory retrieval for accuracy and relevance
 Measure grounding metrics for generated documentation
 Continuous Integration:
 Set up CI pipeline for automated testing
 Configure code quality checks
 Implement performance benchmarking
8. Documentation Reliability Enhancement Strategies
 Factual Grounding Techniques:
 Code-Based Evidence: Implement traceability between documentation claims and source code
 Metrics-Driven Validation: Add quantitative metrics to documentation (lines of code, function counts, etc.)
 Example Execution: Validate code examples through automated execution
 Source Linking: Add direct links/references to source code for all documented functionality
 Hallucination Mitigation Approaches:
 Claim Extraction and Verification: Systematically identify and verify factual claims
 Uncertainty Flagging: Explicitly mark areas of low confidence or incomplete information
 Multi-Stage Verification: Apply multiple verification stages with different techniques
 Self-Contradiction Detection: Check for logical inconsistencies within the generated content
 Memory-Enhanced Documentation:
 Cross-File Context: Maintain awareness of related components documented elsewhere
 Pattern Recognition: Identify and reuse successful documentation patterns
 Documentation Evolution: Track changes in code and documentation over time
 Collective Intelligence: Learn from successful documentation of similar components
  