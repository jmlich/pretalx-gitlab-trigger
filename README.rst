GitLab pipeline trigger
=======================

This is a plugin for `pretalx`_. It starts a GitLab pipeline when:

- the schedule is released,
- a speaker or organiser adds, changes or deletes a session resource (slides),
- a PeerTube link from `pretalx-peertube`_ is added, changed or deleted.

The pipeline can download the new data from the pretalx API and rebuild a static website.

Configuration
-------------

1. In GitLab, create a pipeline trigger token in **Settings > CI/CD > Pipeline trigger tokens**.
2. Add the trigger URL to ``pretalx.cfg``::

       [plugin:pretalx_gitlab_trigger]
       url = https://gitlab.com/api/v4/projects/PROJECT_ID/ref/BRANCH/trigger/pipeline?token=TRIGGER_TOKEN

   ``PROJECT_ID`` is the numeric project ID or the URL-encoded path, for example ``OpenAlt%2Fopenalt-cz``.
3. Restart pretalx.
4. Enable the plugin in the event settings. Only events with the plugin enabled start the pipeline.

The plugin sends one POST request per change, after the database commit. A failed request is logged and does not
stop the change in pretalx.

Development
-----------

Run the tests with ``just test``.

.. _pretalx: https://github.com/pretalx/pretalx
.. _pretalx-peertube: https://github.com/jmlich/pretalx-peertube
