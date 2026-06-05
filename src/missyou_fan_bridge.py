#!/usr/bin/env python3
"""
Gig Performer OSC -> Missyou hologram fan TCP bridge

Install:
  pip3 install python-osc

Run:
  python3 missyou_fan_bridge.py --fan-ip 10.10.10.1 --fan-port 50200

Gig Performer sends OSC to:
  127.0.0.1:8000
"""

import argparse
import socket
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer


COMMANDS = {
    "start":      (0x01, 0x00),  # Starting up
    "shutdown":   (0x02, 0x00),  # Shut down
    "pause":      (0x03, 0x00),  # Pause playback
    "play":       (0x04, 0x00),  # Keep playing
    "loop":       (0x05, 0x00),  # Loop current file
    "previous":   (0x07, 0x00),  # Previous file
    "next":       (0x08, 0x00),  # Next file
    "brighter":   (0x09, 0x00),  # Increase brightness
    "dimmer":     (0x0A, 0x00),  # Reduce brightness
}


class MissyouFan:
    def __init__(self, ip: str, port: int, timeout: float = 1.0):
        self.ip = ip
        self.port = port
        self.timeout = timeout

    def send_packet(self, command: int, value: int = 0x00):
        packet = bytes([0x5B, command & 0xFF, value & 0xFF])
        print(f"Sending to fan {self.ip}:{self.port} -> {packet.hex(' ').upper()}")

        with socket.create_connection((self.ip, self.port), timeout=self.timeout) as sock:
            sock.sendall(packet)

    def send_named(self, name: str):
        command, value = COMMANDS[name]
        self.send_packet(command, value)

    def play_file(self, index: int):
        if not 0 <= index <= 255:
            raise ValueError("File index must be between 0 and 255")

        # Manual says: play Nth file, first file is 0.
        self.send_packet(0x06, index)


def build_dispatcher(fan: MissyouFan):
    dispatcher = Dispatcher()

    def simple(name):
        def handler(address, *args):
            fan.send_named(name)
        return handler

    dispatcher.map("/fan/start", simple("start"))
    dispatcher.map("/fan/shutdown", simple("shutdown"))
    dispatcher.map("/fan/pause", simple("pause"))
    dispatcher.map("/fan/play", simple("play"))
    dispatcher.map("/fan/loop", simple("loop"))
    dispatcher.map("/fan/previous", simple("previous"))
    dispatcher.map("/fan/next", simple("next"))
    dispatcher.map("/fan/brightness/up", simple("brighter"))
    dispatcher.map("/fan/brightness/down", simple("dimmer"))

    def file_handler(address, *args):
        if not args:
            print("Missing file index. Example: /fan/file 0")
            return

        fan.play_file(int(args[0]))

    dispatcher.map("/fan/file", file_handler)

    return dispatcher


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fan-ip", default="10.10.10.1")
    parser.add_argument("--fan-port", type=int, default=50200)
    parser.add_argument("--osc-ip", default="127.0.0.1")
    parser.add_argument("--osc-port", type=int, default=8000)
    args = parser.parse_args()

    fan = MissyouFan(args.fan_ip, args.fan_port)
    dispatcher = build_dispatcher(fan)

    server = ThreadingOSCUDPServer((args.osc_ip, args.osc_port), dispatcher)

    print(f"Listening for OSC on {args.osc_ip}:{args.osc_port}")
    print(f"Sending fan TCP commands to {args.fan_ip}:{args.fan_port}")
    server.serve_forever()


if __name__ == "__main__":
    main()