# Copyright 2017, Mycroft AI Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from tempfile import NamedTemporaryFile
from subprocess import call
from threading import Timer

from adapt.intent import IntentBuilder
from mycroft.configuration import ConfigurationManager
from mycroft.skills.core import MycroftSkill


class PlatformPatchSkill(MycroftSkill):
    def __init__(self):
        super(PlatformPatchSkill, self).__init__(name="PlatformPatchSkill")
        self.platform_type = ConfigurationManager.instance().get(
                                "enclosure").get("platform")
        self.platform_build = ConfigurationManager.instance().get(
                                "enclosure").get("platform_build")
        self.timer = None

    def initialize(self):
        platform_patch = IntentBuilder("PlatformPatchIntent"). \
            require("PlatformPatch").build()
        self.register_intent(platform_patch, self.patch_platform)
        if self.is_eligible() and self.must_apply():
            self.patch_platform()

    @staticmethod
    def cmd(name):
        if call(name, shell=True) != 0:
            raise RuntimeError('Failed to run command: ' + name)

    def is_eligible(self):
        # This only make sense to run on a Mark 1
        return self.platform_type == "mycroft_mark_1"

    def must_apply(self):
        # This should be run for any Mark 1 with a version # before 9
        return self.platform_build is None or self.platform_build < 9

    @classmethod
    def download_patch(cls):
        filename = NamedTemporaryFile().name
        cls.cmd('curl -sL https://mycroft.ai/to/platform_patch_1 | base64 --decode > ' + filename)  # nopep8
        return filename

    def run_patch(self, filename):
        # In brief, the patch:
        # - Replaces the crontab (run hourly instead of once a day)
        # - Updates the GPG key for the Mycroft repo
        # - Bumps the platform_build to '9'
        self.log.info("Attempting platform patch...")
        self.cmd('bash ' + filename)
        ConfigurationManager.load_local()
        self.platform_build = 9

    def patch_platform(self, message=None):
        if not self.is_eligible():
            self.speak_dialog("platform.patch.not.possible")
        elif not self.must_apply():
            self.speak_dialog("platform.patch.not.needed")
        else:
            try:
                name = self.download_patch()
                self.run_patch(name)
                self.speak_dialog("platform.patch.success")
                self.log.info("Patch successful")

                # Now show a message until the unit reboots
                self._force_update_message()

            except RuntimeError:
                self.log.info("Patch runtime error")
                self.speak_dialog('platform.patch.failure', data={
                    'type': 'runtime error',
                    'error': ''
                })
            except Exception as e:
                self.log.info("Patch failure")
                self.speak_dialog("platform.patch.failure", data={
                    'error': str(e),
                    'type': e.__class__.__name__
                })

    def _force_update_message(self):
        # This message will be shown every 60 seconds until the
        # system restarts due to the pending apt install of a new
        # version of mycroft-core.
        self.enclosure.deactivate_mouth_events()
        self.enclosure.mouth_text("UPDATING...")
        if self.timer and self.timer.is_alive():
            self.timer.cancel()
        self.timer = Timer(60, self._force_update_message)
        self.timer.start()


def create_skill():
    return PlatformPatchSkill()
