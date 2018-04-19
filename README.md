# Control Things Serial

ctserial is a security professional's swiss army knife for interacting with raw serial devices

# Installation:

As long as you have git and Python 3.5 or later installed, all you should need to do is:

```
git clone https://github.com/ControlThingsTools/ctserial.git
cd ctserial
pip3 install -r requirements.txt
```

# Usage:

First, start the tool from a terminal, specifying which serial device you want to connect to:

```
ctserial connect /dev/your-serial-device
```

This opens the ctserial application conntect to your serial device.  From there you have a prompt to interact with your serial device, complete with tab completion.  For example:

```
ctmodbus> sendhex deadc0de        (sends actual hex, so 4 bytes)
ctmodbus> sendhex \xde \xad c0de  (sends same hex as before, ignoring spaces and \x)
ctmondus> send Dead Code 国        (sends full utf-8 string without spaces)
ctmodbus> send "Dead Code 国"      (Use quotes if you need spaces)
ctmodbus> exit
```

# Platform Independence

Python 3.5+ and all dependencies are available for all major operating systems.  It is primarily developed on MacOS and Linux, but should work in Windows as well.

# Author

* Justin Searle <justin@controlthings.io>

Based on the excellent work of Philipp Klaus <philipp.l.klaus@web.de> which can be found at:

* (https://github.com/pklaus/jpnevulator.py)

Which in turn was a python implementation of:

* [jpnevulator](http://jpnevulator.snarl.nl/)
