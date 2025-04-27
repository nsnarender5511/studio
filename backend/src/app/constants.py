# Define constants and enumerations for the application

from enum import Enum


class JobStatus(str, Enum):
    PENDING = "PENDING"
    STARTED = "STARTED"
    PROGRESS = "PROGRESS"
    COMPLETED = "COMPLETED" # Changed from Completed
    FAILED = "FAILED"       # Changed from Failed
    # TODO: Add other statuses if used (e.g., CANCELED)


class AdkStages(str, Enum):
    SERVICE_CREATION = "service_creation"
    AGENT_TOOL_SETUP = "agent_tool_setup"
    RUNNER_CREATION = "runner_creation"
    INITIAL_STATE_CREATION = "initial_state_creation"
    ADK_RUNNER_EXECUTION = "adk_runner_execution"
    RESULT_PROCESSING = "result_processing"
    # TODO: Add other relevant stages


class AgentKeys(str, Enum):
    # Based on current placeholder agents
    FILE_IDENTIFICATION = "file_identification"
    STRUCTURE_DESIGNER = "structure_designer"
    CODE_PARSER = "code_parser"
    CODE_INTERPRETER = "code_interpreter"
    DEPENDENCY_ANALYZER = "dependency_analyzer"
    TESTING_ANALYZER = "testing_analyzer"
    FEATURE_EXTRACTOR = "feature_extractor"
    CONTENT_GENERATOR = "content_generator"
    VERIFIER = "verifier"
    VISUALIZER = "visualizer"
    MD_FORMATTER = "md_formatter"
    OBSIDIAN_WRITER = "obsidian_writer"
    SUMMARIZER = "summarizer"
    FACT_CHECKER = "fact_checker"
    SELF_REFLECTION = "self_reflection"
    CODE_EXECUTION_VERIFIER = "code_execution_verifier"
    # TODO: Add keys for any future agents


# Add other constants as needed, e.g., for configuration keys, etc. 