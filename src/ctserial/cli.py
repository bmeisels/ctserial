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

from argparse import ArgumentParser as Argp
from .commands import Commands
from .application import start_app
try:
    import better_exceptions
except ImportError as err:
    pass


def main():
    """Start application but allow passing of commands that create sessions"""
    # cmd = Commands()
    # p = Argp(description='ctserial is a security professional\'s swiss army knife for interacting with raw serial devices')
    # subp = p.add_subparsers(dest='session')
    #
    # # Connect
    # p_conn = subp.add_parser('connect', help=cmd.do_connect.__doc__)
    # p_conn.add_argument('device', type=str,
    #                     help='open a /dev/... serial file or COM port')
    # p_conn.add_argument('baudrate', nargs='?', type=int, default=9600, help='baudrate ')

    # # Sniff
    # p_sniff = subp.add_parser('sniff', help='')
    # p_sniff.add_argument('', help='')

    # # Proxy
    # p_proxy = subp.add_parser('proxy', help=cmd.do_proxy.__doc__)
    # p_proxy.add_argument('', help='')

    # args = p.parse_args()
    # start_app(args)
    start_app([])


if __name__ == '__main__':
    main()
