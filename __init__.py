# Copyright 2016 Mycroft AI, Inc.
#
# This file is part of Mycroft Core.
#
# Mycroft Core is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Mycroft Core is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Mycroft Core.  If not, see <http://www.gnu.org/licenses/>.

from tempfile import NamedTemporaryFile
from subprocess import call

from adapt.intent import IntentBuilder
from mycroft.configuration import ConfigurationManager
from mycroft.skills.core import MycroftSkill
from mycroft.util.log import getLogger
from mycroft.messagebus.message import Message

__author__ = 'aatchison'

LOGGER = getLogger(__name__)


class PlatformPatchSkill(MycroftSkill):
    def __init__(self):
        super(PlatformPatchSkill, self).__init__(name="PlatformPatchSkill")
        self.platform_type = ConfigurationManager.instance().get("enclosure").get("platform")
        self.platform_build = ConfigurationManager.instance().get("enclosure").get("platform_build")

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
        """Duplicate logic exists in remote platform patch script"""
        return self.platform_type == "mycroft_mark_1"

    def must_apply(self):
        """Duplicate logic exists in remote platform patch script"""
        return self.platform_build is None or self.platform_build < 9

    @classmethod
    def download_patch(cls):
        filename = NamedTemporaryFile().name
        cls.cmd('curl -sL https://mycroft.ai/to/platform_patch_1 | base64 --decode > ' + filename)
        return filename

    def run_patch(self, filename):
        """Replaces crontab, updates GPG key, and sets platform_build to 9"""
        self.cmd('bash ' + filename)
        try:
            ConfigurationManager.load_local()
        except AttributeError:
            self.emitter.emit(Message('configuration.updated'))
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
            except RuntimeError:
                self.speak_dialog('platform.patch.failure', data={
                    'type': 'runtime error',
                    'error': ''
                })
            except Exception as e:
                self.speak_dialog("platform.patch.failure", data={
                    'error': str(e),
                    'type': e.__class__.__name__
                })

    def stop(self):
        pass


def create_skill():
    return PlatformPatchSkill()
