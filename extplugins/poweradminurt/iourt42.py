#
# PowerAdmin Plugin for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2012 Thomas LEVEIL <courgette@bigbrotherbot.net)
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

import b3.plugin

from poweradminurt.iourt41 import Poweradminurt41Plugin
from poweradminurt import __version__, __author__

import ConfigParser


class Poweradminurt42Plugin(Poweradminurt41Plugin):

    def __init__(self, console, config=None):

        b3.plugin.Plugin.__init__(self, console, config)
        if self.console.gameName != 'iourt42':
            self.critical("unsupported game : %s" % self.console.gameName)
            raise SystemExit(220)

        ### hit location constants ###

        try:
            self._hitlocations['HL_HEAD'] = self.console.HL_HEAD
        except AttributeError, e:
            self._hitlocations['HL_HEAD'] = '1'
            self.warning("could not get HL_HEAD value from B3 parser: %s" % e)

        self.debug("HL_HEAD is %s" % self._hitlocations['HL_HEAD'])

        try:
            self._hitlocations['HL_HELMET'] = self.console.HL_HELMET
        except AttributeError, e:
            self._hitlocations['HL_HELMET'] = '2'
            self.warning("could not get HL_HELMET value from B3 parser: %s" % e)

        self.debug("HL_HELMET is %s" % self._hitlocations['HL_HELMET'])

        try:
            self._hitlocations['HL_TORSO'] = self.console.HL_TORSO
        except AttributeError, e:
            self._hitlocations['HL_TORSO'] = '3'
            self.warning("could not get HL_TORSO value from B3 parser: %s" % e)

        self.debug("HL_TORSO is %s" % self._hitlocations['HL_TORSO'])

    # radio spam protection
    _rsp_enable = False
    _rsp_mute_duration = 2
    _rsp_falloffRate = 2  # spam points will fall off by 1 point every 4 seconds
    _rsp_maxSpamins = 10

    def registerEvents(self):
        """\
        Register events needed
        """
        Poweradminurt41Plugin.registerEvents(self)
        self.registerEvent(self.console.EVT_CLIENT_RADIO)

    def onLoadConfig(self):
        """\
        Load plugin configuration
        """
        Poweradminurt41Plugin.onLoadConfig(self)
        self.loadRadioSpamProtection()

    def onEvent(self, event):
        """\
        Handle intercepted events
        """
        if event.type == self.console.EVT_CLIENT_RADIO:
            self.onRadio(event)
        else:
            Poweradminurt41Plugin.onEvent(self, event)

    ###############################################################################################
    #
    #    config loaders
    #
    ###############################################################################################

    def loadRadioSpamProtection(self):
        """\
        Setup the radio spam protection
        """
        try:
            self._rsp_enable = self.config.getboolean('radio_spam_protection', 'enable')
        except ConfigParser.NoOptionError:
            self.warning('Could not find radio_spam_protection/enable in config file, using default: %s' %
                         self._rsp_enable)
        except ValueError, e:
            self.error('Could not load radio_spam_protection/enable config value: %s' % e)
            self.debug('Using default value (%s) for radio_spam_protection/enable' % self._rsp_enable)

        try:

            self._rsp_mute_duration = self.config.getint('radio_spam_protection', 'mute_duration')
            if self._rsp_mute_duration < 1:
                raise ValueError('radio_spam_protection/mute_duration cannot be lower than 1')

        except ConfigParser.NoOptionError:
            self.warning('Could not find radio_spam_protection/mute_duration in config file, using default: %s' %
                         self._rsp_mute_duration)
        except ValueError, e:
            self._rsp_mute_duration = 2  # set again because it might have been overwritten
            self.error('Could not load radio_spam_protection/mute_duration config value: %s' % e)
            self.debug('Using default value (%s) for radio_spam_protection/mute_duration' % self._rsp_mute_duration)

        self.debug('Radio spam protection enable: %s' % self._rsp_enable)
        self.debug('Radio spam protection mute duration: %s' % self._rsp_mute_duration)

    ###############################################################################################
    #
    #    event handlers
    #
    ###############################################################################################

    def onRadio(self, event):
        """\
        Handle radio events
        """
        if not self._rsp_enable:
            return

        # event.data : {'msg_group': '7', 'msg_id': '2', 'location': 'New Alley', 'text': "I'm going for the flag" }

        client = event.client
        if client.var(self, 'radio_ignore_till', self.getTime()).value > self.getTime():
            self.debug("ignoring radio event")
            return

        points = 0
        data = repr(event.data)
        last_message_data = client.var(self, 'last_radio_data').value

        now = self.getTime()
        last_radio_time = client.var(self, 'last_radio_time', None).value
        gap = None
        if last_radio_time is not None:
            gap = now - last_radio_time
            if gap < 20:
                points += 1
            if gap < 2:
                points += 1
                if data == last_message_data:
                    points += 3
            if gap < 1:
                points += 3

        spamins = client.var(self, 'radio_spamins', 0).value + points

        # apply natural points decrease due to time
        if gap is not None:
            spamins -= int(gap / self._rsp_falloffRate)

        if spamins < 1:
            spamins = 0

        # set new values
        self.verbose("radio_spamins for %s : %s" % (client.name, spamins))
        client.setvar(self, 'radio_spamins', spamins)
        client.setvar(self, 'last_radio_time', now)
        client.setvar(self, 'last_radio_data', data)

        # should we warn ?
        if spamins >= self._rsp_maxSpamins:
            self.console.writelines(["mute %s %s" % (client.cid, self._rsp_mute_duration)])
            client.setvar(self, 'radio_spamins', int(self._rsp_maxSpamins / 2.0))
            client.setvar(self, 'radio_ignore_till', int(self.getTime() + self._rsp_mute_duration - 1))

    ###############################################################################################
    #
    #    commands
    #
    ###############################################################################################

    def cmd_pakill(self, data, client, cmd=None):
        """\
        <player> - kill a player.
        (You can safely use the command without the 'pa' at the beginning)
        """
        if not data:
            client.message('^7Invalid data, try !help pakill')
            return

        sclient = self._adminPlugin.findClientPrompt(data, client)
        if not sclient:
            # a player matchin the name was not found, a list of closest matches will be displayed
            # we can exit here and the user will retry with a more specific player
            return

        self.console.write('smite %s' % sclient.cid)

    def cmd_palms(self, data, client, cmd=None):
        """\
        Change game type to Last Man Standing
        (You can safely use the command without the 'pa' at the beginning)
        """
        self.console.setCvar('g_gametype', '1')
        if client:
            client.message('^7game type changed to ^4Last Man Standing')

        self.set_configmode('lms')

    def cmd_pajump(self, data, client, cmd=None):
        """\
        Change game type to Jump
        (You can safely use the command without the 'pa' at the beginning)
        """
        self.console.setCvar('g_gametype', '9')
        if client:
            client.message('^7game type changed to ^4Jump')

        self.set_configmode('jump')
    
    def cmd_paskins(self, data, client, cmd=None):
        """\
        Set the use of client skins <on/off>
        (You can safely use the command without the 'pa' at the beginning)
        """
        if not data or data not in ('on', 'off'):
            client.message('^7Invalid or missing data, try !help paskins')
            return

        if data == 'on':
            self.console.setCvar('g_skins', '1')
            self.console.say('^7Client skins: ^2ON')
        elif data == 'off':
            self.console.setCvar('g_skins', '0')
            self.console.say('^7Client skins: ^1OFF')

    def cmd_pafunstuff(self, data, client, cmd=None):
        """\
        Set the use of funstuff <on/off>
        (You can safely use the command without the 'pa' at the beginning)
        """
        if not data or data not in ('on', 'off'):
            client.message('^7Invalid or missing data, try !help pafunstuff')
            return

        if data == 'on':
            self.console.setCvar('g_funstuff', 1)
            self.console.say('^7Funstuff: ^2ON')
        elif data == 'off':
            self.console.setCvar('g_funstuff', 0)
            self.console.say('^7Funstuff: ^1OFF')

    def cmd_pagoto(self, data, client, cmd=None):
        """\
        Set the goto <on/off>
        (You can safely use the command without the 'pa' at the beginning)
        """
        if not data or data not in ('on', 'off'):
            client.message('^7Invalid or missing data, try !help pagoto')
            return

        if data == 'on':
            self.console.setCvar('g_allowgoto', 1)
            self.console.say('^7Goto: ^2ON')
        elif data == 'off':
            self.console.setCvar('g_allowgoto', 0)
            self.console.say('^7Goto: ^1OFF')

    def cmd_pastamina(self, data, client, cmd=None):
        """\
        Set the stamina behavior <default/regain/infinite>
        (You can safely use the command without the 'pa' at the beginning)
        """
        if not data or data not in ('default', 'regain', 'infinite'):
            client.message('^7Invalid or missing data, try !help pastamina')
            return

        if data == 'default':
            self.console.setCvar('g_stamina', 0)
            self.console.say('^7Stamina mode: ^3DEFAULT')
        elif data == 'regain':
            self.console.setCvar('g_stamina', 1)
            self.console.say('^7Stamina mode: ^3REGAIN')
        elif data == 'infinite':
            self.console.setCvar('g_stamina', 2)
            self.console.say('^7Stamina mode: ^3INFINITE')

    def cmd_paident(self, data, client=None, cmd=None):
        """\
        <name> - show the ip and guid and authname of a player
        (You can safely use the command without the 'pa' at the beginning)
        """
        args = self._adminPlugin.parseUserCmd(data)
        if not args:
            cmd.sayLoudOrPM(client, 'Your id is ^2@%s' % client.id)
            return

        # args[0] is the player id
        sclient = self._adminPlugin.findClientPrompt(args[0], client)
        if not sclient:
            # a player matching the name was not found, a list of closest matches will be displayed
            # we can exit here and the user will retry with a more specific player
            return

        if client.maxLevel < self._full_ident_level:
            cmd.sayLoudOrPM(client, '%s ^4@%s ^2%s' % (self.console.formatTime(self.console.time()),
                                                       sclient.id, sclient.exactName))
        else:
            cmd.sayLoudOrPM(client, '%s ^4@%s ^2%s ^2%s ^7[^2%s^7] since ^2%s' % (
                self.console.formatTime(self.console.time()), sclient.id, sclient.exactName, sclient.ip, sclient.pbid,
                self.console.formatTime(sclient.timeAdd)))

    ###############################################################################################
    #
    #    Other methods
    #
    ###############################################################################################

    def getTime(self):
        """ just to ease automated tests """
        return self.console.time()