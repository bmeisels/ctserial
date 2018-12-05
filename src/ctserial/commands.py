# Copyright (C) 2018  Justin Searle
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details at <http://www.gnu.org/licenses/>.

import shlex
import re
import serial
import serial.tools.list_ports
import time
from prompt_toolkit.application.current import get_app
from prompt_toolkit.document import Document
from tabulate import tabulate
from os.path import expanduser


class Commands(object):
    """Commands that users may use at the application prompt."""
    # Each function that users can call must:
    #     - start with a do_
    #     - accept self, input_text, output_text, and event as params
    #     - return a string to print, None, or False
    # Returning a False does nothing, forcing users to correct mistakes

    macro_hex = {}

    def execute(self, input_text, output_text, event):
        """Extract command and call appropriate function."""
        parts = input_text.strip().split(maxsplit=1)
        command = parts[0].lower()
        if len(parts) == 2:
            arg = parts[1]
        else:
            arg = ''
        try:
            func = getattr(self, 'do_' + command)
        except AttributeError:
            return False
        return func(arg, output_text, event)


    def commands(self):
        commands = [a[3:] for a in dir(self.__class__) if a.startswith('do_')]
        return commands


    def meta_dict(self):
        meta_dict = {}
        for command in self.commands():
            # TODO: find a better way to do this than eval
            meta_dict[command] = eval('self.do_' + command + '.__doc__')
        return meta_dict


    def do_clear(self, input_text, output_text, event):
        """Clear the screen."""
        return ''


    def do_connect(self, input_text, output_text, event):
        """Generate a session with a single serial device to interact with it."""
        parts = input_text.split()
        devices = [x.device for x in serial.tools.list_ports.comports()]
        if len(parts) > 0:
            device = parts[0]
            if len(parts) > 1:
                baudrate = parts[1]
            else:
                baudrate = 9600
            if device in devices:
                event.app.session = serial.Serial(
                    port=device,
                    baudrate=baudrate,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS)
                # initiate a serial session and return success message
                event.app.session.isOpen()
                output_text += 'Connect session opened with {}\n'.format(device)
                return output_text
        # return list of devices if command incomplete or incorrect
        output_text += 'Valid devices: ' + ', '.join(devices) + '\n'
        return output_text


    def do_close(self, input_text, output_text, event):
        """Close a session."""
        if type(event.app.session) != serial.Serial:
            output_text += 'Connect to a device first\n'
            return output_text
        else:
            device = event.app.session.port
            event.app.session.close()
            output_text += 'Session with {} closed.'.format(device) + '\n'
            event.app.session = ''
        return output_text


    def do_help(self, input_text, output_text, event):
        """Print application help."""
        output_text += '==================== Help ====================\n'
        output_text += 'Welcome to Control Things Serial, or ctserial\n\n'
        output_text += 'This application allows you to interact directly with '
        output_text += 'serial devices.  You can do this by typing commands at '
        output_text += 'the prompt above, the output of which will appear in '
        output_text += 'this space.\n\n'
        table = []
        for key, value in self.meta_dict().items():
            table.append([key, value])
        output_text += tabulate(table, tablefmt="plain") + '\n'
        output_text += '==============================================\n'
        return output_text


    def do_history(self, input_text, output_text, event):
        """Print current history."""
        output_text += ''.join(event.app.history)
        return output_text


    def do_exit(self, input_text, output_text, event):
        """Exit the application."""
        if type(event.app.session) == serial.Serial:
            event.app.session.close()
        event.app.exit()
        output_text += 'Closing application and all sessions.\n'
        return output_text


    def _send_instruction(self, session, tx_bytes):
        """Send data to serial device"""
        # clear out any leftover data
        try:
            if session.inWaiting() > 0:
                session.flushInput()
            session.write(tx_bytes)
            time.sleep(0.1)
            rx_raw = bytes()
            while session.inWaiting() > 0:
                rx_raw += session.read()
        except BaseException as e:
            output = '\n\n{}'.format(e)
        time.sleep(0.1)
        return rx_raw


    def _format_output(self, raw_bytes, output_format, prefix=''):
        """ Return hex and utf-8 decodes aligned on two lines """
        if len(raw_bytes) == 0:
            return prefix + 'None'
        table = []
        if output_format == 'hex' or output_format == 'mixed':
            hex_out = [prefix] + list(bytes([x]).hex() for x in raw_bytes)
            table.append(hex_out)
        if output_format == 'ascii' or output_format == 'mixed':
            ascii_out = [' ' * len(prefix)] + list(raw_bytes.decode('ascii', 'replace'))
            table.append(ascii_out)
        if output_format == 'utf-8':
            # TODO: track \xefbfdb and replace with actual sent character
            utf8 = raw_bytes.decode('utf-8', 'replace')
            utf8_hex_out = [prefix] + list(x.encode('utf-8').hex() for x in utf8)
            utf8_str_out = [' ' * len(prefix)] + list(utf8)
            table = [utf8_hex_out, utf8_str_out]
        return tabulate(table, tablefmt="plain", stralign='right')


    def do_sendhex(self, input_text, output_text, event):
        """Send raw hex to serial device."""
        if type(event.app.session) != serial.Serial:
            output_text += 'Connect to a device first\n'
            return output_text
        data = input_text.lower().replace("0x", "")
        if re.match('^[0123456789abcdef\\\\x ]+$', data):
            raw_hex = re.sub('[\\\\x ]', '', data)
            if len(raw_hex) % 2 == 0:
                tx_bytes = bytes.fromhex(raw_hex)
                session = event.app.session
                rx_bytes = self._send_instruction(session, tx_bytes)
                output_text += self._format_output(tx_bytes, event.app.output_format, prefix='--> ') + '\n'
                output_text += self._format_output(rx_bytes, event.app.output_format, prefix='<-- ') + '\n'
                return output_text
        return False

    def do_setmacro(self, input_text, output_text, evnt):
        v1 = input_text[: input_text.find(' ')]
        v2 = input_text[input_text.find(' '): ]
        self.macro_hex[v1] = v2
        output_text += "key " + v1 + " set to value " + v2 + "\n"
        return output_text

    def do_sendmacro(self, input_text, output_text, event):
        macro = self.macro_hex[input_text]
        if macro:
            return self.do_sendhex(macro, output_text, event)
        output_text += 'Unknown macro\n'
        return output_text

    def do_send(self, input_text, output_text, event):
        """Send string to serial device."""
        if type(event.app.session) != serial.Serial:
            output_text += 'Connect to a device first\n'
            return output_text
        if len(input_text) > 0:
            # remove spaces not in quotes and format
            string = ''.join(shlex.split(input_text))
            tx_bytes = bytes(string, encoding='utf-8')
            session = event.app.session
            rx_bytes = self._send_instruction(session, tx_bytes)
            output_text += self._format_output(tx_bytes, event.app.output_format, prefix='--> ') + '\n'
            output_text += self._format_output(rx_bytes, event.app.output_format, prefix='<-- ') + '\n'
            return output_text
        return False
