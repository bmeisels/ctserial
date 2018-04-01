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
from prompt_toolkit.application.current import get_app
from prompt_toolkit.document import Document
from prompt_toolkit.filters import has_focus
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, VSplit, Window, FloatContainer, Float, Align
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.shortcuts.dialogs import message_dialog
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import TextArea, MenuContainer, MenuItem, ProgressBar
from prompt_toolkit.contrib.completers import WordCompleter
from tabulate import tabulate
try:
    import better_exceptions
except ImportError as err:
    pass

class MyApplication(Application):
    device = None
    mode = 'hex'

def get_statusbar_text():
    # sep = '  '
    # dev = 'connected:' + sep
    # mode += 'mode:' + get_app().mode
    # return sep.join([dev,mode])
    return 'mode:' + get_app().mode

def do_exit():
    '''Exit the application'''
    get_app().exit()

def do_cmd():
    get_app().mode = 'cmd'

def do_mode(mode):
    '''Change mode between hex, ascii, and utf-8'''
    get_app().mode = mode

def do_debug():
    '''Starts a Python Debugger session'''
    # import pdb
    # pdb.set_trace()

def format_output(raw_bytes, mode, prefix=''):
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


def format_input(input_text, mode):
    if mode == 'hex':
        if re.match('^[0123456789abcdef\\\\x \'\"]+$', input_text):
            raw_hex = re.sub('[\\\\x \'\"]', '', input_text)
            if len(raw_hex) % 2 == 0:
                return bytes.fromhex(raw_hex)
            else:
                return False
    elif mode == 'ascii' or mode == 'utf-8':
        return bytes(input_text, encoding='utf-8')
    else:
        return False


def parse_command(input_text, event):
    """Return bytes to send, None if nothing to send, or False if invalid"""
    parts = input_text.split(maxsplit=2)
    command = parts[0].lower()
    if command == 'exit':
        event.app.exit()
        return None
    elif command == 'send' and len(parts) >= 2:
        subcommand = parts[1].lower()
        if subcommand in ['hex', 'ascii', 'utf-8'] and len(parts) == 3:
            data = parts[2]
            tx_bytes = format_input(data, subcommand)
            return tx_bytes
    return False


def start_app(ser):
    '''Text-based GUI application'''
    completer = WordCompleter(['hex', 'ascii', 'utf-8'])
    history = InMemoryHistory()

    # Individual windows
    input_field = TextArea(
        height=1,
        prompt='ctserial> ',
        style='class:input-field',
        completer=completer)

    output_field = TextArea(
        scrollbar=True,
        style='class:output-field',
        text='')

    statusbar = Window(
        content = FormattedTextControl(get_statusbar_text),
        height=1,
        style='class:statusbar'  )

    # Organization of windows
    body = FloatContainer(
        HSplit([
            input_field,
            Window(height=1, char='-', style='class:line'),
            output_field,
            statusbar ]),
        floats=[
            Float(xcursor=True,
                  ycursor=True,
                  content=CompletionsMenu(max_height=16, scroll_offset=1)) ] )

    # Adding menus
    root_container = MenuContainer(
        body=body,
        menu_items=[
            MenuItem('Project', children=[
                MenuItem('New'),
                MenuItem('Open'),
                MenuItem('Save'),
                MenuItem('Save as...'),
                MenuItem('-', disabled=True),
                MenuItem('Exit', handler=do_exit),  ]),
            MenuItem('Mode', children=[
                MenuItem('CMD', handler=do_cmd()),
                MenuItem('HEX', handler=do_mode('hex')),
                MenuItem('ASCII', handler=do_mode('ascii')),
                MenuItem('UTF-8', handler=do_mode('utf-8')),  ]),
            MenuItem('View', children=[
                MenuItem('Split'),  ]),
            MenuItem('Info', children=[
                MenuItem('Help'),
                MenuItem('Debug', handler=do_debug()),
                MenuItem('About'),  ]),  ],
        floats=[
            Float(xcursor=True,
                  ycursor=True,
                  content=CompletionsMenu(max_height=16, scroll_offset=1)),  ])

    # The key bindings.
    kb = KeyBindings()

    @kb.add('enter', filter=has_focus(input_field))
    def _(event):
        # Process commands on prompt after hitting enter key
        tx_bytes = parse_command(input_field.text, event=event)

        # For commands that do not send data to serial device
        if tx_bytes == None:
            input_field.text = ''
            return
        # For invalid commands forcing users to correct them
        elif tx_bytes == False:
            return

        # For commands that send data to serial device
        try:
            rx_bytes = send_instruction(ser, tx_bytes)
        except BaseException as e:
            output = '\n\n{}'.format(e)
            output_field.buffer.document = Document(
                text=output, cursor_position=len(output))
            return

        output = output_field.text
        output += format_output(tx_bytes, mode=event.app.mode, prefix='--> ') + '\n'
        output += format_output(rx_bytes, mode=event.app.mode, prefix='<-- ') + '\n'

        output_field.buffer.document = Document(
            text=output, cursor_position=len(output))
        input_field.text = ''

    @kb.add('c-c')
    @kb.add('c-q')
    def _(event):
        " Pressing Ctrl-Q or Ctrl-C will exit the user interface. "
        ser.close()
        event.app.exit()

    @kb.add('c-a')
    def _(event):
        event.app.mode = 'cmd'

    @kb.add('c-d')
    def _(event):
        """Press Ctrl-D for debug mode"""
        import pdb
        pdb.set_trace()

    @kb.add('escape')
    def _(event):
        """ Pressing ESC key will enter toggle input mode"""
        input_field.prompt = 'cmd> '

    style = Style([
        # ('output-field', 'bg:#000000 #ffffff'),
        # ('input-field', 'bg:#000000 #ffffff'),
        ('line',        '#004400'),
        ('statusbar', 'bg:#AAAAAA')  ])

    # Run application.
    application = MyApplication(
        layout=Layout(root_container, focused_element=input_field),
        key_bindings=kb,
        style=style,
        mouse_support=True,
        full_screen=True  )
    # application.device = ser.port
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
    start_app(ser)


if __name__ == '__main__':
    main()
