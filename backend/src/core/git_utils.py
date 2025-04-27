import git
import logging
import shutil

# Assuming exceptions are defined in src/exceptions.py
from src.exceptions import CloningError

logger = logging.getLogger(__name__)

def clone_repo(repo_url: str, target_dir: str) -> None:
    """Clones a Git repository to the specified target directory.
    Raises CloningError if the cloning process fails.
    """
    if not repo_url or not target_dir:
        raise CloningError("Repository URL and target directory must be provided.")
    try:
        logger.info(f"Cloning {repo_url} into {target_dir}")
        git.Repo.clone_from(repo_url, target_dir, depth=1) # Shallow clone for speed
        logger.info(f"Cloning successful for {repo_url}.")
    except git.GitCommandError as e:
        error_detail = str(e.stderr) if e.stderr else str(e)
        logger.error(f"Git clone failed for {repo_url}. Error: {error_detail}", exc_info=True)
        # Attempt cleanup before raising
        shutil.rmtree(target_dir, ignore_errors=True)
        raise CloningError(f"Failed to clone repository {repo_url}: {error_detail}") from e
    except Exception as e: # Catch other potential errors during clone setup
        logger.error(f"Error during git clone setup for {repo_url}: {e}", exc_info=True)
        shutil.rmtree(target_dir, ignore_errors=True)
        raise CloningError(f"Server error during repository cloning for {repo_url}: {e}") from e 