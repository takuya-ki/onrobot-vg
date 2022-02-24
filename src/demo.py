#!/usr/bin/env python3

import time
import argparse
from pymodbus.client.sync import ModbusTcpClient as ModbusClient


def get_vacuum_limit(client):
    """Set and read the current limit.
       The limit is provided and must be given in mA (milli-amperes).
       The limit is 500mA per default and should never be set above 1000 mA.
    """
    result = client.read_holding_registers(address=2, count=1, unit=65)
    limit_mA = result.registers[0]
    return limit_mA


def get_channelA_vacuum(client):
    """Reads the actual vacuum on Channel A.
       The vacuum is provided in 1/1000 of relative vacuum.
       Please note that this differs from the setpoint given in percent,
       as extra accuracy is desirable on the actual vacuum.
    """
    result = client.read_holding_registers(address=258, count=1, unit=65)
    vacuum = result.registers[0]
    return vacuum


def get_channelB_vacuum(client):
    """Same as the one of channel A."""
    result = client.read_holding_registers(address=259, count=1, unit=65)
    vacuum = result.registers[0]
    return vacuum


def set_channelA_control(client, modename, command):
    """This register allows for control of channel A.
       
       The register is split into two 8-bit fields:
       Bits 15-8        Bits 7-0
       Control mode     Target vacuum

       The Control mode field must contain one of these three values:

       Value    Name    Description
       0 (0x00) Release Commands the channel to release
                        any work item and stop the pump,
                        if not required by the other channel.
       1 (0x01) Grip    Commands the channel to build up
                        and maintain vacuum on this channel.
       2 (0x02) Idle    Commands the channel to neither release nor grip.
                        Workpieces may "stick" to the channel
                        if physically pressed towards its vacuum cups,
                        but the VG will use slightly less power.

        The Target vacuum field sets the level of vacuum
        to be build up and maintained by the chann el.
        It is used only when the control mode is 1 (0x01) / Grip.
        The target vacuum should be provided in % vacuum.
        It should never exceed 80.

        Examples:
        Setting the register value 0 (0x0000)
            will command the VG to release the work item.
        Setting the register value 276 (0x0114)
            will command the VG to grip at 20 % vacuum.
        Setting the register value 296 (0x0128)
            will command the VG to grip at 40 % vacuum.
        Setting the register value 331 (0x014B)
            will command the VG to grip at 75 % vacuum.
        Setting the register value 512 (0x0200)
            will command the VG to idle the channel.
    """
    if modename == "Release":
        modeval = 0x0000
    elif modename == "Grip":
        modeval = 0x0100
    elif modename == "Idle":
        modeval = 0x0200
    result = client.write_register(address=0, value=modeval+command, unit=65)


def set_channelB_control(client, modename, command):
    """Same as the one of channel A."""
    if modename == "Release":
        modeval = 0x0000
    elif modename == "Grip":
        modeval = 0x0100
    elif modename == "Idle":
        modeval = 0x0200
    result = client.write_register(address=1, value=modeval+command, unit=65)


def vacuum_on(client, sleep_sec=1.0):
    """Turns on all vacuums."""
    modeval = 0x0100  # grip
    command = 0x00ff  # 100 % vacuum
    commands = [modeval+command, modeval+command]
    result = client.write_registers(address=0, values=commands, unit=65)

    print("Turn on all vacuums.") 
    start = time.time()
    while True:
        print("Current channelA's vacuum: " +
              str(get_channelA_vacuum(client)))
        print("Current channelB's vacuum: " +
              str(get_channelB_vacuum(client)))
        if time.time() - start > sleep_sec:
            break


def release_vacuum(client):
    """Releases all vacuums"""
    modeval = 0x0000  # release
    command = 0x0000  # 0 % vacuum
    commands = [modeval+command, modeval+command]

    print("Release all vacuums.")
    result = client.write_registers(address=0, values=commands, unit=65)
    time.sleep(1.0)


def vacuum_on_channelA(client, sleep_sec=1.0):
    """Turns on the vacuum of channel A."""
    modeval = 0x0100  # grip
    command = 0x00ff  # 100 % vacuum
    result = client.write_register(address=0, value=modeval+command, unit=65)

    print("Turn on the vacuum of channel A.") 
    start = time.time()
    while True:
        print("Current channelA's vacuum: " +
              str(get_channelA_vacuum(client)))
        if time.time() - start > sleep_sec:
            break


def vacuum_on_channelB(client, sleep_sec=1.0):
    """Turns on the vacuum of channel B."""
    modeval = 0x0100  # grip
    command = 0x00ff  # 100 % vacuum
    result = client.write_register(address=1, value=modeval+command, unit=65)

    print("Turn on the vacuum of channel B.") 
    start = time.time()
    while True:
        print("Current channelB's vacuum: " +
              str(get_channelB_vacuum(client)))
        if time.time() - start > sleep_sec:
            break


def release_vacuum_channelA(client):
    """Releases the vacuum of channel A."""
    modeval = 0x0000  # release
    command = 0x0000  # 0 % vacuum
    print("Release the vacuum of channel A.") 
    result = client.write_register(address=0, value=modeval+command, unit=65)
    time.sleep(1.0)


def release_vacuum_channelB(client):
    """Releases the vacuum of channel B."""
    modeval = 0x0000  # release
    command = 0x0000  # 0 % vacuum
    print("Release the vacuum of channel B.") 
    result = client.write_register(address=1, value=modeval+command, unit=65)
    time.sleep(1.0)


def get_options():
    """Returns user-specific options."""
    parser = argparse.ArgumentParser(description='Set options.')
    parser.add_argument(
        '--ip', dest='ip', type=str, default="192.168.1.1",
        help='set ip address')
    parser.add_argument(
        '--port', dest='port', type=str, default="502",
        help='set port number')
    return parser.parse_args()


def run_demo():
    """Runs pump on/off demonstration once."""
    client = ModbusClient(
        toolchanger_ip,
        port=toolchanger_port,
        stopbits=1,
        bytesize=8,
        parity='E',
        baudrate=115200,
        timeout=1)
    client.connect()

    print("Vacuum limit [mA]: " +
          str(get_vacuum_limit(client)))

    vacuum_on(client, sleep_sec=2.0)
    release_vacuum(client)
    vacuum_on_channelA(client, sleep_sec=2.0)
    release_vacuum_channelA(client)
    vacuum_on_channelB(client, sleep_sec=2.0)
    release_vacuum_channelB(client)
    client.close()


if __name__ == '__main__':
    args = get_options()
    toolchanger_ip = args.ip
    toolchanger_port = args.port
    run_demo()
