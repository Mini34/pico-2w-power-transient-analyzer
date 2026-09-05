# Pico 2 W EE Lab Tool

A Raspberry Pi Pico 2 W electrical-engineering instrument that combines calibrated DC power/energy measurement, RC transient analysis, diode characterization, internal MCU temperature telemetry, guided source characterization, software fault monitoring, experiment logging, and a Wi-Fi dashboard.

![Annotated prototype component overview](images/designs/01_annotated_prototype_overview.png)

[Original photograph](images/sanitized/01_image-1787893448668_sanitized.jpg) · [Annotation review](docs/IMAGE_REVIEW.md). Callouts identify visible components, not electrical terminals.

## Current status

The five-mode integrated prototype and dashboard were verified on hardware before this repository update. The new Source Test invalid-fit guard is covered by host-side synthetic tests and still needs a final on-device recheck; negative fitted source resistance is now rejected rather than accepted as a physical result. The repository uses the official generic MicroPython SSD1306 driver as a user-approved replacement for the unavailable Pico-side copy; this exact replacement has not been rechecked on the stored-away hardware.

## Implemented modes

1. **Power / Energy Monitor** - voltage, current, power, mAh, Wh, elapsed time, minimum voltage, peak current/power, and running averages.
2. **RC Analyzer** - automated charge/discharge, live OLED curves, 1/e time-constant extraction, capacitance calculation, and dashboard traces.
3. **Diode Analyzer** - settled single-point Vf/current measurement and classification, plus a display-only PWM I-V sweep.
4. **MCU Temperature** - RP2350 internal-die telemetry. This is not ambient temperature.
5. **Guided Source Test** - manual V/I point capture and linear fit for Voc, source resistance, and R^2.

The dashboard also provides software threshold/fault monitoring, persistent experiment history, and CSV/JSON export.

## Verified example results

| Measurement | Example |
|---|---:|
| Live power | 2.996 V, 0.469 A, 1.404 W |
| Power session | 9.70 mAh, 0.0292 Wh over 103 s |
| RC time constant | 1.076-1.079 s |
| RC capacitance | 1076-1079 uF |
| Silicon diode | Vf 0.662 V at 7.09 mA, 3.000 V source |
| 1N5819 Schottky | Vf 0.248 V at 8.20 mA, 2.954 V source |
| MCU temperature | approximately 41.25-46.02 C internal die telemetry |

## Measurement integrity

- Shared SoftI2C bus: `GP6 = SDA`, `GP7 = SCL`, `50 kHz`.
- INA219 address: `0x40`; OLED address: `0x3C`.
- Voltage calibration: `V_cal = 0.98896 * V_raw - 0.03531 V` (`R^2` approximately `0.999975`).
- Current was independently verified by measuring `30.1-30.2 mV` directly across the nominal `0.1 ohm` R100 shunt, corresponding to approximately `0.301-0.302 A` while the INA219 reported approximately `0.300 A`.
- Star grounding reduced ground-reference error from approximately `86 mV` to approximately `0.2 mV`.
- Prototype contact/wiring losses are measured as real circuit elements and are not calibrated away.

## Hardware

- Raspberry Pi Pico 2 W
- INA219 current/voltage monitor
- 128 x 64 SSD1306-compatible OLED
- Adjustable bench supply
- 10 ohm, 100 W aluminum power resistor
- 2N2222 RC switching transistor
- 1000 uF, 10 V capacitor
- 1 kOhm charge/discharge resistors
- 330 ohm diode test resistor
- Breadboard, jumper wiring, and detachable screw-terminal harness

## Pin map

| Pico resource | Function |
|---|---|
| GP0 | RC capacitor charge |
| GP1 | RC transistor control / discharge |
| GP2 | Menu/select button, active low |
| GP3 | Diode test source / sweep drive |
| GP6 | I2C SDA |
| GP7 | I2C SCL |
| GP26 / ADC0 | RC capacitor voltage |
| GP27 / ADC1 | Diode source-side voltage |
| GP28 / ADC2 | Diode forward voltage |
| ADC4 | Internal MCU temperature |

## Firmware layout

```text
firmware/
  main.py
  instrument_state.py
  wifi_manager.py
  web_server.py
  experiment_logger.py
  fault_monitor.py
  source_characterizer.py
  ssd1306.py
```

The display driver is MicroPython's generic `ssd1306` package, pinned and attributed in [`firmware/THIRD_PARTY_NOTICES.md`](firmware/THIRD_PARTY_NOTICES.md).

Do not commit Wi-Fi credentials. Keep local credential files ignored and provide only an example/template if the firmware requires one.

## Documentation

- [`docs/PROJECT_LOG.md`](docs/PROJECT_LOG.md) - complete engineering chronology and current status.
- [`docs/PROJECT_LOG.json`](docs/PROJECT_LOG.json) - machine-readable project record.
- [`docs/EE_Lab_Tool_Final_Project_Log.pdf`](docs/EE_Lab_Tool_Final_Project_Log.pdf) - final illustrated log.
- [`docs/EE_Lab_Tool_Photo_Appendix_All_26.pdf`](docs/EE_Lab_Tool_Photo_Appendix_All_26.pdf) - complete sanitized photo set.
- [`docs/SYSTEM_ARCHITECTURE.md`](docs/SYSTEM_ARCHITECTURE.md) - firmware-grounded functional overview and measurement boundaries.
- [`docs/IMAGE_REVIEW.md`](docs/IMAGE_REVIEW.md) - corrected annotations, original photo, and image accuracy review.
- [`docs/CODEX_REPOSITORY_UPDATE_INSTRUCTIONS.md`](docs/CODEX_REPOSITORY_UPDATE_INSTRUCTIONS.md) - exact repository-update procedure.

## Important limitations

- Source Test negative resistance is invalid and must be rejected/flagged.
- The PWM I-V sweep is visualization-only; settled DC data determines diode classification.
- MCU temperature is internal die temperature, not ambient.
- Fault monitoring is software monitoring only and does not disconnect the circuit.
- Automated electronic load stepping remains a future hardware stage.

## Safety and scope

Use a regulated source with a sensible current limit. Confirm polarity before energizing the load path. The project is an educational prototype and is not a certified protection instrument.
