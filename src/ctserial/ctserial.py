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
import time
from .commands import Commands
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
try:
    import better_exceptions
except ImportError as err:
    pass


class MyApplication(Application):
    connection = ''
    mode = ''
    output_format = 'mixed'
    output_format = 'utf-8'


def get_statusbar_text():
    sep = ' - '
    mode = 'mode:' + get_app().mode
    device = 'connected:' + get_app().connection.port
    output_format = 'output:' + get_app().output_format
    return sep.join([mode, device, output_format])
    # return 'text'


def start_app(mode, connection):
    """Text-based GUI application"""
    cmd = Commands()
    completer = WordCompleter(cmd.commands(), meta_dict=cmd.meta_dict(), ignore_case=True)
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
            MenuItem('Project ', children=[
                MenuItem('New'),
                MenuItem('Open'),
                MenuItem('Save'),
                MenuItem('Save as...'),
                MenuItem('-', disabled=True),
                MenuItem('Exit', handler=cmd.do_exit),  ]),
            MenuItem('View ', children=[
                MenuItem('Split'),  ]),
            MenuItem('Info ', children=[
                MenuItem('Help'),
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
        # tx_bytes = parse_command(input_field.text, event=event)
        output_text = cmd.execute(input_field.text, output_field.text, event)

        # For commands that do not send data to serial device
        if output_text == None:
            input_field.text = ''
            return
        # For invalid commands forcing users to correct them
        elif output_text == False:
            return
        # For invalid commands forcing users to correct them
        else:
            output_field.buffer.document = Document(
                text=output_text, cursor_position=len(output_text))
            input_field.text = ''

    @kb.add('c-c')
    @kb.add('c-q')
    def _(event):
        " Pressing Ctrl-Q or Ctrl-C will exit the user interface. "
        connection.close()
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
    application.mode = mode
    application.connection = connection
    application.run()


@click.group()
def main():
    pass


@main.command()
@click.argument('device', type=str)
@click.argument('baudrate', default=9600)
def connect(device, baudrate):
    """Connect to a serial device to interact with it"""
    print('entering connect')
    connection = serial.Serial(
        port=device,
        baudrate=baudrate,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS)
    # initiate a serial connection
    connection.isOpen()
    # start full screen application
    start_app(mode='connect', connection=connection)


if __name__ == '__main__':
    main()
