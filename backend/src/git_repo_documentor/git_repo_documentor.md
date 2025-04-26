# Git Repo Documentor - ADK Implementation Plan

This plan outlines the steps to create a multi-agent system using Google ADK for automatically documenting GitHub repositories iteratively and with verification.

## 1. Project Setup

-   [X] **Initialize Environment:**
    -   [X] Create a new project directory inside src (`git_repo_documentor`).
-   [X] **Install Dependencies:**
    -   [X] Install ADK: `poetry install google-adk`
    -   [X] Install Gemini client: `poetry install google-generativeai`
    -   [X] Install language-specific parsers (e.g., for Python): `poetry install astroid`
    -   [X] Install visualization libraries: `poetry install graphviz matplotlib`

-   [X] **Project Structure:**
    ```
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
    ```

## 2. Core Tools Implementation

*Comprehensive Tooling Approach:* Implementing robust and extensible tools is critical for the entire agent ecosystem. All tools will be implemented as custom `FunctionTool` wrappers to provide maximum control and flexibility.

-   [ ] **File System Tool (`tools/file_system.py`):**
    -   [ ] Implement functions for:
        -   `read_directory(path: str, recursive: bool = False) -> list[str]`
        -   `read_file_content(path: str) -> str`
        -   `write_file_content(path: str, content: str)`
        -   `ensure_directory_exists(path: str)`
    -   [ ] Implement error handling with retry mechanisms
    -   [X] Wrap these functions using `google.adk.tools.FunctionTool` (Placeholders created in `tools/__init__.py`)

-   [ ] **Code Parser Tool (`tools/code_parser.py`):**
    -   [ ] Design multilingual code parsing architecture
    -   [ ] Implement language-specific parsers for: Python (ast), JS/TS, Java, Go, etc.
    -   [ ] Implement unified function `parse_code(file_path: str, language: str = None) -> dict`
    -   [X] Wrap using `FunctionTool` (Placeholder created)
-   [ ] **Dependency Analyzer Tool (`tools/dependency_analyzer.py`):**
    -   [ ] Implement language-specific dependency analysis (requirements.txt, package.json, etc.)
    -   [ ] Create function to extract import statements
    -   [ ] Create function to build dependency graph
    -   [X] Wrap using `FunctionTool` (Placeholder created)
-   [ ] **Visualization Tool (`tools/visualization.py`):**
    -   [ ] Implement function to generate dependency graphs (Graphviz)
    -   [ ] Implement function to create class/module diagrams (Graphviz)
    -   [ ] Save visualizations as SVG/PNG
    -   [X] Wrap using `FunctionTool` (Placeholder created)
-   [ ] **Obsidian Linker Tool (`tools/obsidian_linker.py`):**
    -   [ ] Implement function `format_obsidian_links(content: str, available_docs: list[str]) -> str`
    -   [ ] Add support for embedding images `![[image.png]]`
    -   [X] Wrap using `FunctionTool` (Placeholder created)
-   [ ] **Web Search Tool (`tools/web_search.py`):**
    -   [ ] Implement function to search for external library docs (using APIs)
    -   [ ] Add caching
    -   [X] Wrap using `FunctionTool` (Placeholder created)
-   [ ] **Memory and Knowledge Graph Tools:**
    -   [ ] **Knowledge Graph Tool (`tools/knowledge_graph.py`):**
        -   [ ] Implement graph building and querying (e.g., NetworkX)
        -   [X] Wrap using `FunctionTool` (Placeholder created)
    -   [ ] **Memory Interaction Tool (`tools/memory_tools.py`):**
        -   [ ] Implement functions for storing/retrieving from `MemoryService`
        -   [ ] Implement semantic search capability
        -   [X] Wrap using `FunctionTool` (Placeholder created)
    -   [ ] **Fact Verification Tool (`tools/fact_verification.py`):**
        -   [ ] Implement code execution verification (link to Code Executor Tool)
        -   [ ] Implement claim extraction and validation logic
        -   [X] Wrap using `FunctionTool` (Placeholder created)
    -   [ ] **Code Executor Tool (`tools/code_executor.py`):**
        -   [ ] Implement **sandboxed** code execution (CRITICAL FOR SECURITY)
        -   [X] Wrap using `FunctionTool` (Placeholder created)

## 3. Agent Architecture Implementation

*Common Setup for LlmAgents:* (Used in agent files)
```python
from google.adk.agents import LlmAgent, BaseAgent
from google.adk.models import Gemini # Or your chosen LLM

common_model = Gemini(model="gemini-1.5-pro-latest") # Using the most capable model for complex tasks
# Using gemini-1.5-flash-latest in placeholders for speed/cost during dev
```

### 3.1 Planner Agents

-   [X] **File Identification Agent (`agents/planner/file_identification.py`):**
    -   [X] Define `FileIdentificationAgent(LlmAgent)` (Placeholder created)
-   [X] **Structure Designer Agent (`agents/planner/structure_designer.py`):**
    -   [X] Define `StructureDesignerAgent(LlmAgent)` (Placeholder created)

### 3.2 Processing Agents

-   [X] **Code Parser Agent (`agents/processing/code_parser.py`):**
    -   [X] Define `CodeParserAgent(LlmAgent)` (Placeholder created)
-   [X] **Code Interpreter Agent (`agents/processing/code_interpreter.py`):**
    -   [X] Define `CodeInterpreterAgent(LlmAgent)` (Placeholder created)
-   [X] **Dependency Analyzer Agent (`agents/processing/dependency_analyzer.py`):**
    -   [X] Define `DependencyAnalyzerAgent(LlmAgent)` (Placeholder created)
-   [X] **Testing Analyzer Agent (`agents/processing/testing_analyzer.py`):**
    -   [X] Define `TestingAnalyzerAgent(LlmAgent)` (Placeholder created)
-   [X] **Feature Extractor Agent (`agents/processing/feature_extractor.py`):**
    -   [X] Define `FeatureExtractorAgent(LlmAgent)` (Placeholder created)
-   [X] **Content Generator Agent (`agents/processing/content_generator.py`):**
    -   [X] Define `DocContentAgent(LlmAgent)` (Placeholder created)
-   [X] **Verifier Agent (`agents/processing/verifier.py`):**
    -   [X] Define `VerifierAgent(LlmAgent)` (Placeholder created)

### 3.3 Visualization Agents

-   [X] **Visualization Agent (`agents/visualization/visualizer.py`):**
    -   [X] Define `VisualizationAgent(LlmAgent)` (Placeholder created)

### 3.4 Writer Agents

-   [X] **Markdown Formatter Agent (`agents/writer/md_formatter.py`):**
    -   [X] Define `MarkdownFormatterAgent(LlmAgent)` (Placeholder created)
-   [X] **Obsidian Writer Agent (`agents/writer/obsidian_writer.py`):**
    -   [X] Define `ObsidianWriterAgent(LlmAgent)` (Placeholder created)
-   [X] **Summarizer Agent (`agents/writer/summarizer.py`):**
    -   [X] Define `SummarizerAgent(LlmAgent)` (Placeholder created)

### 3.5 Reliability Enhancement Agents

-   [X] **Fact-Checking Agent (`agents/processing/fact_checker.py`):**
    -   [X] Define `FactCheckingAgent(LlmAgent)` (Placeholder created)
-   [X] **Self-Reflection Agent (`agents/processing/self_reflection.py`):**
    -   [X] Define `SelfReflectionAgent(LlmAgent)` (Placeholder created, planner commented out)
-   [X] **Code Execution Verifier (`agents/processing/code_execution_verifier.py`):**
    -   [X] Define `CodeExecutionVerifierAgent(LlmAgent)` (Placeholder created)

## 4. Orchestration and Workflow Implementation

-   [X] **Design Custom Orchestrator (`agents/orchestrator.py`):**
    -   [X] Implement `OrchestratorAgent(BaseAgent)` structure (Implemented with placeholders)
    -   [X] Implement `run` method with Planning -> Loop -> Summary phases
    -   [X] Implement basic `_invoke_agent` helper with retry logic
    -   [X] Implement basic `_merge_states` helper

## 5. State Management and Data Flow

-   [X] **Comprehensive State Design:** (Keys defined conceptually in plan, used in agent placeholders)
-   [ ] **State Persistence:**
    -   [ ] Implement checkpointing (`services/checkpoint_service.py`)
    -   [ ] Design state serialization
-   [ ] **Long-Term Memory Integration:**
    -   [ ] **Multi-Layered Memory Architecture:**
        -   [X] Configure `MemoryService` (`services/memory_service.py`, `main.py` factory)
        -   [ ] Implement working memory usage in agents
        -   [ ] Implement knowledge base interactions (via Memory/KG agents/tools)
    -   [ ] **Knowledge Graph Integration:**
        -   [ ] Implement KG population and querying (via KG agent/tool)
    -   [ ] **Session-Based Learning:** (Advanced feature)

## 6. System Integration and Execution

-   [X] **Advanced Runner Configuration (`main.py`):**
    -   [X] Import necessary ADK components
    -   [X] Create service factories (`create_service_factory`)
    -   [X] Implement CLI (`argparse`)
    -   [X] Add support for in-memory services
    -   [ ] Add full support for persistent (Vertex) services (Placeholders exist)
    -   [X] Instantiate and connect orchestrator, agents, tools, services
    -   [X] Initialize state and run the `Runner`
    -   [X] Print summary output

## 7. Testing and Quality Assurance

-   [ ] **Comprehensive Testing Strategy:**
    -   [ ] Unit Tests (for tools, helpers)
    -   [ ] Agent Tests (`AgentEvaluator`)
    -   [ ] Integration Tests (agent interactions, state flow)
    -   [ ] End-to-End Tests (full repository documentation)
-   [ ] **Hallucination Prevention Tests:**
-   [ ] **Continuous Integration:**

## 8. Documentation Reliability Enhancement Strategies

-   [ ] **Factual Grounding Techniques:** (Partially addressed by Fact Checking/Verification agents)
-   [ ] **Hallucination Mitigation Approaches:** (Partially addressed by Fact Checking, Self-Reflection agents)
-   [ ] **Memory-Enhanced Documentation:** (Requires Memory/KG implementation)
