"""Permission-aware retrieval example using simple lexical scoring."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class UserContext:
    user_id: str
    department: str
    project_ids: frozenset[str] = frozenset()


@dataclass(frozen=True)
class Document:
    doc_id: str
    title: str
    text: str
    visibility: str = "internal"  # public, internal, department, project, user
    departments: frozenset[str] = frozenset()
    project_ids: frozenset[str] = frozenset()
    user_ids: frozenset[str] = frozenset()
    effective: bool = True


@dataclass(frozen=True)
class Citation:
    doc_id: str
    title: str
    excerpt: str
    score: int


def is_authorized(user: UserContext, document: Document) -> bool:
    if not document.effective:
        return False
    if document.visibility in {"public", "internal"}:
        return True
    if document.visibility == "department":
        return user.department in document.departments
    if document.visibility == "project":
        return bool(user.project_ids & document.project_ids)
    if document.visibility == "user":
        return user.user_id in document.user_ids
    return False


def _tokens(text: str) -> set[str]:
    lowered = text.lower()
    words = set(re.findall(r"[a-z0-9_]+", lowered))
    cjk = "".join(re.findall(r"[\u4e00-\u9fff]", lowered))
    words.update(cjk[index : index + 2] for index in range(max(0, len(cjk) - 1)))
    return {token for token in words if token}


def retrieve(
    query: str,
    user: UserContext,
    documents: list[Document],
    limit: int = 3,
) -> list[Citation]:
    """Filter by authorization before scoring and returning citations."""

    query_tokens = _tokens(query)
    scored: list[Citation] = []
    for document in documents:
        if not is_authorized(user, document):
            continue
        score = len(query_tokens & _tokens(f"{document.title} {document.text}"))
        if score == 0:
            continue
        scored.append(
            Citation(
                doc_id=document.doc_id,
                title=document.title,
                excerpt=document.text[:120],
                score=score,
            )
        )
    return sorted(scored, key=lambda item: (-item.score, item.doc_id))[:limit]
