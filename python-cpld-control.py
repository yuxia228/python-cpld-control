#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# -----------------------------------------------------------------------------
#
# python-cpld-control.py: cpld-control porting to python
#
# Copyright (c) 2021 Yuya Hamamachi <yuya.hamamachi.sx@renesas.com>
# -----------------------------------------------------------------------------

import time
import sys
import ftd2xx as ftd
import optparse


PIN_TX = 0x01
PIX_RX = 0x02
PIN_RTS = 0x04
PIN_CTS = 0x08
PIN_DTR = 0x10
PIN_DSR = 0x20
PIN_DCD = 0x40
PIN_RI = 0x80
PIN_MOSI = PIN_DCD
PIN_MISO = PIN_DTR
PIN_SCK = PIN_RTS
PIN_SSTBZ = PIN_CTS

CPLD_ADDR_MODE = 0x00     # /* RW */
CPLD_ADDR_MUX = 0x02      # /* RW */
CPLD_ADDR_DIPSW6 = 0x08   # /* R */
CPLD_ADDR_RESET = 0x80    # /* RW */
CPLD_ADDR_VERSION = 0xFF  # /* R */

FTDI_BITMODE_RESET = 0x00
FTDI_BITMODE_ASYNC_BITBANG = 0x01
FTDI_BITMODE_SYNC_BITBANG = 0x04


def usleep(x): return time.sleep(x/1000000.0)


def ftdi_write_data(d, data, data_size):
    _data = data[0:data_size]
    s = str(bytearray(_data)) if sys.version_info < (3,) else bytes(_data)
    d.purge()
    return d.write(s)


def ftdi_read_data(d, nbytes):
    s = d.read(nbytes, False)
    return [ord(c) for c in s] if type(s) is str else list(s)


def cpld_sync(d):
    dat = [None] * (2 * 32)
    cmd = [None] * ((2 * 8) + 2)
    addr = 0xfe
    bit = 0

    # Do this to somehow synchronize the CPLD and let it communicate.
    for i in range(0, 32):
        dat[(2 * i) + 0] = PIN_SSTBZ | PIN_SCK
        dat[(2 * i) + 1] = PIN_SSTBZ

    dat[(2 * 31) + 0] = PIN_MOSI | PIN_SSTBZ | PIN_SCK
    dat[(2 * 31) + 1] = PIN_MOSI | PIN_SSTBZ

    ret = ftdi_write_data(d, dat, len(dat))

    for i in range(0, 8):
        bit = PIN_MOSI if (addr & (1 << 7)) else 0
        cmd[(2 * i) + 0] = bit | PIN_SSTBZ | PIN_SCK
        cmd[(2 * i) + 1] = bit | PIN_SSTBZ
        addr <<= 1

    cmd[(2 * 8) + 0] = PIN_MOSI | PIN_SCK
    cmd[(2 * 8) + 1] = PIN_MOSI

    ret = ftdi_write_data(d, cmd, len(cmd))


def cpld_write(d, addr, data):
    cmd = [None] * ((2 * 8) + 2)
    dat = [None] * (2 * 32)

    for i in range(0, 32):
        bit = PIN_MOSI if (data & (1 << 31)) else 0
        dat[(2 * i) + 0] = bit | PIN_SSTBZ | PIN_SCK
        dat[(2 * i) + 1] = bit | PIN_SSTBZ
        data <<= 1

    ret = ftdi_write_data(d, dat, len(dat))

    for i in range(0, 8):
        bit = PIN_MOSI if (addr & (1 << 7)) else 0
        cmd[(2 * i) + 0] = bit | PIN_SSTBZ | PIN_SCK
        cmd[(2 * i) + 1] = bit | PIN_SSTBZ
        addr <<= 1

    cmd[(2 * 8) + 0] = PIN_MOSI | PIN_SCK
    cmd[(2 * 8) + 1] = PIN_MOSI
    ret = ftdi_write_data(d, cmd, len(cmd))


def cpld_read(d, addr):
    cmd = [None] * ((2 * 8) + 2)
    pin_data = 0
    data = 0
    bit = 0

    for i in range(0, 8):
        bit = PIN_MOSI if (addr & (1 << 7)) else 0
        cmd[(2 * i) + 0] = bit | PIN_SSTBZ | PIN_SCK
        cmd[(2 * i) + 1] = bit | PIN_SSTBZ
        addr <<= 1

    cmd[(2 * 8) + 0] = PIN_SCK
    cmd[(2 * 8) + 1] = 0
    ret = ftdi_write_data(d, cmd, len(cmd))
    ftdi_read_data(d, 1)

    for i in range(0, 32):
        cmd[(2 * 0) + 0] = PIN_SSTBZ | PIN_SCK
        cmd[(2 * 0) + 1] = PIN_SSTBZ
        ret = ftdi_write_data(d, cmd, 2)

        data_num = 2
        pin_data = ftdi_read_data(d, data_num)
        pin_data = not not (pin_data[1] & PIN_MISO)
        data = (data << 1) | pin_data;

    return data


def cpld_dump(d):
    print("CPLD version:\t\t\t0x{:02x} : 0x{:08x}".format(
        CPLD_ADDR_VERSION, cpld_read(d, CPLD_ADDR_VERSION)))
    print("Mode setting (MD0..28)\t\t0x{:02x} : 0x{:08x}".format(
        CPLD_ADDR_MODE, cpld_read(d, CPLD_ADDR_MODE)))
    print("Multiplexer settings:\t\t0x{:02x} : 0x{:08x}".format(
        CPLD_ADDR_MUX, cpld_read(d, CPLD_ADDR_MUX)))
    print("DIPSW (SW6):\t\t\t0x{:02x} : 0x{:08x}".format(
        CPLD_ADDR_DIPSW6, cpld_read(d, CPLD_ADDR_DIPSW6)))


def cpld_list():
    serials = ftd.listDevices()
    for i in serials:
        d = ftd.openEx(i)
        info = d.getDeviceInfo()
        if sys.platform == "win32":
            com  = d.getComPortNumber()
            print("COM", com, ":", info)
        else:
            print(info)
        d.close()


def cpld_help(pn):
    print("CPLD control");
    print("{} [-h] ............................... Print this help.".format(pn))
    print("{} -l ................................. List available devices.".format(pn))
    print("{} -d <FTDI iSerial> .................. Dump CPLD registers.".format(pn))
    print("{} -w <FTDI iSerial> [<reg> <val>]* ... Write CPLD register(s).".format(pn))
    print("      *One or more [<reg> <val>] pairs can be specified.");


def main(args):
    pn = args.pop(0)
    if len(args) == 0 or args[0] == "-h":
        cpld_help(pn)
        quit()
    elif args[0] == "-l":
        cpld_list()
        quit()

    parser = optparse.OptionParser()
    parser.add_option('-d', action="store_true", default=False)
    parser.add_option('-l', action="store_true", default=False)
    parser.add_option('-w', action="store_true", default=False)
    _opts, _args = parser.parse_args(args)

    d = "" # ftd.open(0)    # Open first FTDI device
    if len(_args) >= 1:
        d = ftd.openEx(_args[0].encode())    # Open first FTDI device
        _args.pop(0)
    else:
        cpld_help(pn)
        quit()

    d.resetDevice()
    d.setBaudRate(921600)
    d.setBitMode(PIN_MOSI | PIN_SCK | PIN_SSTBZ, FTDI_BITMODE_SYNC_BITBANG)

    if _opts.l is True:
        help()
        quit()

    cpld_sync(d)
    if _opts.d is True:
        cpld_dump(d)
    elif _opts.w is True:
        while len(_args) >= 2:
            addr = int(_args[0], 0)
            val = int(_args[1], 0)

            print("Write => ", hex(addr), ":", hex(val))
            cpld_write(d, addr, val)
            cpld_dump(d)

            del _args[:2]


    d.setBitMode(PIN_MOSI | PIN_SCK | PIN_SSTBZ, FTDI_BITMODE_RESET)
    d.setBaudRate(115200)
    d.resetDevice()
    d.close()


if __name__ == '__main__':
    main(sys.argv)

