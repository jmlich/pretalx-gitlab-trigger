import datetime as dt

import pytest
from django.core import management
from django_scopes import scope, scopes_disabled

from pretalx.event.domain.event import initialise_event
from pretalx.event.domain.plugins import enable_plugin
from pretalx.event.models import Event, Organiser, Team
from pretalx.person.models import SpeakerProfile, User
from pretalx.schedule.domain.release import freeze_schedule
from pretalx.submission.models import Submission, SubmissionType


@pytest.fixture(scope="session", autouse=True)
def collect_static(request):
    management.call_command("collectstatic", "--noinput", "--clear")


@pytest.fixture
def organiser():
    with scopes_disabled():
        o = Organiser.objects.create(name="Super Organiser", slug="superorganiser")
        Team.objects.create(
            name="Organisers",
            organiser=o,
            can_create_events=True,
            can_change_teams=True,
            can_change_organiser_settings=True,
            can_change_event_settings=True,
            can_change_submissions=True,
        )
        Team.objects.create(name="Reviewers", organiser=o, is_reviewer=True)
    return o


@pytest.fixture
def event(organiser):
    today = dt.date.today()
    with scopes_disabled():
        event = Event.objects.create(
            name="Fancy testevent",
            is_public=True,
            slug="test",
            email="orga@orga.org",
            date_from=today,
            date_to=today + dt.timedelta(days=3),
            organiser=organiser,
        )
        initialise_event(event)
        enable_plugin(event, "pretalx_gitlab_trigger")
        event.save()
        for team in organiser.teams.all():
            team.limit_events.add(event)
    return event


@pytest.fixture
def submission_type(event):
    with scope(event=event):
        return SubmissionType.objects.create(
            name="Workshop", event=event, default_duration=60
        )


@pytest.fixture
def speaker(event):
    with scopes_disabled():
        user = User.objects.create_user(
            password="speakerpwd1!", name="Jane Speaker", email="jane@speaker.org"
        )
        return SpeakerProfile.objects.create(  # noqa: RET504
            user=user, event=event, biography="A speaker.", name="Jane"
        )


@pytest.fixture
def confirmed_submission(event, submission_type, speaker):
    with scope(event=event):
        sub = Submission.objects.create(
            title="Test Talk",
            submission_type=submission_type,
            event=event,
            content_locale="en",
        )
        sub.speakers.add(speaker)
        sub.accept()
        sub.confirm()
        return sub


@pytest.fixture
def schedule(event):
    with scope(event=event):
        freeze_schedule(event.wip_schedule, name="v1")
        return event.current_schedule
