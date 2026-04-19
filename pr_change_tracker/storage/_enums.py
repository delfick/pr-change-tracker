from __future__ import annotations

import enum


class PullRequestStatus(enum.StrEnum):
    MERGED = "merged"
    CLOSED = "closed"
    DRAFT = "draft"
    READY_FOR_REVIEW = "ready_for_review"


class ReviewState(enum.StrEnum):
    DISMISSED = "dismissed"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
