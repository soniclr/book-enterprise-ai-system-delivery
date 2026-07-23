"""Idempotent workflow and human approval example."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class Status(str, Enum):
    AWAITING_APPROVAL = "awaiting_approval"
    EXECUTED = "executed"
    OUTCOME_UNKNOWN = "outcome_unknown"
    FAILED = "failed"


class IdempotencyConflict(ValueError):
    """The same idempotency key was reused for a different business intent."""


class ApprovalMismatch(ValueError):
    """The approval does not bind to the prepared object and content version."""


class OutcomeUnknown(RuntimeError):
    """The external side effect may have happened and must be reconciled."""


@dataclass(frozen=True)
class ApprovalContext:
    approver: str
    business_object_id: str
    content_version: str


@dataclass
class Task:
    task_id: str
    idempotency_key: str
    payload: dict[str, Any]
    payload_digest: str
    status: Status = Status.AWAITING_APPROVAL
    approver: str | None = None
    result: dict[str, Any] | None = None
    events: list[str] = field(default_factory=list)


class WorkflowStore:
    def __init__(self) -> None:
        self._by_key: dict[str, Task] = {}

    def get(self, idempotency_key: str) -> Task:
        return self._by_key[idempotency_key]

    @staticmethod
    def _payload_digest(payload: dict[str, Any]) -> str:
        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    def prepare(
        self,
        task_id: str,
        idempotency_key: str,
        payload: dict[str, Any],
    ) -> Task:
        payload_digest = self._payload_digest(payload)
        existing = self._by_key.get(idempotency_key)
        if existing is not None:
            if existing.payload_digest != payload_digest:
                raise IdempotencyConflict(
                    f"idempotency key {idempotency_key!r} has a different payload"
                )
            return existing
        task = Task(
            task_id=task_id,
            idempotency_key=idempotency_key,
            payload=payload,
            payload_digest=payload_digest,
        )
        task.events.append("prepared")
        self._by_key[idempotency_key] = task
        return task

    def approve_and_execute(
        self,
        idempotency_key: str,
        approval: ApprovalContext,
        action: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> Task:
        task = self._by_key[idempotency_key]
        if task.status == Status.EXECUTED:
            return task
        if task.status == Status.OUTCOME_UNKNOWN:
            raise OutcomeUnknown("reconcile the business postcondition before retrying")
        if not approval.approver.strip():
            raise ValueError("An accountable approver is required")
        if (
            approval.business_object_id != task.payload.get("business_object_id")
            or approval.content_version != task.payload.get("content_version")
        ):
            raise ApprovalMismatch(
                "approval must bind to the prepared business object and content version"
            )

        task.approver = approval.approver
        task.events.append(
            f"approved:{approval.approver}:{approval.content_version}"
        )
        try:
            task.result = action(task.payload)
            task.status = Status.EXECUTED
            task.events.append("executed")
        except OutcomeUnknown:
            task.status = Status.OUTCOME_UNKNOWN
            task.events.append("outcome_unknown")
            raise
        except Exception as exc:
            task.status = Status.FAILED
            task.events.append(f"failed:{type(exc).__name__}")
            raise
        return task

    def reconcile(
        self,
        idempotency_key: str,
        read_postcondition: Callable[[dict[str, Any]], dict[str, Any] | None],
    ) -> Task:
        """Resolve an unknown outcome by reading the authoritative system."""

        task = self._by_key[idempotency_key]
        if task.status != Status.OUTCOME_UNKNOWN:
            raise ValueError("only an outcome_unknown task can be reconciled")
        result = read_postcondition(task.payload)
        if result is not None:
            task.result = result
            task.status = Status.EXECUTED
            task.events.append("reconciled:postcondition_satisfied")
        else:
            task.status = Status.FAILED
            task.events.append("reconciled:postcondition_absent")
        return task
