from __future__ import annotations

import abc
import collections
import contextlib
import datetime
import enum
from collections.abc import AsyncGenerator, AsyncIterator, Sequence
from typing import Any, Self

import aiohttp
import attrs
import gidgethub.abc
import gidgethub.aiohttp


class UserHadNoDatabaseID(Exception):
    pass


@attrs.frozen
class User:
    id: int
    login: str

    @classmethod
    def from_graphql_data(cls, data: dict[str, object]) -> User:
        if (database_id := data.get("databaseId")) is None:
            raise UserHadNoDatabaseID

        assert isinstance(database_id, int)
        return User(login=str(data["login"]), id=database_id)


@attrs.frozen
class Commit:
    commit_sha: str
    author: User
    committer: User


@attrs.frozen
class Approve:
    submitted_at: datetime.datetime
    reviewer: User
    approved_sha: str


class PullRequestState(enum.StrEnum):
    CLOSED = "CLOSED"
    MERGED = "MERGED"
    OPEN = "OPEN"


@attrs.frozen
class CurrentPullRequestState:
    author: User
    state: PullRequestState
    commits: Sequence[Commit]
    approves: Sequence[Approve]
    head_sha: str
    head_ref: str
    base_sha: str
    base_ref: str


class CommonGithubAPI(abc.ABC):
    @abc.abstractmethod
    def for_pull_request(
        self, *, repo_name: str, org: str, pr_number: int
    ) -> CommonGithubPullRequest: ...


class CommonGithubPullRequest(abc.ABC):
    @abc.abstractmethod
    async def current_state(self) -> CurrentPullRequestState: ...


@attrs.frozen
class GithubPullRequest(CommonGithubPullRequest):
    _api: gidgethub.abc.GitHubAPI
    _org: str
    _repo_name: str
    _pr_number: int

    async def current_state(self) -> CurrentPullRequestState:
        pr = (
            await self._api.graphql(
                """
                query ($owner: String!, $repo: String!, $number: Int!) {
                    repository(owner: $owner, name: $repo) {
                        pullRequest(number: $number) {
                            baseRef { name, target { oid } },
                            headRef { name, target { oid } },
                            author { login, ... on User { databaseId }, ... on Bot { databaseId } }
                            state,
                            commits(first: 100, after: null) {
                                nodes {
                                    commit {
                                        oid,
                                        author {
                                            user {
                                                login,
                                                databaseId
                                            }
                                        }
                                        committer {
                                            user {
                                                login,
                                                databaseId
                                            }
                                        }
                                    }
                                },
                                pageInfo {
                                    endCursor
                                    hasNextPage
                                }
                            }
                            reviews(first: 100, after: null) {
                                nodes {
                                    state
                                    submittedAt
                                    commit {
                                        oid
                                    }
                                    author {
                                        login, ... on User { databaseId }, ... on Bot { databaseId }
                                    }
                                }
                                pageInfo {
                                    endCursor
                                    hasNextPage
                                }
                            }
                        }
                    },
                }
                """,
                owner=self._org,
                repo=self._repo_name,
                number=self._pr_number,
            )
        )["repository"]["pullRequest"]

        commits: list[Commit] = []
        async for commit in self._interpret_commits(
            end_cursor=str(pr["commits"]["pageInfo"]["endCursor"]),
            has_next_page=bool(pr["commits"]["pageInfo"]["hasNextPage"]),
            commits=pr["commits"]["nodes"],
        ):
            commits.append(commit)

        approves_by_reviewer: dict[int, list[Approve]] = collections.defaultdict(list)
        async for approve in self._interpret_approved_reviews(
            end_cursor=str(pr["reviews"]["pageInfo"]["endCursor"]),
            has_next_page=bool(pr["reviews"]["pageInfo"]["hasNextPage"]),
            reviews=pr["reviews"]["nodes"],
        ):
            approves_by_reviewer[approve.reviewer.id].append(approve)

        approves: list[Approve] = []
        for _, aps in approves_by_reviewer.items():
            approves.append(sorted(aps, key=lambda ap: ap.submitted_at)[-1])

        return CurrentPullRequestState(
            author=User.from_graphql_data(pr["author"]),
            head_sha=str(pr["headRef"]["target"]["oid"]),
            head_ref=str(pr["headRef"]["name"]),
            base_sha=str(pr["baseRef"]["target"]["oid"]),
            base_ref=str(pr["baseRef"]["name"]),
            state=PullRequestState(pr["state"]),
            commits=commits,
            approves=approves,
        )

    async def _interpret_commits(
        self, *, end_cursor: str, has_next_page: bool, commits: Sequence[dict[str, Any]]
    ) -> AsyncIterator[Commit]:
        for commit in commits:
            yield Commit(
                commit_sha=str(commit["commit"]["oid"]),
                author=User.from_graphql_data(commit["commit"]["author"]["user"]),
                committer=User.from_graphql_data(commit["commit"]["committer"]["user"]),
            )

        if has_next_page:
            response = (
                await self._api.graphql(
                    """
                    query ($owner: String!, $repo: String!, $number: Int!, $after: String!) {
                        repository(owner: $owner, name: $repo) {
                            pullRequest(number: $number) {
                                commits(first: 100, after: $after) {
                                    nodes {
                                        commit {
                                            oid,
                                            author {
                                                user {
                                                    login,
                                                    databaseId
                                                }
                                            }
                                            committer {
                                                user {
                                                    login,
                                                    databaseId
                                                }
                                            }
                                        }
                                    },
                                    pageInfo {
                                        endCursor
                                        hasNextPage
                                    }
                                }
                            }
                        },
                    }
                    """,
                    owner=self._org,
                    repo=self._repo_name,
                    number=self._pr_number,
                    after=end_cursor,
                )
            )["repository"]["pullRequest"]["commits"]

            async for processed in self._interpret_commits(
                end_cursor=str(response["pageInfo"]["endCursor"]),
                has_next_page=bool(response["pageInfo"]["hasNextPage"]),
                commits=response["nodes"],
            ):
                yield processed

    async def _interpret_approved_reviews(
        self, *, end_cursor: str, has_next_page: bool, reviews: Sequence[dict[str, Any]]
    ) -> AsyncIterator[Approve]:
        for review in reviews:
            if str(review["state"]) == "APPROVED":
                yield Approve(
                    submitted_at=datetime.datetime.fromisoformat(str(review["submittedAt"])),
                    approved_sha=str(review["commit"]["oid"]),
                    reviewer=User.from_graphql_data(review["author"]),
                )

        if has_next_page:
            response = (
                await self._api.graphql(
                    """
                    query ($owner: String!, $repo: String!, $number: Int!, $after: String!) {
                        repository(owner: $owner, name: $repo) {
                            pullRequest(number: $number) {
                                reviews(first: 100, after: $after) {
                                    nodes {
                                        state,
                                        submittedAt
                                        commit {
                                            oid
                                        }
                                        author {
                                            login, ... on User { databaseId }, ... on Bot { databaseId }
                                        }
                                    }
                                    pageInfo {
                                        endCursor
                                        hasNextPage
                                    }
                                }
                            }
                        },
                    }
                    """,
                    owner=self._org,
                    repo=self._repo_name,
                    number=self._pr_number,
                    after=end_cursor,
                )
            )["repository"]["pullRequest"]["reviews"]

            async for processed in self._interpret_approved_reviews(
                end_cursor=str(response["pageInfo"]["endCursor"]),
                has_next_page=bool(response["pageInfo"]["hasNextPage"]),
                reviews=response["nodes"],
            ):
                yield processed


@attrs.frozen
class GithubAPI(CommonGithubAPI):
    _api: gidgethub.abc.GitHubAPI
    _session: aiohttp.ClientSession

    @classmethod
    @contextlib.asynccontextmanager
    async def create(cls, *, token: str, requester: str) -> AsyncGenerator[Self]:
        async with aiohttp.ClientSession() as session:
            yield cls(
                session=session,
                api=gidgethub.aiohttp.GitHubAPI(session, requester, oauth_token=token),
            )

    def for_pull_request(self, *, repo_name: str, org: str, pr_number: int) -> GithubPullRequest:
        return GithubPullRequest(api=self._api, org=org, repo_name=repo_name, pr_number=pr_number)
