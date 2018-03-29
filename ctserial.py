#!/usr/bin/env python3
"""
Control Things Serial, aka ctserial.py

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
"""

import click
import sys
import serial
import re
import time
from prompt_toolkit.application import Application
from prompt_toolkit.document import Document
from prompt_toolkit.filters import has_focus
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window, FloatContainer, Float
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.contrib.completers import WordCompleter
from tabulate import tabulate
try:
    import better_exceptions
except ImportError as err:
    pass


intro = 'Connected to serial device {}\nEntering Hex mode\n\n'


def format_output(raw_bytes, prefix='', mode='hex'):
    """ Return hex and utf-8 decodes aligned on two lines """
    if len(raw_bytes) == 0:
        return prefix + 'None'
    elif mode == 'hex' or mode == 'ascii':
        hex_out = [prefix] + list(bytes([x]).hex() for x in raw_bytes)
        ascii_out = [' ' * len(prefix)] + list(raw_bytes.decode('ascii', 'replace'))
        table = [hex_out, ascii_out]
    elif mode == 'utf-8':
        # TODO: track \xefbfdb and replace with actual sent character
        utf8 = raw_bytes.decode('utf-8', 'replace')
        utf8_hex_out = [prefix] + list(x.encode('utf-8').hex() for x in utf8)
        utf8_str_out = [' ' * len(prefix)] + list(utf8)
        table = [utf8_hex_out, utf8_str_out]
    else:
        return prefix + 'Invalid Mode'
    return tabulate(table, tablefmt="plain", stralign='right')


def send_instruction(ser, tx_bytes):
    """Send data to serial device"""
    # clear out any leftover data
    if ser.inWaiting() > 0:
        ser.flushInput()
    ser.write(tx_bytes)
    time.sleep(0.1)
    rx_raw = bytes()
    while ser.inWaiting() > 0:
        rx_raw += ser.read()
    time.sleep(0.1)
    return rx_raw
    # return rx_raw


def parse_command(input_text, event):
    """Extract command and prepare data to send if applicable"""
    parts = input_text.strip().split(maxsplit=1)
    command = parts[0].lower()
    if command == 'exit':
        event.app.set_result(None)
        return (None, None)
    data = parts[1]
    if command == 'hex':
        if re.match('^[0123456789abcdef\\\\x \'\"]+$', data):
            raw_hex = re.sub('[\\\\x \'\"]', '', data)
            if len(raw_hex) % 2 == 0:
                mode = command
                return (bytes.fromhex(raw_hex), mode)
    elif command == 'ascii' or command == 'utf-8':
        mode = command
        return (bytes(data, encoding='utf-8'), mode)


def application(ser):
    # The layout.
    output_field = TextArea(
        style='class:output-field',
        text=intro.format(ser.port))
    completer = WordCompleter(['hex', 'bin', 'ascii', 'utf-8'])
    history = InMemoryHistory()
    input_field = TextArea(
        height=1,
        prompt='>>> ',
        style='class:input-field',
        completer=completer)

    body = FloatContainer(
        HSplit([
            input_field,
            Window(height=1, char='-', style='class:line'),
            output_field ]),
        floats=[
            Float(xcursor=True,
                  ycursor=True,
                  content=CompletionsMenu(max_height=16, scroll_offset=1)) ] )

    # The key bindings.
    kb = KeyBindings()

    @kb.add('enter', filter=has_focus(input_field))
    def _(event):
        (tx_bytes, mode) = parse_command(input_field.text, event)
        if type(tx_bytes) != bytes:
            return

        try:
            rx_bytes = send_instruction(ser, tx_bytes)
        except BaseException as e:
            rx_bytes = '\n\n{}'.format(e)

        output = output_field.text
        output += format_output(tx_bytes, prefix='--> ', mode=mode) + '\n'
        output += format_output(rx_bytes, prefix='<-- ', mode=mode) + '\n'

        output_field.buffer.document = Document(
            text=output, cursor_position=len(output))
        input_field.text = ''

    @kb.add('c-c')
    @kb.add('c-q')
    def _(event):
        " Pressing Ctrl-Q or Ctrl-C will exit the user interface. "
        ser.close()
        event.app.set_result(None)

    style = Style([
        # ('output-field', 'bg:#000000 #ffffff'),
        # ('input-field', 'bg:#000000 #ffffff'),
        ('line',        '#004400'),
    ])

    # Run application.
    application = Application(
        layout=Layout(body, focused_element=input_field),
        key_bindings=kb,
        style=style,
        mouse_support=True,
        full_screen=True)

    application.run()


@click.group()
def main():
    pass


@main.command()
@click.argument('device', type=click.Path(exists=True))
@click.argument('baudrate', default=9600)
def connect(device, baudrate):
    """Connect to a serial device to interact with it"""
    print('entering connect')
    ser = serial.Serial(
        port=device,
        baudrate=baudrate,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS)
    # initiate a serial connection
    ser.isOpen()
    # start full screen application
    application(ser)


if __name__ == '__main__':
    main()
