import logging
import urllib.request
from functools import partial

from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from pretalx.schedule.signals import schedule_release

logger = logging.getLogger(__name__)


def trigger_pipeline(event):
    if "pretalx_gitlab_trigger" not in event.plugin_list:
        return
    url = settings.PLUGIN_SETTINGS.get("pretalx_gitlab_trigger", {}).get("url")
    if not url:
        return
    request = urllib.request.Request(url, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310 -- URL comes from pretalx.cfg
            logger.info("GitLab trigger for event %s returned HTTP %s", event.slug, response.status)
    except OSError:
        # The URL contains the trigger token, so do not log the exception message.
        logger.warning("GitLab trigger failed for event %s", event.slug)


@receiver(schedule_release, dispatch_uid="gitlab_trigger_schedule_release")
def on_schedule_release(sender, **kwargs):
    trigger_pipeline(sender)


@receiver(post_save, sender="submission.Resource", dispatch_uid="gitlab_trigger_resource_save")
@receiver(post_delete, sender="submission.Resource", dispatch_uid="gitlab_trigger_resource_delete")
@receiver(post_save, sender="pretalx_peertube.PeertubeLink", dispatch_uid="gitlab_trigger_peertube_save")
@receiver(post_delete, sender="pretalx_peertube.PeertubeLink", dispatch_uid="gitlab_trigger_peertube_delete")
def on_talk_data_change(sender, instance, **kwargs):
    # Send after the commit, so the pipeline already downloads the new data.
    transaction.on_commit(partial(trigger_pipeline, instance.submission.event))
