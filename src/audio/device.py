from dataclasses import dataclass

import sounddevice as sd


@dataclass
class AudioDevice:
    id: int
    name: str
    input_channels: int
    default_samplerate: float


class AudioDeviceManager:
    @staticmethod
    def list_input_devices() -> list[AudioDevice]:
        devices = sd.query_devices()
        return [
            AudioDevice(
                id=i,
                name=d["name"],
                input_channels=d["max_input_channels"],
                default_samplerate=d["default_samplerate"],
            )
            for i, d in enumerate(devices)
            if d["max_input_channels"] > 0
        ]

    @staticmethod
    def default_input_name() -> str | None:
        default = sd.query_devices(kind="input")
        return default["name"] if default else None

    @staticmethod
    def device_id_by_name(name: str) -> int | None:
        for dev in AudioDeviceManager.list_input_devices():
            if dev.name == name:
                return dev.id
        return None
