# System architecture

Reviewed against `firmware/main.py` and the project log on 4 September 2026. This is a functional overview, not a wiring schematic or a claim of a new hardware test.

```mermaid
flowchart LR
    P["Pico 2 W / MicroPython"] <-->|"SoftI2C: GP6 SDA, GP7 SCL, 50 kHz"| I["INA219 / 0x40"]
    P -->|"Same SoftI2C bus"| O["SSD1306 OLED / 0x3C"]
    P -->|"GP0 charge / GP1 transistor control"| R["RC test network"]
    R -->|"GP26 / ADC0 capacitor voltage"| P
    P -->|"GP3 test drive"| D["Diode test network / 330 ohm resistor"]
    D -->|"GP27 source side / GP28 forward voltage"| P
    B["Active-low menu button / GP2"] --> P
    P --> S["Shared state / logging / software fault monitoring"]
    S --> W["Wi-Fi dashboard / CSV and JSON exports"]
```

## Power measurement path

The external load-current path is separate from the Pico's signal connections:

1. Bench supply positive → INA219 VIN+.
2. INA219 VIN− → test load.
3. Test-load return → supply negative directly.

Supply negative is the common reference. Pico and sensor low-current grounds reference the star-ground point; the high-current return is kept direct. The diagram above shows communication and control relationships, not electrical power flowing through the Pico or the Wi-Fi dashboard.

## Measurement boundaries

- ADC4 reads the MCU's internal die temperature, not ambient temperature.
- Guided Source Test captures V/I points manually. It does not drive an automatic load bank.
- A negative fitted source resistance is invalid; the new rejection guard still needs its documented on-device recheck.
- The diode PWM sweep is display-only. Settled DC measurements determine classification.
- Fault monitoring reports conditions in software; it does not disconnect power.
- The replacement OLED driver still requires the documented device recheck.

See the [README pin map](../README.md#pin-map) and [project log](PROJECT_LOG.md#verified-hardware-architecture) for the detailed implementation record.
