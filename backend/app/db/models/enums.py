"""Domain enums shared across Noesis ORM models.

Stored as VARCHAR (``native_enum=False`` at the column site) for portability
between PostgreSQL and the SQLite database used in tests.
"""

from __future__ import annotations

import enum


class WorkspaceDomain(str, enum.Enum):
    RA_SEVERITY = "ra_severity"
    PATENT = "patent"
    MULTIMODAL_AI = "multimodal_ai"
    VLM = "vlm"
    CUSTOM = "custom"


class PaperSource(str, enum.Enum):
    ARXIV = "arxiv"
    SEMANTIC_SCHOLAR = "semantic_scholar"
    OPENALEX = "openalex"
    PATENT = "patent"
    UPLOAD = "upload"
    WEB = "web"


class QuestionStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    ANSWERED = "answered"


class ExperimentStatus(str, enum.Enum):
    PLANNED = "planned"
    RUNNING = "running"
    DONE = "done"
    ABANDONED = "abandoned"


class GapStatus(str, enum.Enum):
    OPEN = "open"
    ADDRESSED = "addressed"


class InquiryType(str, enum.Enum):
    LITERATURE_REVIEW = "literature_review"
    GAP_ANALYSIS = "gap_analysis"
    PRIOR_ART = "prior_art"
    EXPERIMENT_DESIGN = "experiment_design"
    METHODOLOGY = "methodology"
    FACTUAL = "factual"


class InquiryStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    CRITIC_FAILED = "critic_failed"
    FAILED = "failed"


class TimelineEventType(str, enum.Enum):
    PAPER_ANALYZED = "paper_analyzed"
    REVIEW_GENERATED = "review_generated"
    GAP_DISCOVERED = "gap_discovered"
    EXPERIMENT_PLANNED = "experiment_planned"
    NOTE_ADDED = "note_added"
    QUESTION_ADDED = "question_added"
    INQUIRY_RUN = "inquiry_run"
    IDEA_CAPTURED = "idea_captured"


class MemoryKind(str, enum.Enum):
    PAPER_SUMMARY = "paper_summary"
    REVIEW = "review"
    GAP = "gap"
    EXPERIMENT = "experiment"
    NOTE = "note"
    SESSION_SUMMARY = "session_summary"
