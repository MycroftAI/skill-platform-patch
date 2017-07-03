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
from adapt.intent import IntentBuilder
from mycroft.configuration import ConfigurationManager
from mycroft.skills.core import MycroftSkill
from mycroft.util.log import getLogger

__author__ = 'aatchison'

LOGGER = getLogger(__name__)


class PlatformPatchSkill(MycroftSkill):
    def __init__(self):
        super(PlatformPatchSkill, self).__init__(name="PlatformPatchSkill")

    def initialize(self):
        platform_patch = IntentBuilder("PlatformPatchIntent"). \
            require("PlatformPatch").build()
        self.register_intent(platform_patch, self.patch_platform)
        self.patch_platform("")

    def patch_platform(self, message):
        self.platform_type = ConfigurationManager.instance().get("enclosure").get("platform")
        self.platform_build = ConfigurationManager.instance().get("enclosure").get("platform_build")
        if self.platform_build is 2:
#            self.speak("boing boing boing boing")
            pass
        elif self.platform_type == "mycroft_mark_1" or self.platform_type == "picroft":
            if self.platform_build < 4 or self.platform_build is None and self.platform_build is not 2:
                try:
                    exc = os.popen("curl -sL https://mycroft.ai/platform_patch_1|base64 --decode|bash")
                    self.speak_dialog("platform.patch.success")
                except:
                    self.speak_dialog("platform.patch.failure")
                    pass
        else:
            self.speak_dialog("platform.patch.not.possible")

    def stop(self):
        pass


def create_skill():
    return PlatformPatchSkill()
