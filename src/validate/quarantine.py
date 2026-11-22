"""
Quarantine and Audit Logging for Data Quality and Integration Issues
"""
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from config.settings import QUARANTINE_DATA_DIR
from src.validate.issues import IntegrationIssueRecord
from src.utils.logger import logger

class QuarantineManager:
    """Manages recording, persisting, and reporting quarantined and resolved records."""

    def __init__(self, output_dir: Path = QUARANTINE_DATA_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.audit_log: List[IntegrationIssueRecord] = []

    def record_issue(self, issue: IntegrationIssueRecord) -> None:
        """Add an issue record to the audit log."""
        self.audit_log.append(issue)

    def persist_log(self, filename: str = "quarantine_audit_log.json") -> Path:
        """Persist all recorded issues to disk as structured JSON."""
        log_path = self.output_dir / filename
        data = [asdict(record) for record in self.audit_log]
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "generated_at": datetime.utcnow().isoformat(),
                    "total_issues_handled": len(self.audit_log),
                    "summary_by_issue_code": self.get_summary_by_code(),
                    "records": data
                },
                f,
                indent=2
            )
        logger.info(f"Persisted quarantine audit log ({len(self.audit_log)} events) to {log_path}")
        return log_path

    def get_summary_by_code(self) -> Dict[str, int]:
        """Return counts of handled issues grouped by issue code."""
        counts: Dict[str, int] = {}
        for item in self.audit_log:
            code = item.issue_code.value if hasattr(item.issue_code, "value") else str(item.issue_code)
            counts[code] = counts.get(code, 0) + 1
        return counts

    def clear(self) -> None:
        """Clear recorded logs in memory."""
        self.audit_log.clear()
