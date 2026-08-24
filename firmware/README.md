# Firmware export status

The full device-tested MicroPython source files were not included in the initial project export. This folder is intentionally documentation-only until the exact scripts can be copied from the Raspberry Pi Pico 2 W or the Thonny development environment and checked against the current hardware.

Planned files:

- `power_monitor.py` — calibrated INA219 voltage/current/power acquisition, eight-sample averaging, OLED output, and raw serial diagnostics.
- `rc_analyzer.py` — GP0 charge control, GP1/2N2222 discharge control, GP26/ADC0 acquisition, OLED plots, time-constant extraction, and capacitance estimation.

Documented configuration to preserve during export:

```python
V_SLOPE = 0.98896
V_OFFSET = -0.03531
SHUNT_OHMS = 0.1
SAMPLES = 8
```

The documented shared I2C bus uses GP6 for SDA and GP7 for SCL. The RC analyzer uses GP0 for charge control, GP1 for transistor base control, and GP26/ADC0 for capacitor-voltage measurement.

Future firmware commits should state whether they were syntax-checked only or validated on the physical hardware.
