# Copyright (c) 2017, Zebula Sampedro, CU Boulder Research Computing

"""
Singularity Spawner

SingularitySpawner provides a mechanism for spawning Jupyter Notebooks inside of Singularity containers. The spawner options form is leveraged such that the user can specify which Singularity image the spawner should use.

A `singularity exec {notebook spawn cmd}` is used to start the notebook inside of the container.
"""
import os
import pipes

from tornado import gen
from tornado.process import Subprocess
from tornado.iostream import StreamClosedError
from singularity.cli import Singularity

from jupyterhub.spawner import (
    LocalProcessSpawner, set_user_setuid
)
from jupyterhub.utils import random_port
from jupyterhub.traitlets import Command
from traitlets import (
    Integer, Unicode, Float, Dict, List, Bool, default
)

JS_SCRIPT = """<script>
require(['jquery'], function($) {
  var pullCheckbox = $('#pull-checkbox');
  var spawnButton = $('#spawn_form input[type="submit"]');

  pullCheckbox.on('change', function() {
    $('#url-group').toggle();
  });

  spawnButton.on('click', function() {
    if (pullCheckbox.is(':checked')) {
      $(this).attr("value","Pulling image...")
    }
  })
});
</script>
"""

class SingularitySpawner(LocalProcessSpawner):
    """SingularitySpawner - extends the default LocalProcessSpawner to allow for:
    1) User-specification of a singularity image via the Spawner options form
    2) Spawning a Notebook server within a Singularity container
    """

    singularity_cmd = Command(['/usr/local/bin/singularity','exec'],
        help="""
        This is the singularity command that will be executed when starting the
        single-user server. The image path and notebook server args will be concatenated to the end of this command. This is a good place to
        specify any site-specific options that should be applied to all users,
        such as default mounts.
        """
    ).tag(config=True)

    notebook_cmd = Command(['jupyterhub-singleuser'],
        help="""
        The command used for starting the single-user server.
        Provide either a string or a list containing the path to the startup script command. Extra arguments,
        other than this path, should be provided via `args`.
        """
    ).tag(config=True)

    default_image_path = Unicode('',
        help="""
        Absolute POSIX filepath to Singularity image that will be used to
        execute the notebook server spawn command, if another path is not
        specified by the user.
        """
    ).tag(config=True)

    pull_from_url = Bool(False,
        help="""
        If set to True, the user should be presented with URI specification
        options, and the spawner should first pull a new image from the
        specified shub or docker URI prior to running the notebook command.
        In this configuration, the `user_image_path` will specify where the
        new container will be created.
        """
    ).tag(config=True)

    default_image_url = Unicode('docker://jupyter/base-notebook',
        help="""
        Singularity Hub or Docker URI from which the notebook image will be
        pulled, if no other URI is specified by the user but the _pull_ option
        has been selected.
        """
    ).tag(config=True)

    options_form = Unicode()

    form_template = Unicode(
        """
        <div class="checkbox">
          <label>
            <input id="pull-checkbox" type="checkbox" value="pull" name="pull_from_url">Pull from URL
          </label>
        </div>
        <div id="url-group" class="form-group" hidden>
          <label for="user_image_url">
            Specify the image URL to pull from:
          </label>
          <input class="form-control" name="user_image_url" value="{default_image_url}">
        </div>
        <div class="form-group">
          <label id="path-label" for="user_image_path">
            Specify the Singularity image to use (absolute filepath):
          </label>
          <input class="form-control" name="user_image_path" value="{default_image_path}" required autofocus>
        </div>
        """
    )

    def format_default_image_path(self):
        """Format the image path template string."""
        format_options = dict(username=self.user.escaped_name)
        default_image_path = self.default_image_path.format(**format_options)
        return default_image_path

    @default('options_form')
    def _options_form(self):
        """Render the options form."""
        default_image_path = self.format_default_image_path()
        format_options = dict(default_image_path=default_image_path,default_image_url=self.default_image_url)
        options_form = self.form_template.format(**format_options)
        return JS_SCRIPT + options_form

    def options_from_form(self, form_data):
        """Get data from options form input fields."""
        user_image_path = form_data.get('user_image_path', None)
        user_image_url = form_data.get('user_image_url', None)
        pull_from_url = form_data.get('pull_from_url',False)

        return dict(user_image_path=user_image_path,user_image_url=user_image_url,pull_from_url=pull_from_url)

    def get_image_url(self):
        """Get image URL to pull image from user options or default."""
        default_image_url = self.default_image_url
        image_url = self.user_options.get('user_image_url',[default_image_url])
        return image_url

    def get_image_path(self):
        """Get image filepath specified in user options else default."""
        default_image_path = self.format_default_image_path()
        image_path = self.user_options.get('user_image_path',[default_image_path])
        return image_path

    @gen.coroutine
    def pull_image(self,image_url):
        """Pull the singularity image to specified image path."""
        image_path = self.get_image_path()
        s = Singularity()
        container_path = s.pull(image_url[0],image_name=image_path[0])
        return Unicode(container_path)

    def _build_cmd(self):
        image_path = self.get_image_path()
        cmd = []
        cmd.extend(self.singularity_cmd)
        cmd.extend(image_path)
        cmd.extend(self.notebook_cmd)
        return cmd

    @property
    def cmd(self):
        return self._build_cmd()

    @gen.coroutine
    def start(self):
        """
        Start the single-user server in the Singularity container specified
        by image path, pulling from docker or shub first if the pull option
        is selected.
        """
        image_path = self.get_image_path()
        pull_from_url = self.user_options.get('pull_from_url',False)
        if pull_from_url:
            image_url = self.get_image_url()
            self.pull_image(image_url)

        super(SingularitySpawner,self).start()
