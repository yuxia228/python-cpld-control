# python-cpld-control

This software is ported to python3 from [cpld-control](https://github.com/marex/cpld-control)
This is used for reading/writing cpld equipped on R-Car Gen3 ULCB.

# System requirement

I confirmed following environment.

- OS
  - Windows 10
  - Ubuntu 18.04 x64
- python version
  - python 3.7.3 (Windows)
  - python 3.6.9 (Ubuntu)

# Usage

## Iniital Setup

### Windows case

1. Install python3 to your system.
   https://www.python.org/downloads/windows/
2. Install ftd2xx.
   ```
   pip install ftd2xx
   ```

### Linux Case

1. Install ftd2xx.
   ```
   pip3 install ftd2xx
   ```
2. Install "libftd2xx.so"
   - Download "libftd2xx.so" from [FTDI HomePage](https://ftdichip.com/drivers/d2xx-drivers/), and install to your system.
     - See also: https://ftdichip.com/wp-content/uploads/2020/08/AN_220_FTDI_Drivers_Installation_Guide_for_Linux-1.pdf
       > memo: I tried https://www.ftdichip.com/Drivers/D2XX/Linux/libftd2xx0.4.16_x86_64.tar.gz and it works.

## Function

```
bash $ python3 ./python-cpld-control.py -h
CPLD control
./python-cpld-control.py [-h] ............................... Print this help.
./python-cpld-control.py -l ................................. List available devices.
./python-cpld-control.py -d <FTDI iSerial> .................. Dump CPLD registers.
./python-cpld-control.py -w <FTDI iSerial> [<reg> <val>]* ... Write CPLD register(s).
      *One or more [<reg> <val>] pairs can be specified.
```

## Known issue

### The error message "AttributeError: /usr/lib/libftd2xx.so: undefined symbol: stime" is shown.

According to the [1], this is caused when using newer kernel version( >= 5.4).
Please use [cpld-control](https://github.com/marex/cpld-control) instead of this program.

* [1] https://github.com/abhra0897/gowin-easy-linux


