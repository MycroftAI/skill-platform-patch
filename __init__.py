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

import os
from tempfile import NamedTemporaryFile
from subprocess import call

from adapt.intent import IntentBuilder
from mycroft.configuration import ConfigurationManager
from mycroft.skills.core import MycroftSkill
from mycroft.util.log import getLogger

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
        if self.platform_build is not 2:
            self.patch_platform("")

    def patch_platform(self, message):
        if self.platform_type == "mycroft_mark_1" or self.platform_type == "picroft":
            if self.platform_build < 4 or self.platform_build is None and self.platform_build is not 2:
                script_fn = NamedTemporaryFile().name
                ret_code = call('curl -sL https://mycroft.ai/to/platform_patch_1 | base64 --decode > ' + script_fn, shell=True)
                if ret_code == 0:
                    if call('bash ' + script_fn) == 0:
                        self.speak_dialog("platform.patch.success")
                        return
                self.speak_dialog("platform.patch.failure")
        else:
            self.speak_dialog("platform.patch.not.possible")

    def stop(self):
        pass


def create_skill():
    return PlatformPatchSkill()
