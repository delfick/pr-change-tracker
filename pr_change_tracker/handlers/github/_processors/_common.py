from __future__ import annotations

from collections.abc import Mapping
from typing import ClassVar, Self

import attrs
import jsonpath


class _Pointers:
    pr_number: ClassVar[jsonpath.JSONPointer] = jsonpath.JSONPointer("/pull_request/number")
    branch_name: ClassVar[jsonpath.JSONPointer] = jsonpath.JSONPointer("/pull_request/head/ref")
    full_name: ClassVar[jsonpath.JSONPointer] = jsonpath.JSONPointer("/repository/full_name")


def _as_int(value: object) -> int:
    assert isinstance(value, int)
    return value


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
