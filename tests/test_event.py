from unittest.mock import Mock

import pytest
from github.Branch import Branch
from github.CheckRun import CheckRun
from github.CheckSuite import CheckSuite
from github.Commit import Commit
from github.GitRelease import GitRelease
from github.GithubObject import GithubObject
from github.Issue import Issue
from github.IssueComment import IssueComment
from github.NamedUser import NamedUser
from github.PullRequest import PullRequest
from github.PullRequestReview import PullRequestReview
from github.Repository import Repository

from githubapp.events import (
    CheckRunCompletedEvent,
    CheckSuiteCompletedEvent,
    CheckSuiteRequestedEvent,
    CheckSuiteRerequestedEvent,
    CreateBranchEvent,
    CreateTagEvent,
    IssueCommentCreatedEvent,
    IssueCommentDeletedEvent,
    IssueCommentEditedEvent,
    IssueOpenedEvent,
    PullRequestReviewDismissedEvent,
    PullRequestReviewEditedEvent,
    PullRequestReviewSubmittedEvent,
    PushEvent,
    ReleaseCreatedEvent,
    ReleaseReleasedEvent,
    StatusEvent,
)
from githubapp.events.event import Event
from githubapp.events.issues import IssueEditedEvent
from tests.conftest import event_action_request
from tests.mocks import EventTest, SubEventTest


# noinspection PyUnresolvedReferences
def test_init(event_action_request):
    headers, body = event_action_request
    SubEventTest(gh=Mock(), requester=Mock(), headers=headers, **body)
    assert Event.github_event == "event"
    assert Event.hook_id == 1
    assert Event.delivery == "a1b2c3d4"
    assert Event.hook_installation_target_type == "type"
    assert Event.hook_installation_target_id == 2


def test_normalize_dicts():
    d1 = {"a": "1"}
    d2 = {"X-Github-batata": "Batata"}

    union_dict = Event.normalize_dicts(d1, d2)
    assert union_dict == {"a": "1", "batata": "Batata"}


def test_get_event(event_action_request):
    headers, body = event_action_request
    assert Event.get_event(headers, body) == SubEventTest
    body.pop("action")
    assert Event.get_event(headers, body) == EventTest


def test_match():
    d1 = {"a": 1, "b": 2}
    d2 = {"b": 2}
    d3 = {"a": 1, "b": 1}

    class LocalEventTest(Event):
        pass

    LocalEventTest.event_identifier = d2
    assert LocalEventTest.match(d1) is True
    assert LocalEventTest.match(d3) is False
    LocalEventTest.event_identifier = d1
    assert LocalEventTest.match(d3) is False


def test_lazy_fix_url():
    attributes = {"url": "https://github.com/potato"}
    Event.fix_attributes(attributes)
    assert attributes["url"] == "https://api.github.com/repos/potato"


def test_lazy_fix_url_when_is_correct():
    attributes = {"url": "correct_url"}
    Event.fix_attributes(attributes)
    assert attributes["url"] == "correct_url"


@pytest.fixture(autouse=True, scope="session")
def all_events():
    all_event_classes = []
    for event_class in Event.__subclasses__():
        if event_class.__module__.startswith("tests"):
            continue
        if sub_classes := event_class.__subclasses__():
            all_event_classes.extend(sub_classes)
        else:
            all_event_classes.append(event_class)
    yield all_event_classes
    assert all_event_classes == []


TEST_INSTANTIATE_EVENTS_VALUES = {
    CheckRunCompletedEvent: (
        "check_run",
        {"action": "completed"},
        {"check_run": CheckRun},
    ),
    CheckSuiteCompletedEvent: (
        "check_suite",
        {"action": "completed"},
        {"check_suite": CheckSuite},
    ),
    CheckSuiteRequestedEvent: (
        "check_suite",
        {"action": "requested"},
        {"check_suite": CheckSuite},
    ),
    CheckSuiteRerequestedEvent: (
        "check_suite",
        {"action": "rerequested"},
        {"check_suite": CheckSuite},
    ),
    CreateBranchEvent: (
        "create",
        {"ref_type": "branch"},
        {
            "description": str,
            "master_branch": str,
            "pusher_type": str,
            "ref": str,
        },
    ),
    CreateTagEvent: (
        "create",
        {"ref_type": "tag"},
        {
            "description": str,
            "master_branch": str,
            "pusher_type": str,
            "ref": str,
        },
    ),
    IssueCommentCreatedEvent: (
        "issue_comment",
        {"action": "created"},
        {
            "issue": Issue,
            "issue_comment": IssueComment,
        },
    ),
    IssueCommentDeletedEvent: (
        "issue_comment",
        {"action": "deleted"},
        {
            "issue": Issue,
            "issue_comment": IssueComment,
        },
    ),
    IssueCommentEditedEvent: (
        "issue_comment",
        {"action": "edited"},
        {"issue": Issue, "issue_comment": IssueComment, "changes": dict},
    ),
    IssueOpenedEvent: (
        "issues",
        {"action": "opened"},
        {"issue": Issue, "old_issue": Issue, "old_repository": Repository},
    ),
    IssueEditedEvent: (
        "issues",
        {"action": "edited"},
        {"issue": Issue, "changes": dict},
    ),
    PullRequestReviewDismissedEvent: (
        "pull_request_review",
        {"action": "dismissed"},
        {"pull_request": PullRequest, "review": PullRequestReview},
    ),
    PullRequestReviewEditedEvent: (
        "pull_request_review",
        {"action": "edited"},
        {"pull_request": PullRequest, "review": PullRequestReview, "changes": dict},
    ),
    PullRequestReviewSubmittedEvent: (
        "pull_request_review",
        {"action": "submitted"},
        {"pull_request": PullRequest, "review": PullRequestReview},
    ),
    PushEvent: (
        "push",
        {"action": "submitted"},
        {
            "after": str,
            "base_ref": str,
            "before": str,
            "commits": [Commit],
            "compare": str,
            "created": bool,
            "deleted": bool,
            "forced": bool,
            "head_commit": Commit,
            "pusher": NamedUser,
            "ref": str,
        },
    ),
    ReleaseReleasedEvent: (
        "release",
        {"action": "released"},
        {"release": GitRelease},
    ),
    ReleaseCreatedEvent: (
        "release",
        {"action": "created"},
        {"release": GitRelease},
    ),
    StatusEvent: (
        "status",
        {},
        {
            "branches": [Branch],
            "commit": Commit,
            "context": str,
            "created_at": str,
            "description": str,
            "id": int,
            "name": str,
            "sha": str,
            "state": str,
            "target_url": str,
            "updated_at": str,
        },
    ),
}


@pytest.mark.parametrize(
    "event_class",
    [
        CheckRunCompletedEvent,
        CheckSuiteCompletedEvent,
        CheckSuiteRequestedEvent,
        CheckSuiteRerequestedEvent,
        CreateBranchEvent,
        CreateTagEvent,
        IssueCommentCreatedEvent,
        IssueCommentDeletedEvent,
        IssueCommentEditedEvent,
        IssueOpenedEvent,
        IssueEditedEvent,
        PullRequestReviewDismissedEvent,
        PullRequestReviewEditedEvent,
        PullRequestReviewSubmittedEvent,
        PushEvent,
        ReleaseReleasedEvent,
        ReleaseCreatedEvent,
        StatusEvent,
    ],
)
def test_instantiate_events(event_class, event_action_request, all_events):
    event, event_identifier, check_instance = TEST_INSTANTIATE_EVENTS_VALUES.get(
        event_class
    )
    check_instance.update({"sender": NamedUser, "repository": Repository})
    headers, default_body = event_action_request
    headers["X-Github-Event"] = event

    body = default_body.copy()
    body.pop("action")
    body.update(event_identifier)
    for attribute, attr_type in check_instance.items():
        if isinstance(attr_type, list):
            value = [{}]
        elif issubclass(attr_type, GithubObject):
            value = {}
        else:
            value = attr_type()
        body[attribute] = value

    # Exceptions
    if event_class == IssueOpenedEvent:
        body["changes"] = {
            "old_issue": body.pop("old_issue"),
            "old_repository": body.pop("old_repository"),
        }
    event_instance = Event.get_event(headers, body)(
        gh=Mock(), requester=Mock(), headers=headers, **body
    )
    assert isinstance(event_instance, event_class)
    assert isinstance(event_instance.repository, Repository)
    assert isinstance(event_instance.sender, NamedUser)
    for attribute, attr_type in check_instance.items():
        if isinstance(attr_type, list):
            value = getattr(event_instance, attribute)[0]
            attr_type = attr_type[0]
        else:
            value = getattr(event_instance, attribute)
        assert isinstance(
            value, attr_type
        ), f"{attribute} is {type(value)} not {attr_type}"
    all_events.remove(event_class)
