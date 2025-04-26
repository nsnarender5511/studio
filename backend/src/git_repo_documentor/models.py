from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import json

# Initialize SQLAlchemy without the app object
db = SQLAlchemy()

# --- Database Model ---
class JobHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(36), unique=True, nullable=False, index=True)
    repo_url = db.Column(db.String, nullable=False)
    request_time = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    end_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50), nullable=False, index=True)
    details = db.Column(db.Text, nullable=True)
    error_info_json = db.Column(db.Text, nullable=True) # Store error dict as JSON string

    def to_dict(self):
        error_info = None
        if self.error_info_json:
            try:
                error_info = json.loads(self.error_info_json)
            except json.JSONDecodeError:
                error_info = {"error": "Failed to parse stored error info"}

        return {
            "id": self.id,
            "job_id": self.job_id,
            "repo_url": self.repo_url,
            "request_time": self.request_time.isoformat() if self.request_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status,
            "details": self.details,
            "error_info": error_info
        } 