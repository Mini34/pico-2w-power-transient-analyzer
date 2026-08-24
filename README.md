# Pico 2 W Power & Transient Analyzer

An embedded instrumentation project built around the **Raspberry Pi Pico 2 W**, **INA219**, and **SSD1306 OLED**. The project began as a DC power monitor and developed into a measurement-focused platform that combines calibrated steady-state power analysis with an automated RC transient analyzer.

![RC transient analyzer breadboard](images/11_rc_analyzer_breadboard.jpg)

> **Initial export status:** This first repository snapshot preserves the validated measurements, engineering chronology, and 13 source photographs from the project log. The complete device-tested MicroPython files were not included in the supplied export, so the repository does not present reconstructed firmware as tested code. See [`firmware/README.md`](firmware/README.md) for the planned source export.

## Why this project matters

The emphasis is not only on making the hardware work, but on **measurement integrity and engineering diagnosis**. The build documents how contradictory measurements were isolated, how parasitic wiring resistance was quantified, how calibration outliers were rejected, how the INA219 current channel was independently verified, and how a transistor-controlled RC experiment was compared against first-order circuit theory.

## Current capabilities

- Calibrated INA219 bus-voltage measurement with a five-point fit:
  - `V_cal = 0.98896 * V_raw - 0.03531`
- Current derived from the INA219 R100 (0.1 ohm) shunt and independently checked with a direct shunt-voltage measurement.
- Live OLED display of voltage, current, power, and diagnostic values.
- Eight-sample averaging for steadier steady-state readings.
- BJT-controlled RC charge/discharge experiment using a 2N2222.
- Pico ADC capture of capacitor voltage on GP26 / ADC0.
- Live OLED plotting of both charge and discharge curves.
- Automatic 1/e time-constant extraction and capacitance estimation.

## Selected quantitative results

| Result | Measurement |
|---|---:|
| Ground-reference error before star grounding | ~86 mV |
| Ground-reference error after grounding revision | ~0.2 mV |
| Positive-path drop, original single-jumper path | ~0.39 V at ~0.42 A |
| Positive-path drop, three parallel jumpers | ~0.076 V |
| Direct INA219 R100 shunt drop | 30.1-30.2 mV |
| INA219 current at same operating point | ~0.300 A |
| Independent calibrated voltage validation | ~3.78 V vs 3.78 V multimeter |
| RC nominal time constant | 1.00 s |
| RC measured charge time constant | ~1.03 s |
| RC measured discharge time constant | ~1.06 s |
| Estimated 1000 uF capacitor | ~1050 uF |

## Hardware

- Raspberry Pi Pico 2 W
- INA219 current/voltage monitor
- 128x64 SSD1306-compatible OLED
- Adjustable DC bench supply
- 100 W, nominal 10 ohm aluminum power resistors
- 2N2222 NPN BJT
- 1000 uF, 10 V electrolytic capacitor
- 1 kOhm charge/discharge resistors
- 4.7 kOhm transistor base resistor
- Breadboard and jumper wiring

## Pin assignments

| Pico pin | Function |
|---|---|
| GP6 | I2C SDA |
| GP7 | I2C SCL |
| GP0 | RC capacitor charge control through 1 kOhm |
| GP1 | 2N2222 base control through 4.7 kOhm |
| GP26 / ADC0 | Capacitor-voltage measurement |

For the specific 2N2222 used in this build, the pinout was **experimentally identified** with the flat face toward the observer as **Emitter - Base - Collector (left to right)**.

## Repository structure

```text
.
├── README.md
├── firmware/
│   └── README.md
├── docs/
│   ├── PROJECT_LOG.md
│   └── EE_Summer_Project_Log_GitHub_Export.docx
└── images/
    └── 13 diagnostic and build photographs extracted from the project log
```

## Firmware status

The project log documents the working calibration constants, INA219 register calculations, sample averaging, GPIO assignments, RC experiment sequence, and automatic time-constant analysis. The exact scripts currently running on the Pico/used in Thonny will be added in a later commit after they are exported from the device or development environment and checked against the hardware.

## Engineering highlights

### Sensor failure was separated from wiring failure

The first INA219 module could communicate over I2C and produced a plausible current reading, but its bus-voltage register reported ~0.18 V while a multimeter measured ~4.76 V directly between VIN- and INA219 GND. Repeating the test at ~3 V produced ~0.12 V, strongly indicating a defective/non-compliant voltage channel rather than a simple code mistake.

### Parasitic resistance was measured instead of calibrated away

At several hundred milliamps, Dupont wires, breadboard contacts, and temporary resistor-lug connections became measurable circuit elements. Direct voltage-drop measurements isolated losses in the positive lead, ground reference, and load connections. Star grounding reduced reference error dramatically, and parallel positive jumpers reduced the positive-path loss from ~0.39 V to ~0.076 V.

### Current was verified at the shunt itself

A direct multimeter measurement across the INA219 R100 shunt gave 30.1-30.2 mV, corresponding to ~0.301-0.302 A for a nominal 0.1 ohm shunt. The INA219 simultaneously reported ~0.300 A. This was more trustworthy than an inconsistent handheld-meter 10 A range reading.

### RC theory was validated experimentally

The completed RC analyzer charged a 1000 uF capacitor toward ~3.29 V and discharged it through a transistor-controlled 1 kOhm path. At ~1 s during charging the Pico measured ~2.055 V, close to the theoretical 63.2% point (~2.08 V). The measured time constants were approximately 1.03 s (charge) and 1.06 s (discharge).

## Next planned extensions

- Energy accumulation: mAh, Wh, average power, peak current, and minimum voltage.
- Repeatable transistor-controlled load-step testing.
- Additional capacitor/transient characterization.
- Late-stage USB source characterization using a USB-A screw-terminal breakout and multiple 5 V adapters.
- Replace temporary high-current Dupont/curl connections with mechanically robust low-resistance wiring.

## Documentation

See [`docs/PROJECT_LOG.md`](docs/PROJECT_LOG.md) for the engineering chronology and [`docs/EE_Summer_Project_Log_GitHub_Export.docx`](docs/EE_Summer_Project_Log_GitHub_Export.docx) for the full illustrated project log.
