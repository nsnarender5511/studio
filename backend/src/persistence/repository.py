import logging
import json
from contextlib import contextmanager
from sqlalchemy.orm import Session, sessionmaker
from typing import Optional, List, Generator, Any
from datetime import datetime, timezone

from src.app.models import JobHistory
from src.app.constants import JobStatus
from src.exceptions import HistoryUpdateError

logger = logging.getLogger(__name__)

class JobHistoryRepository:
    def __init__(self, session_factory: sessionmaker[Session]):
        self._session_factory = session_factory

    @contextmanager
    def _session_scope(self) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations."""
        session = self._session_factory()
        logger.debug("Repository: Acquired DB session.")
        try:
            yield session
            session.commit()
            logger.debug("Repository: DB session committed.")
        except Exception as e:
            logger.error(f"Repository: DB session error: {e}", exc_info=True)
            session.rollback()
            logger.warning("Repository: DB session rolled back.")
            raise HistoryUpdateError(f"Database operation failed: {e}") from e
        finally:
            session.close()
            logger.debug("Repository: DB session closed.")

    def add_initial(self, job_id: str, repo_url: str) -> JobHistory:
        with self._session_scope() as session:
            existing = session.query(JobHistory).filter(JobHistory.job_id == job_id).first()
            if existing:
                logger.warning(f"Job {job_id}: Initial record already exists.")
                return existing

            history_entry = JobHistory(
                job_id=job_id,
                repo_url=repo_url,
                status=JobStatus.PENDING.value
            )
            session.add(history_entry)
            session.flush() # Assign ID
            logger.info(f"Job {job_id}: Created initial history record with ID {history_entry.id}.")
            # Expunge the object from the session before returning
            session.expunge(history_entry)
            logger.debug(f"Job {job_id}: Expunged history entry from session before returning.")
            return history_entry

    def update_final_status(self, job_id: str, status: JobStatus, end_time: datetime, details: Optional[str] = None, error_info: Optional[dict] = None) -> Optional[JobHistory]:
        with self._session_scope() as session:
            job_record = session.query(JobHistory).filter(JobHistory.job_id == job_id).first()
            if job_record:
                job_record.status = status.value
                job_record.end_time = end_time
                job_record.details = details
                if error_info:
                    try:
                        job_record.error_info_json = json.dumps(error_info)
                    except TypeError as e:
                        logger.error(f"Job {job_id}: Failed to serialize error_info to JSON: {e}")
                        job_record.error_info_json = json.dumps({"error": "Failed to serialize error details"})
                else:
                    job_record.error_info_json = None
                logger.info(f"Job {job_id}: Updated history record status to '{status.value}'.")
                return job_record
            else:
                logger.warning(f"Job {job_id}: Could not find history record to update final status.")
                return None

    def get_by_job_id(self, job_id: str) -> Optional[JobHistory]:
         with self._session_scope() as session:
             job = session.query(JobHistory).filter(JobHistory.job_id == job_id).first()
             return job

    def get_all_history(self, limit: int = 100) -> List[JobHistory]:
         with self._session_scope() as session:
             jobs = session.query(JobHistory).order_by(JobHistory.request_time.desc()).limit(limit).all()
             return jobs

    # Optional: Add delete method if needed for rollback in jobs_api
    def delete_by_job_id(self, job_id: str) -> bool:
        with self._session_scope() as session:
            job_record = session.query(JobHistory).filter(JobHistory.job_id == job_id).first()
            if job_record:
                session.delete(job_record)
                logger.info(f"Job {job_id}: Deleted history record.")
                return True
            else:
                logger.warning(f"Job {job_id}: Could not find history record to delete.")
                return False 