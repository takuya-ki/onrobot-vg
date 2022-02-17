#!/usr/bin/env python3

import time
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
    """Same as the one of channel B."""
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
    """Same as the one of channel B."""
    if modename == "Release":
        modeval = 0x0000
    elif modename == "Grip":
        modeval = 0x0100
    elif modename == "Idle":
        modeval = 0x0200
    result = client.write_register(address=1, value=modeval+command, unit=65)


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

    time.sleep(1.0)
    print("Vacuum limit [mA]: " +
          str(get_vacuum_limit(client)))

    # channel A
    set_channelA_control(client, "Grip", 0x00ff)  # 100% vacuum
    time.sleep(2.0)
    # if sth was gripped, the value is changed
    print("Current channelA's vacuum: " +
          str(get_channelA_vacuum(client)))
    time.sleep(1.0)
    set_channelA_control(client, "Release", 0x0000)  # 0% vacuum
    # channel B
    set_channelB_control(client, "Grip", 0x00ff)  # 100% vacuum
    time.sleep(2.0)
    # if sth was gripped, the value is changed
    print("Current channelB's vacuum: " +
          str(get_channelB_vacuum(client)))
    time.sleep(1.0)
    set_channelB_control(client, "Release", 0x0000)  # 0% vacuum

    client.close()


if __name__ == '__main__':
    toolchanger_ip = "192.168.1.1"
    toolchanger_port = "502"
    run_demo()
