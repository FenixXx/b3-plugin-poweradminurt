#
# PowerAdmin Plugin for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2008 Mark Weirath (xlr8or@xlr8or.com)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

__version__ = '1.24'
__author__ = 'xlr8or, courgette'


"""
Depending on the B3 parser loaded, this module will either act as the plugin for
UrT4.1 or the plugin for UrT4.2
"""


class PoweradminurtPlugin(object):

    requiresConfigFile = True
    requiresPlugins = []
    requiresParsers = ['iourt41', 'iourt42']

    def __new__(cls, *args, **kwargs):
        console, plugin_config = args
        if console.gameName == 'iourt41':
            from poweradminurt.iourt41 import Poweradminurt41Plugin
            return Poweradminurt41Plugin(*args, **kwargs)
        elif console.gameName == 'iourt42':
            from poweradminurt.iourt42 import Poweradminurt42Plugin
            return Poweradminurt42Plugin(*args, **kwargs)
        else:
            raise AssertionError("Poweradminurt plugin can only work with Urban Terror 4.1 or 4.2")