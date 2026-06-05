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
#!/usr/bin/env python3

import argparse
import json
import socket
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer


COMMANDS = {
    "start":      (0x01, 0x00),
    "shutdown":   (0x02, 0x00),
    "pause":      (0x03, 0x00),
    "play":       (0x04, 0x00),
    "loop":       (0x05, 0x00),
    "previous":   (0x07, 0x00),
    "next":       (0x08, 0x00),
    "brighter":   (0x09, 0x00),
    "dimmer":     (0x0A, 0x00),
}


class MissyouFanBridge:
    def __init__(self, fans, timeout=1.0, dry_run=False):
        self.fans = fans
        self.timeout = timeout
        self.dry_run = dry_run

    @staticmethod
    def make_packet(command, value=0x00):
        return bytes([0x5B, command & 0xFF, value & 0xFF])

    def send_packet_to_fan(self, fan, packet):
        hex_text = packet.hex(" ").upper()

        if self.dry_run:
            print(f"[DRY RUN] Would send {hex_text} to {fan['name']} {fan['ip']}:{fan['port']}")
            return

        try:
            with socket.create_connection((fan["ip"], fan["port"]), timeout=self.timeout) as sock:
                sock.sendall(packet)

            print(f"Sent {hex_text} to {fan['name']} {fan['ip']}:{fan['port']}")

        except Exception as e:
            print(f"FAILED sending {hex_text} to {fan['name']} {fan['ip']}:{fan['port']} -> {e}")

    def send_packet_to_all(self, command, value=0x00):
        packet = self.make_packet(command, value)

        with ThreadPoolExecutor(max_workers=len(self.fans)) as executor:
            for fan in self.fans:
                executor.submit(self.send_packet_to_fan, fan, packet)

    def send_packet_to_named_fan(self, fan_name, command, value=0x00):
        packet = self.make_packet(command, value)
        matching_fans = [fan for fan in self.fans if fan["name"] == fan_name]

        if not matching_fans:
            print(f"No fan named '{fan_name}'")
            return

        self.send_packet_to_fan(matching_fans[0], packet)

    def send_named_to_all(self, command_name):
        command, value = COMMANDS[command_name]
        self.send_packet_to_all(command, value)

    def send_named_to_fan(self, fan_name, command_name):
        command, value = COMMANDS[command_name]
        self.send_packet_to_named_fan(fan_name, command, value)

    def play_file_all(self, file_index):
        file_index = int(file_index)

        if not 0 <= file_index <= 255:
            print("File index must be between 0 and 255")
            return

        self.send_packet_to_all(0x06, file_index)

    def play_file_fan(self, fan_name, file_index):
        file_index = int(file_index)

        if not 0 <= file_index <= 255:
            print("File index must be between 0 and 255")
            return

        self.send_packet_to_named_fan(fan_name, 0x06, file_index)


def load_config(config_path):
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        config = json.load(f)

    if "bridge" not in config:
        raise ValueError("Config missing required 'bridge' section")

    if "fans" not in config or not isinstance(config["fans"], list) or len(config["fans"]) < 1:
        raise ValueError("Config must include at least one fan in the 'fans' array")

    for fan in config["fans"]:
        for key in ("name", "ip", "port"):
            if key not in fan:
                raise ValueError(f"Fan config missing required key: {key}")

    return config


def build_dispatcher(bridge):
    dispatcher = Dispatcher()

    def group_command(command_name):
        def handler(address, *args):
            bridge.send_named_to_all(command_name)
        return handler

    def single_fan_command(fan_name, command_name):
        def handler(address, *args):
            bridge.send_named_to_fan(fan_name, command_name)
        return handler

    def group_file_handler(address, *args):
        if not args:
            print("Missing file index. Example: /fans/file 0")
            return
        bridge.play_file_all(args[0])

    def single_file_handler(fan_name):
        def handler(address, *args):
            if not args:
                print(f"Missing file index. Example: /fan/{fan_name}/file 0")
                return
            bridge.play_file_fan(fan_name, args[0])
        return handler

    dispatcher.map("/fans/start", group_command("start"))
    dispatcher.map("/fans/shutdown", group_command("shutdown"))
    dispatcher.map("/fans/pause", group_command("pause"))
    dispatcher.map("/fans/play", group_command("play"))
    dispatcher.map("/fans/loop", group_command("loop"))
    dispatcher.map("/fans/previous", group_command("previous"))
    dispatcher.map("/fans/next", group_command("next"))
    dispatcher.map("/fans/brightness/up", group_command("brighter"))
    dispatcher.map("/fans/brightness/down", group_command("dimmer"))
    dispatcher.map("/fans/file", group_file_handler)

    for fan in bridge.fans:
        name = fan["name"]

        dispatcher.map(f"/fan/{name}/start", single_fan_command(name, "start"))
        dispatcher.map(f"/fan/{name}/shutdown", single_fan_command(name, "shutdown"))
        dispatcher.map(f"/fan/{name}/pause", single_fan_command(name, "pause"))
        dispatcher.map(f"/fan/{name}/play", single_fan_command(name, "play"))
        dispatcher.map(f"/fan/{name}/loop", single_fan_command(name, "loop"))
        dispatcher.map(f"/fan/{name}/previous", single_fan_command(name, "previous"))
        dispatcher.map(f"/fan/{name}/next", single_fan_command(name, "next"))
        dispatcher.map(f"/fan/{name}/brightness/up", single_fan_command(name, "brighter"))
        dispatcher.map(f"/fan/{name}/brightness/down", single_fan_command(name, "dimmer"))
        dispatcher.map(f"/fan/{name}/file", single_file_handler(name))

    return dispatcher


def main():
    parser = argparse.ArgumentParser(description="OSC to TCP bridge for Missyou hologram fans")
    parser.add_argument(
        "--config",
        default="MissYouFanConfig.json",
        help="Path to JSON config file. Default: MissYouFanConfig.json",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config)

    bridge_config = config["bridge"]
    osc_ip = bridge_config.get("osc_ip", "127.0.0.1")
    osc_port = int(bridge_config.get("osc_port", 8000))
    timeout = float(bridge_config.get("timeout", 1.0))

    bridge = MissyouFanBridge(
        fans=config["fans"],
        timeout=timeout,
        dry_run=args.dry_run,
    )

    dispatcher = build_dispatcher(bridge)
    server = ThreadingOSCUDPServer((osc_ip, osc_port), dispatcher)

    print("Missyou fan OSC bridge running")
    print(f"Config file: {args.config}")
    print(f"Listening for OSC on {osc_ip}:{osc_port}")
    print(f"Socket timeout: {timeout}")
    print("Fans:")

    for fan in config["fans"]:
        print(f"  {fan['name']}: {fan['ip']}:{fan['port']}")

    print("")
    print("Group OSC commands:")
    print("  /fans/play")
    print("  /fans/pause")
    print("  /fans/file 0")
    print("  /fans/brightness/up")
    print("  /fans/brightness/down")
    print("")
    print("Individual OSC commands:")
    for fan in config["fans"]:
        name = fan["name"]
        print(f"  /fan/{name}/play")
        print(f"  /fan/{name}/file 0")

    print("")
    server.serve_forever()


if __name__ == "__main__":
    main()