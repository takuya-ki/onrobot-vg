#!/usr/bin/env python3

import argparse

from onrobot import VGC10


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
    vgc10 = VGC10(toolchanger_ip, toolchanger_port)

    vgc10.vacuum_on(sleep_sec=2.0)
    vgc10.release_vacuum()
    vgc10.vacuum_on_channelA(sleep_sec=2.0)
    vgc10.release_vacuum_channelA()
    vgc10.vacuum_on_channelB(sleep_sec=2.0)
    vgc10.release_vacuum_channelB()

    vgc10.close_connection()


if __name__ == '__main__':
    args = get_options()
    toolchanger_ip = args.ip
    toolchanger_port = args.port
    run_demo()
