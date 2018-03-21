# Control Things Serial

ctserial is a tool for sniffing serial devices:

    $ ctserial.py --ascii --timing-print \
      --tty /dev/ttyS0:SB9600d \
      --tty "/dev/ttyUSB0:Motorola MTM800" \
      --read
    2015-08-30 13:23:49.461075: SB9600d
    00 00 05 3B 0D 00 00 05                         ...;....
    2015-08-30 13:23:49.461113: Motorola MTM800
    00 05 3B 0D 00 00 05 3B 0D                      ..;....;.
    2015-08-30 13:23:49.473074: SB9600d
    3B 0D 00 00 05 3B 0D                            ;....;.
    2015-08-30 13:23:49.473105: Motorola MTM800
    00 12 05 06 39 00 12 05 06 39 1F 00 22 80 00 0E ....9....9.."...
    $

### Functionality

Not all command line parameters and their functionality are implemented so far,
but the most important ones are:

* `--read`
* `--tty NAME:ALIAS`
* `--timing-delta MICROSECONDS`
* `--timing-print`
* `--ascii`
* `--width WIDTH`

#### Examples

One feature that is available in this tool is controlling the baudrates.
This is supported by adding them to the tty device name separated by an `@`:

    jpnevulator.py --ascii --timing-print \
      --tty /dev/ttyUSB0@9600:SENDING \
      --tty /dev/ttyUSB1@9600:RECEIVING \h
      --read

Alternatively, you could also set the baudrate for all of them with the argument `--baudrate BAUDRATE`.

### Platform Independence

Python and the [PySerial][] package this software depends on are available for all major operating systems.

* [PySerial]: http://pyserial.sourceforge.net/

### Author

* Justin Searle <justin@controlthings.io>

Based on the excellent work of Philipp Klaus <philipp.l.klaus@web.de> which can be found at:

* https://github.com/pklaus/jpnevulator.py

Which in turn was a python implementation of:

* [jpnevulator]: http://jpnevulator.snarl.nl/
