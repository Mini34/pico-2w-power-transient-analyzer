# Firmware deployment

Copy the MicroPython modules in this directory to the root of the Raspberry Pi Pico 2 W filesystem. Keep the filenames unchanged so `main.py` can resolve its service imports.

Required project modules:

- `main.py`
- `instrument_state.py`
- `wifi_manager.py`
- `web_server.py`
- `experiment_logger.py`
- `fault_monitor.py`
- `source_characterizer.py`
- `ssd1306.py` (official generic MicroPython driver; see `THIRD_PARTY_NOTICES.md` for the pinned source and license)

For Wi-Fi, copy `secrets.example.py` to `secrets.py` on the device and fill in the local credentials there. Never commit `secrets.py`.

The integrated source files are syntax-checked in this repository. Hardware verification applies to the supplied working firmware snapshot. At the user's direction, `ssd1306.py` is a generic upstream replacement rather than an export of the file that was on the Pico, so this exact driver copy remains hardware-unverified. The additional Source Test validation is covered by host-side synthetic tests and should also be rechecked on the Pico before treating it as device-verified.

The software fault monitor records threshold events but is not an electrical protection device and does not disconnect the circuit.
