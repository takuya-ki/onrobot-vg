#!/usr/bin/env python3

import logging
import time
from pymodbus.client.sync import ModbusTcpClient as ModbusClient

# --- モジュールレベル定数 ---
UNIT_ID = 65  # グリッパーのスレーブID（固定）

# レジスタアドレス
REG_CHANNEL_A = 0
REG_CHANNEL_B = 1
REG_CURRENT_LIMIT = 2
REG_VACUUM_A = 258
REG_VACUUM_B = 259

# 制御モード値（上位バイト）
MODE_RELEASE = 0x0000
MODE_GRIP = 0x0100
MODE_IDLE = 0x0200

# 真空目標値（下位バイト）
VACUUM_MAX = 0x00FF  # 100% vacuum

log = logging.getLogger(__name__)


class VG:

    def __init__(self, ip: str, port: int = 502):
        self.client = ModbusClient(ip, port=port, timeout=1)
        if not self.client.connect():
            raise ConnectionError(f"Failed to connect to {ip}:{port}")
        log.info("Connected to %s:%s", ip, port)

    def close_connection(self):
        """Closes the connection with the gripper."""
        self.client.close()
        log.info("Connection closed.")

    def _read_register(self, address: int) -> int:
        """Reads a single holding register and raises IOError on failure."""
        result = self.client.read_holding_registers(
            address=address, count=1, unit=UNIT_ID)
        if not hasattr(result, 'registers'):
            raise IOError(f"Modbus read failed at address {address}: {result}")
        return result.registers[0]

    def get_vacuum_limit(self) -> int:
        """Reads the current limit in mA (default 500 mA, max 1000 mA)."""
        return self._read_register(REG_CURRENT_LIMIT)

    def get_channelA_vacuum(self) -> int:
        """Reads the actual vacuum on Channel A (1/1000 of relative vacuum)."""
        return self._read_register(REG_VACUUM_A)

    def get_channelB_vacuum(self) -> int:
        """Reads the actual vacuum on Channel B (1/1000 of relative vacuum)."""
        return self._read_register(REG_VACUUM_B)

    # --- 内部共通メソッド ---

    def _set_channel_control(self, address: int, modename: str, command: int):
        """Sets the control mode and target vacuum for a channel.

        Args:
            address: Register address (REG_CHANNEL_A or REG_CHANNEL_B).
            modename: "Release", "Grip", or "Idle".
            command: Target vacuum in % (only used in Grip mode, max 80).
        """
        mode_map = {"Release": MODE_RELEASE, "Grip": MODE_GRIP, "Idle": MODE_IDLE}
        if modename not in mode_map:
            raise ValueError(
                f"Invalid modename '{modename}'. Choose from {list(mode_map)}")
        self.client.write_register(
            address=address, value=mode_map[modename] + command, unit=UNIT_ID)

    def _vacuum_on_channel(self, address: int, read_fn, label: str, sleep_sec: float):
        """Writes grip command and polls vacuum every 0.1 s until sleep_sec elapses."""
        self.client.write_register(
            address=address, value=MODE_GRIP + VACUUM_MAX, unit=UNIT_ID)
        log.info("Turn on the vacuum of %s.", label)
        start = time.time()
        while time.time() - start < sleep_sec:
            log.info("Current %s vacuum: %d", label, read_fn())
            time.sleep(0.1)

    def _release_vacuum_channel(self, address: int, label: str):
        """Writes release command and waits 1 second."""
        self.client.write_register(
            address=address, value=MODE_RELEASE, unit=UNIT_ID)
        log.info("Release the vacuum of %s.", label)
        time.sleep(1.0)

    # --- 公開API ---

    def set_channelA_control(self, modename: str, command: int):
        """Controls channel A.

        modename: 'Release', 'Grip', or 'Idle'.
        command: Target vacuum in % (used only in Grip mode, max 80).
        """
        self._set_channel_control(REG_CHANNEL_A, modename, command)

    def set_channelB_control(self, modename: str, command: int):
        """Controls channel B.

        modename: 'Release', 'Grip', or 'Idle'.
        command: Target vacuum in % (used only in Grip mode, max 80).
        """
        self._set_channel_control(REG_CHANNEL_B, modename, command)

    def vacuum_on(self, sleep_sec: float = 1.0):
        """Turns on all vacuums (channel A and B simultaneously)."""
        commands = [MODE_GRIP + VACUUM_MAX, MODE_GRIP + VACUUM_MAX]
        self.client.write_registers(address=REG_CHANNEL_A, values=commands, unit=UNIT_ID)
        log.info("Turn on all vacuums.")
        start = time.time()
        while time.time() - start < sleep_sec:
            log.info(
                "Current vacuums, channel A: %d, channel B: %d",
                self.get_channelA_vacuum(), self.get_channelB_vacuum())
            time.sleep(0.1)

    def release_vacuum(self):
        """Releases all vacuums (channel A and B simultaneously)."""
        commands = [MODE_RELEASE, MODE_RELEASE]
        self.client.write_registers(address=REG_CHANNEL_A, values=commands, unit=UNIT_ID)
        log.info("Release all vacuums.")
        time.sleep(1.0)

    def vacuum_on_channelA(self, sleep_sec: float = 1.0):
        """Turns on the vacuum of channel A."""
        self._vacuum_on_channel(
            REG_CHANNEL_A, self.get_channelA_vacuum, "channel A", sleep_sec)

    def vacuum_on_channelB(self, sleep_sec: float = 1.0):
        """Turns on the vacuum of channel B."""
        self._vacuum_on_channel(
            REG_CHANNEL_B, self.get_channelB_vacuum, "channel B", sleep_sec)

    def release_vacuum_channelA(self):
        """Releases the vacuum of channel A."""
        self._release_vacuum_channel(REG_CHANNEL_A, "channel A")

    def release_vacuum_channelB(self):
        """Releases the vacuum of channel B."""
        self._release_vacuum_channel(REG_CHANNEL_B, "channel B")
