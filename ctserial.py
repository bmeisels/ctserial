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
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.contrib.completers import WordCompleter
try:
    import better_exceptions
except ImportError as err:
    pass


help_text = """Connected to serial device {}

Available commands:
    hex HEX         send hex data (example: "hex 56ffff00080a0007")
    ascii ASCII     send ASCII data
    exit            exit application

Press Control-C to exit.
"""
def as_hex_chars(charcode):
    return str.format('{:02x}', charcode)

def as_normal_chars(charcode):
    if (64 < charcode < 123) or (58 > charcode > 47):
        return chr(charcode)
    return '_'

def as_mixed_chars(charcode):
    if (64 < charcode < 123) or (58 > charcode > 47):
        return '\033[92m {0}\033[0m'.format(chr(charcode))
    if charcode == 32:
        return ' _'
    if charcode == ord('.'):
        return ' .'
    if charcode == 255:
        return '\033[2m{0}\033[0m'.format(as_hex_chars(charcode))
    return as_hex_chars(charcode)


def format_output(raw_bytes):
    """ Return hex and ascii decodes aligned on two lines """
    hex_out = ''.join(map(as_hex_chars, raw_bytes))
    ascii_out = ' '.join(map(as_normal_chars, raw_bytes))
    return (hex_out, ascii_out)


def send_instruction(ser, tx_raw):
    """Send data to serial device"""
    # clear out any leftover data
    if ser.inWaiting() > 0:
        ser.flushInput()
    ser.write(tx_raw)
    time.sleep(0.1)
    rx_raw = []
    while ser.inWaiting() > 0:
        rx_raw.append(ord(ser.read()))
    time.sleep(0.1)
    rx_hex = ''.join(map(as_hex_chars, rx_raw))
    rx_str = ' '.join(map(as_normal_chars, rx_raw))
    return '          <-- {}\n               {}'.format(rx_hex, rx_str)
    # return rx_raw


def parse_command(input_text, event):
    parts = input_text.split()
    command = parts[0]
    data = parts[1:]
    if command.lower() == 'hex':
        raw_str = ''.join(data)
        return bytes.fromhex(raw_str)
    elif command.lower() == 'ascii':
        return b''.join(data)
    elif command.lower() == 'exit':
        event.app.set_result(None)
    else:
        ''


def application(ser):
    # The layout.
    output_field = TextArea(
        style='class:output-field',
        text=help_text.format(ser.port))
    completer = WordCompleter(['hex', 'bin', 'ascii'])
    input_field = TextArea(
        height=1,
        prompt='>>> ',
        style='class:input-field',
        completer=completer)

    container = HSplit([
        input_field,
        Window(height=1, char='-', style='class:line'),
        output_field])

    # The key bindings.
    kb = KeyBindings()

    @kb.add('enter', filter=has_focus(input_field))
    def _(event):
        tx_raw = parse_command(input_field.text, event)
        try:
            rx_raw = str(send_instruction(ser, tx_raw))
        except BaseException as e:
            rx_raw = '\n\n{}'.format(e)

        output = output_field.text
        # output += 'tx_raw = ' + str(tx_raw) + '    type= ' + str(type(tx_raw))
        # output += 'rx_raw = ' + str(format_output(rx_raw))
        output += '{} -->\n'.format(tx_raw)
        output += rx_raw
        # output += '          <-- {[0]}\n               {[1]}'.format(format_output(rx_raw))

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
        ('output-field', 'bg:#000000 #ffffff'),
        ('input-field', 'bg:#000000 #ffffff'),
        ('line',        '#004400'),
    ])

    # Run application.
    application = Application(
        layout=Layout(container, focused_element=input_field),
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
