from django.apps import AppConfig
from django.utils.translation import gettext_lazy

from . import __version__


class PluginApp(AppConfig):
    name = "pretalx_gitlab_trigger"
    verbose_name = "GitLab pipeline trigger"

    class PretalxPluginMeta:
        name = gettext_lazy("GitLab pipeline trigger")
        author = "Jozef Mlich"
        description = gettext_lazy(
            "Start a GitLab pipeline when the schedule is released, or when slides or PeerTube links change."
        )
        visible = True
        version = __version__
        category = "INTEGRATION"

    def ready(self):
        from . import signals  # noqa: F401, PLC0415
