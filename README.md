# Control Things Serial

ctserial is a security professional's swiss army knife for interacting with raw serial devices

# Usage:

ctserial connect /dev/your-serial-device

This opens the ctserial application conntect to your serial device.  From there you have a prompt to interact with your serial device, complete with tab completion.  For example:

  ctmodbus> sendhex deadc0de
  ctmodbus> send "Dead Code 国"
  ctmodbus> exit

# Platform Independence

Python and the [PySerial][] package this software depends on are available for all major operating systems.

* [PySerial]: http://pyserial.sourceforge.net/

# Author

* Justin Searle <justin@controlthings.io>

Based on the excellent work of Philipp Klaus <philipp.l.klaus@web.de> which can be found at:

* https://github.com/pklaus/jpnevulator.py

Which in turn was a python implementation of:

* [jpnevulator]: http://jpnevulator.snarl.nl/
