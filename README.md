# FanController.OSC.MissYou
# MissYou Fan Bridge

OSC to TCP/IP bridge for controlling one or more Missyou 3D Hologram Fan displays from Gig Performer.

This project listens for OSC commands and translates them into the proprietary TCP control protocol documented in the Missyou Third-Party Control appendix.

The bridge allows a Gig Performer rig to trigger hologram animations, switch files, adjust brightness, and synchronize multiple fans from a single control interface.

---

## Features

* Control Missyou hologram fans from Gig Performer using OSC
* Supports multiple fans simultaneously
* Group commands for synchronized playback
* Individual fan commands for testing and troubleshooting
* JSON configuration file
* Cross-platform (macOS, Windows, Linux)
* No additional hardware required
* Dry-run mode for testing without hardware

---

## Supported Missyou Commands

| Function            | OSC Command             |
| ------------------- | ----------------------- |
| Start Fan           | `/fans/start`           |
| Shutdown Fan        | `/fans/shutdown`        |
| Play                | `/fans/play`            |
| Pause               | `/fans/pause`           |
| Loop Current File   | `/fans/loop`            |
| Previous File       | `/fans/previous`        |
| Next File           | `/fans/next`            |
| Increase Brightness | `/fans/brightness/up`   |
| Decrease Brightness | `/fans/brightness/down` |
| Play File N         | `/fans/file <index>`    |

Example:

```text
/fans/file 3
```

Plays file #3 on all configured fans.

---

## Individual Fan Control

Each configured fan can also be addressed independently.

Examples:

```text
/fan/left/play
/fan/right/play

/fan/left/file 0
/fan/right/file 5
```

This is useful for testing or recovery if one fan becomes out of sync.

---

## Requirements

### Python

Python 3.9 or later is recommended.

### Required Package

```bash
pip install python-osc
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/MissYouFanBridge.git

cd MissYouFanBridge
```

Install dependencies:

```bash
pip install python-osc
```

Create or edit:

```text
MissYouFanConfig.json
```

Start the bridge:

```bash
python missyou_fan_bridge.py
```

Test without hardware:

```bash
python missyou_fan_bridge.py --dry-run
```

---

## Configuration

The bridge loads all network settings from:

```text
MissYouFanConfig.json
```

Example:

```json
{
  "bridge": {
    "osc_ip": "127.0.0.1",
    "osc_port": 8000,
    "timeout": 1.0
  },
  "fans": [
    {
      "name": "left",
      "ip": "192.168.1.101",
      "port": 50200
    },
    {
      "name": "right",
      "ip": "192.168.1.102",
      "port": 50200
    }
  ]
}
```

### Configuration Fields

#### bridge

| Setting  | Description                       |
| -------- | --------------------------------- |
| osc_ip   | Local interface to listen for OSC |
| osc_port | UDP port for OSC messages         |
| timeout  | TCP socket timeout in seconds     |

#### fans

| Setting | Description                     |
| ------- | ------------------------------- |
| name    | Friendly name used in OSC paths |
| ip      | Fan IP address                  |
| port    | Fan TCP control port            |

---

## Gig Performer Configuration

Configure Gig Performer to send OSC messages to:

```text
127.0.0.1
Port 8000
```

Example OSC commands:

```text
/fans/play
/fans/pause
/fans/file 0
/fans/file 1
/fans/file 2
/fans/brightness/up
/fans/brightness/down
```

These commands can be attached to:

* Widget actions
* GPScript
* Song changes
* Rackspace changes
* MIDI-triggered OSC actions

---

## Synchronizing Multiple Fans

For best synchronization:

1. Use static IP addresses for all fans.
2. Load identical content on all fans.
3. Keep file ordering identical across devices.
4. Prefer direct file selection (`/fans/file N`) rather than repeated next/previous commands.
5. Place all fans on the same network segment.

The bridge sends commands to all configured fans in parallel to minimize timing differences.

---

## Protocol Information

Based on the Missyou Third-Party Control appendix.

Default TCP port:

```text
50200
```

Command packet format:

```text
0x5B <COMMAND> <VALUE>
```

Examples:

```text
5B 04 00    Play
5B 03 00    Pause
5B 06 05    Play file #5
```

Only one command should be sent per TCP packet.

---

## Troubleshooting

### Fan Does Not Respond

Verify:

* Fan is powered on
* Fan is connected to the network
* Correct IP address is configured
* Port 50200 is reachable

Test connectivity:

```bash
ping <fan-ip>
```

---

### OSC Messages Not Received

Verify:

* Gig Performer is sending to the correct IP and port
* Firewall allows UDP traffic on the OSC port
* Bridge is running

---

### One Fan Gets Out Of Sync

Use:

```text
/fan/left/file N
/fan/right/file N
```

to manually resynchronize.

---

## Future Enhancements

Potential improvements:

* Automatic fan discovery
* TCP connection pooling
* OSC feedback/status messages
* Web-based administration UI
* Synchronization health monitoring
* Playback status reporting
* Preset and scene management

---

## Disclaimer

This project is not affiliated with or endorsed by Missyou.

Protocol implementation is based on the publicly available Third-Party Control appendix and community testing.

