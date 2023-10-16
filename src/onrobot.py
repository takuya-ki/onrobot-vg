#!/usr/bin/env python3

import time
from pymodbus.client.sync import ModbusTcpClient, ModbusSerialClient



class VG():

    def __init__(self, ip=None, port=None, device=None):
        # Check one of the connection methods is provided
        if not ip and device is None:
            raise Exception("Please provide either an IP address or a serial device.")
        # If both are provided, use the IP address
        if ip and device is not None:
            print("Both IP address and serial device provided. Using the IP address.")
            device = None
        
        # Set the default interface configuration
        config = {
            "stopbits": 1,
            "bytesize": 8,
            "parity": 'E',
            "baudrate": 115200,
            "timeout": 1
        }

        self.client = None
        # Create the client, depending on the connection method
        if ip:
            self.client = self._create_client(ip, port, config)
        if device:
            self.client = self._create_client_serial(device, config)
        assert self.client is not None, "Error creating the client."
        self.open_connection()

    def _create_client(self, ip, port, config):
        """ Creates a TCP client for the VG gripper. """
        client = ModbusTcpClient(
            ip,
            port=port,
            stopbits=config["stopbits"],
            bytesize=config["bytesize"],
            parity=config["parity"],
            baudrate=config["baudrate"],
            timeout=config["timeout"])
        return client
    
    def _create_client_serial(self, serial, config):
        """ Creates a serial client for the VG gripper. """
        client = ModbusSerialClient(
            method='rtu',
            port=serial,
            stopbits=config["stopbits"],
            bytesize=config["bytesize"],
            parity=config["parity"],
            baudrate=config["baudrate"],
            timeout=config["timeout"])
        return client
        
    def open_connection(self):
        """Opens the connection with a gripper."""
        self.client.connect()

    def close_connection(self):
        """Closes the connection with the gripper."""
        self.client.close()

    def get_vacuum_limit(self):
        """Sets and reads the current limit.
        The limit is provided and must be given in mA (milli-amperes).
        The limit is 500mA per default and should never be set above 1000 mA.
        """
        result = self.client.read_holding_registers(
            address=2, count=1, unit=65)
        limit_mA = result.registers[0]
        return limit_mA

    def get_channelA_vacuum(self):
        """Reads the actual vacuum on Channel A.
        The vacuum is provided in 1/1000 of relative vacuum.
        Please note that this differs from the setpoint given in percent,
        as extra accuracy is desirable on the actual vacuum.
        """
        result = self.client.read_holding_registers(
            address=258, count=1, unit=65)
        vacuum = result.registers[0]
        return vacuum

    def get_channelB_vacuum(self):
        """Same as the one of channel A."""
        result = self.client.read_holding_registers(
            address=259, count=1, unit=65)
        vacuum = result.registers[0]
        return vacuum

    def set_channelA_control(self, modename, command):
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
        result = self.client.write_register(
            address=0, value=modeval+command, unit=65)

    def set_channelB_control(self, modename, command):
        """Same as the one of channel A."""
        if modename == "Release":
            modeval = 0x0000
        elif modename == "Grip":
            modeval = 0x0100
        elif modename == "Idle":
            modeval = 0x0200
        result = self.client.write_register(
            address=1, value=modeval+command, unit=65)

    def vacuum_on(self, sleep_sec=1.0):
        """Turns on all vacuums."""
        modeval = 0x0100  # grip
        command = 0x00ff  # 100 % vacuum
        commands = [modeval+command, modeval+command]
        result = self.client.write_registers(
            address=0, values=commands, unit=65)

        print("\nTurn on all vacuums.")
        start = time.time()
        while True:
            print("Current vacuums, channel A: " +
                  str(self.get_channelA_vacuum()) +
                  ", channel B: " +
                  str(self.get_channelB_vacuum()))
            if time.time() - start > sleep_sec:
                break

    def release_vacuum(self):
        """Releases all vacuums"""
        modeval = 0x0000  # release
        command = 0x0000  # 0 % vacuum
        commands = [modeval+command, modeval+command]

        print("\nRelease all vacuums.")
        result = self.client.write_registers(
            address=0, values=commands, unit=65)
        time.sleep(1.0)

    def vacuum_on_channelA(self, sleep_sec=1.0):
        """Turns on the vacuum of channel A."""
        modeval = 0x0100  # grip
        command = 0x00ff  # 100 % vacuum
        result = self.client.write_register(
            address=0, value=modeval+command, unit=65)

        print("\nTurn on the vacuum of channel A.")
        start = time.time()
        while True:
            print("Current channel A's vacuum: " +
                  str(self.get_channelA_vacuum()))
            if time.time() - start > sleep_sec:
                break

    def vacuum_on_channelB(self, sleep_sec=1.0):
        """Turns on the vacuum of channel B."""
        modeval = 0x0100  # grip
        command = 0x00ff  # 100 % vacuum
        result = self.client.write_register(
            address=1, value=modeval+command, unit=65)

        print("\nTurn on the vacuum of channel B.")
        start = time.time()
        while True:
            print("Current channel B's vacuum: " +
                  str(self.get_channelB_vacuum()))
            if time.time() - start > sleep_sec:
                break

    def release_vacuum_channelA(self):
        """Releases the vacuum of channel A."""
        modeval = 0x0000  # release
        command = 0x0000  # 0 % vacuum
        print("\nRelease the vacuum of channel A.")
        result = self.client.write_register(
            address=0, value=modeval+command, unit=65)
        time.sleep(1.0)

    def release_vacuum_channelB(self):
        """Releases the vacuum of channel B."""
        modeval = 0x0000  # release
        command = 0x0000  # 0 % vacuum
        print("\nRelease the vacuum of channel B.")
        result = self.client.write_register(
            address=1, value=modeval+command, unit=65)
        time.sleep(1.0)
