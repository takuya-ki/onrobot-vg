#!/usr/bin/env python3

import argparse

from onrobot import VG


def get_options():
    """Returns user-specific options."""
    parser = argparse.ArgumentParser(description='Set options.')
    parser.add_argument(
        '--ip', dest='ip', type=str, default=None,
        help='set ip address')
    parser.add_argument(
        '--port', dest='port', type=str, default="502",
        help='set port number')
    parser.add_argument(
        '--device', dest="device", type=str,  default=None,
        help='set device path'
    )
    return parser.parse_args()


def run_demo():
    """Runs pump on/off demonstration once."""
    vg = VG(ip=toolchanger_ip, port=toolchanger_port, device=args.device)

    vg.vacuum_on(sleep_sec=5.0)
    vg.release_vacuum()
    vg.vacuum_on_channelA(sleep_sec=5.0)
    vg.release_vacuum_channelA()
    vg.vacuum_on_channelB(sleep_sec=5.0)
    vg.release_vacuum_channelB()

    vg.close_connection()


if __name__ == '__main__':
    args = get_options()
    toolchanger_ip = args.ip
    toolchanger_port = args.port
    run_demo()
