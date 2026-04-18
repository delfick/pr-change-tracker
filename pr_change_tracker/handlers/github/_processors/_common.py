from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import ClassVar, Self

import attrs
import jsonpath


class _Pointers:
    pr_number: ClassVar[jsonpath.JSONPointer] = jsonpath.JSONPointer("/pull_request/number")
    branch_name: ClassVar[jsonpath.JSONPointer] = jsonpath.JSONPointer("/pull_request/head/ref")
    full_name: ClassVar[jsonpath.JSONPointer] = jsonpath.JSONPointer("/repository/full_name")

    created_at: ClassVar[jsonpath.JSONPointer] = jsonpath.JSONPointer("/pull_request/created_at")
    updated_at: ClassVar[jsonpath.JSONPointer] = jsonpath.JSONPointer("/pull_request/updated_at")
    closed_at: ClassVar[jsonpath.JSONPointer] = jsonpath.JSONPointer("/pull_request/closed_at")
    merged_at: ClassVar[jsonpath.JSONPointer] = jsonpath.JSONPointer("/pull_request/merged_at")


def _as_int(value: object) -> int:
    assert isinstance(value, int)
    return value


@attrs.frozen
class Timestamps:
    created_at: datetime.datetime
    updated_at: datetime.datetime
    closed_at: datetime.datetime | None
    merged_at: datetime.datetime | None

    @classmethod
    def from_data(cls, data: Mapping[str, object]) -> Self:
        created_at = datetime.datetime.fromisoformat(str(_Pointers.created_at.resolve(data)))
        updated_at = datetime.datetime.fromisoformat(str(_Pointers.created_at.resolve(data)))

        closed_at_raw = _Pointers.created_at.resolve(data)
        if closed_at_raw is None:
            closed_at = None
        else:
            closed_at = datetime.datetime.fromisoformat(str(closed_at_raw))

        merged_at_raw = _Pointers.merged_at.resolve(data)
        if merged_at_raw is None:
            merged_at = None
        else:
            merged_at = datetime.datetime.fromisoformat(str(merged_at_raw))

        return cls(
            created_at=created_at, updated_at=updated_at, closed_at=closed_at, merged_at=merged_at
        )


@attrs.frozen
class PullRequest:
    pr_number: int
    repo_name: str
    org: str
    branch_name: str

    @classmethod
    def from_data(cls, data: Mapping[str, object]) -> Self:
        org, repo_name = str(_Pointers.full_name.resolve(data)).split("/", 1)
        return cls(
            pr_number=_as_int(_Pointers.pr_number.resolve(data)),
            repo_name=repo_name,
            org=org,
            branch_name=str(_Pointers.branch_name.resolve(data)),
        )
