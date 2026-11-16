from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

SEVERITIES = ("info", "low", "medium", "high")
SEVERITY_RANK = {name: i for i, name in enumerate(SEVERITIES)}


@dataclass
class Finding:
    id: str
    title: str
    severity: str
    confidence: str
    description: str
    evidence: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    category: str = "general"
    next_steps: list[str] = field(default_factory=list)
    attack: list[str] = field(default_factory=list)


@dataclass
class AnalysisReport:
    tool: str
    version: str
    profile: str
    target: str
    analyzed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    file: dict[str, Any] = field(default_factory=dict)
    findings: list[Finding] = field(default_factory=list)
    modules: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    schema_version: str = "2"
    summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
