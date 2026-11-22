from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django_scopes import scope

from pretalx.event.models import Event
from pretalx.schedule.domain.release import freeze_schedule
from pretalx.submission.models import Resource

from pretalx_gitlab_trigger import signals

pytestmark = pytest.mark.django_db

TRIGGER_URL = "https://gitlab.example.org/api/v4/projects/1/ref/main/trigger/pipeline?token=secret"


@pytest.fixture
def trigger_url(settings):
    settings.PLUGIN_SETTINGS = {"pretalx_gitlab_trigger": {"url": TRIGGER_URL}}


def sent_urls(urlopen):
    return [call.args[0].full_url for call in urlopen.call_args_list]


def test_schedule_release_triggers_pipeline(event, trigger_url):
    with patch.object(signals.urllib.request, "urlopen") as urlopen, scope(event=event):
        freeze_schedule(event.wip_schedule, name="v1")
    assert sent_urls(urlopen) == [TRIGGER_URL]
    assert urlopen.call_args.args[0].method == "POST"


def test_resource_changes_trigger_pipeline(
    event, confirmed_submission, trigger_url, django_capture_on_commit_callbacks
):
    with (
        patch.object(signals.urllib.request, "urlopen") as urlopen,
        django_capture_on_commit_callbacks(execute=True),
        scope(event=event),
    ):
        resource = Resource.objects.create(
            submission=confirmed_submission,
            resource=SimpleUploadedFile("slides.pdf", b"%PDF-1.4"),
            description="Slides",
        )
        resource.description = "New slides"
        resource.save()
        resource.delete()
    assert sent_urls(urlopen) == [TRIGGER_URL] * 3


def test_peertube_link_changes_trigger_pipeline(
    event, confirmed_submission, trigger_url, django_capture_on_commit_callbacks
):
    peertube_models = pytest.importorskip("pretalx_peertube.models")
    with (
        patch.object(signals.urllib.request, "urlopen") as urlopen,
        django_capture_on_commit_callbacks(execute=True),
    ):
        link = peertube_models.PeertubeLink.objects.create(
            submission=confirmed_submission, link="https://peertube.example.org/w/abc"
        )
        link.delete()
    assert sent_urls(urlopen) == [TRIGGER_URL] * 2


def test_inactive_plugin_does_not_trigger(event, trigger_url):
    Event.objects.filter(pk=event.pk).update(plugins="")
    event.refresh_from_db()
    with patch.object(signals.urllib.request, "urlopen") as urlopen:
        signals.trigger_pipeline(event)
    urlopen.assert_not_called()


def test_missing_url_does_not_trigger(event, settings):
    settings.PLUGIN_SETTINGS = {}
    with patch.object(signals.urllib.request, "urlopen") as urlopen:
        signals.trigger_pipeline(event)
    urlopen.assert_not_called()


def test_failed_request_is_logged_without_token(event, trigger_url, caplog):
    with patch.object(
        signals.urllib.request, "urlopen", side_effect=OSError(TRIGGER_URL)
    ):
        signals.trigger_pipeline(event)
    assert "GitLab trigger failed for event test" in caplog.text
    assert "secret" not in caplog.text
