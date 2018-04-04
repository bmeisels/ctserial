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
import time
from prompt_toolkit.application.current import get_app
from prompt_toolkit.document import Document
from tabulate import tabulate


class Commands(object):
    """Commands that users may use at the application prompt."""
    # Each function that users can call must:
    #     - start with a do_
    #     - accept self and event as params
    #     - return a string to print, None, or False
    # Returning a False does nothing, forcing users to correct mistakes


    def execute(self, input_text, output_text, event):
        """Extract command and call appropriate function."""
        parts = input_text.strip().split(maxsplit=1)
        command = parts[0].lower()
        if len(parts) == 2:
            arg = parts[1]
        else:
            arg = None
        try:
            func = getattr(self, 'do_' + command)
        except AttributeError:
            return False
        return func(arg, output_text, event)


    def do_help(self, input_text, output_text, event):
        """Print application help."""
        output_text += 'Welcome to Control Things Serial, or ctserial\n\n'
        output_text += 'This application allows you to interact directly with '
        output_text += 'serial devices.  You can do this by typing commands at '
        output_text += 'the prompt above, the output of which will appear in '
        output_text += 'this space.\n'
        return output_text


    def do_exit(self, input_text, output_text, event):
        """Exit the application."""
        event.app.exit()


    def _send_instruction(self, connection, tx_bytes):
        """Send data to serial device"""
        # clear out any leftover data
        try:
            if connection.inWaiting() > 0:
                connection.flushInput()
            connection.write(tx_bytes)
            time.sleep(0.1)
            rx_raw = bytes()
            while connection.inWaiting() > 0:
                rx_raw += connection.read()
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
        data = input_text.lower()
        if re.match('^[0123456789abcdef\\\\x ]+$', data):
            raw_hex = re.sub('[\\\\x ]', '', data)
            if len(raw_hex) % 2 == 0:
                tx_bytes = bytes.fromhex(raw_hex)
                connection = event.app.connection
                rx_bytes = self._send_instruction(connection, tx_bytes)
                output_text += self._format_output(tx_bytes, event.app.output_format, prefix='--> ') + '\n'
                output_text += self._format_output(rx_bytes, event.app.output_format, prefix='<-- ') + '\n'
                return output_text
        return False


    def do_send(self, input_text, output_text, event):
        """Send string to serial device."""
        # remove spaces not in quotes and format
        string = ''.join(shlex.split(input_text))
        tx_bytes = bytes(string, encoding='utf-8')
        connection = event.app.connection
        rx_bytes = self._send_instruction(connection, tx_bytes)
        output_text += self._format_output(tx_bytes, event.app.output_format, prefix='--> ') + '\n'
        output_text += self._format_output(rx_bytes, event.app.output_format, prefix='<-- ') + '\n'
        return output_text
