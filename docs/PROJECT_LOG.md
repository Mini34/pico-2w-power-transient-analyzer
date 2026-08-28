# EE Summer Project Log - Pico 2 W EE Lab Tool
**Final integrated documentation update: 27 August 2026**
**Repository target:** `Mini34/pico-2w-power-transient-analyzer`
**Status:** Working integrated prototype; firmware and dashboard verified; source-test fit validation remains open.

## Executive summary
The project began as a Raspberry Pi Pico 2 W and INA219 DC power monitor and developed into a self-contained, network-connected electrical-engineering lab instrument. The final working prototype combines calibrated power and energy measurement, RC transient analysis, diode characterization, MCU internal-temperature telemetry, guided source characterization, software threshold/fault monitoring, persistent experiment logging, and a Wi-Fi dashboard with CSV/JSON export.
The engineering record preserves failures as well as final results: defective INA219 screening, I2C recovery, grounding redesign, contact-resistance diagnosis, calibration outlier rejection, transistor pinout verification, RC node-isolation faults, a diode PWM-method correction, and an invalid negative source-resistance fit. These events are retained because they demonstrate the measurement reasoning that made the final system trustworthy.

![Annotated final prototype](../images/designs/01_annotated_prototype_overview.png)
*Figure 1. Sanitized and annotated final prototype overview. The photograph is evidence of the integrated physical build; exact pin assignments and electrical limits are defined below.*

![Verified system architecture](../images/designs/02_verified_system_architecture.png)
*Figure 2. Verified system architecture and pin map. The firmware uses SoftI2C at 50 kHz on GP6/GP7.*

## Current capability status
| Capability | Status | Notes |
|---|---|---|
| Power / Energy Monitor | Complete | Live V/I/P, mAh, Wh, min/peak/average statistics, OLED pages, dashboard, session logging. |
| RC Analyzer | Complete | Automated charge/discharge, live OLED curves, tau and capacitance, dashboard traces, logging. |
| Diode Analyzer | Complete with method boundary | Steady-DC single test is quantitative; PWM I-V sweep is display-only. |
| Wi-Fi dashboard | Complete | Live cards, charts, mode/state, history, exports, system status. |
| MCU temperature telemetry | Complete | Internal die telemetry; not ambient; intentionally idle in STARTUP/MENU. |
| Experiment logging/export | Complete | Power, RC, diode, source, and fault records; CSV/JSON downloads. |
| Fault/threshold monitoring | Complete as software monitoring | No hardware cutoff/protection stage. |
| Guided Source Test | Implemented; validation open | Manual point capture and regression work; negative-Rs results are invalid and flagged. |
| Automated load bank | Not implemented | Requires future MOSFET/switched-load hardware. |

## Verified hardware architecture
### Core components
- Raspberry Pi Pico 2 W running MicroPython.
- INA219 current/voltage monitor at I2C address `0x40`, with an onboard nominal `R100 = 0.1 ohm` shunt.
- 128 x 64 SSD1306-compatible OLED at I2C address `0x3C`.
- Shared `SoftI2C` bus: `GP6 = SDA`, `GP7 = SCL`, `50 kHz`.
- 10 ohm, 100 W aluminum power resistor as the principal high-current load.
- 1000 uF, 10 V electrolytic capacitor, 1 kOhm charge/discharge paths, and 2N2222 transistor for RC analysis.
- 330 ohm diode-test resistor with GP27/GP28 ADC measurements.
- Active-low menu/select button on GP2.
- Bench supply negative used as the star-ground reference.

### Pin assignments
| Pico resource | Function |
|---|---|
| `GP0` | RC capacitor charge |
| `GP1` | RC transistor control / discharge path |
| `GP2` | menu/select button, active low |
| `GP3` | diode test source / PWM sweep drive |
| `GP6` | I2C SDA |
| `GP7` | I2C SCL |
| `GP26_ADC0` | RC capacitor voltage |
| `GP27_ADC1` | diode source-side voltage |
| `GP28_ADC2` | diode forward voltage |
| `ADC4` | RP2350 internal temperature sensor |

### Power-monitor calibration and measurement integrity
- Final bus-voltage calibration: `V_cal = 0.98896 * V_raw - 0.03531 V`.
- Fit quality: `R^2 = 0.999975` with accepted residuals on the order of approximately +/-3 mV.
- Direct shunt validation: 30.1-30.2 mV across the nominal 0.1 ohm R100 shunt implies approximately 0.301-0.302 A, while the INA219 reported approximately 0.300 A. No current-scale correction was added.
- Star grounding reduced the measured INA219-ground-to-supply-negative error from approximately 86 mV to approximately 0.2 mV.
- Three parallel temporary positive jumpers reduced positive-path drop from approximately 0.39 V to approximately 0.076 V. These are real wiring/contact losses, not calibration error.

## Engineering chronology
### 1. Hardware bring-up and soldering
Soldered Pico and INA219 headers, recovered from oxidized-tip and breadboard/contact issues, and established stable power and ground rails.

**Evidence**
- Pico 3V3 measured approximately 3.22-3.26 V
- Shared I2C bus ultimately detected both devices

**Decision / next step:** Continue with GP6/GP7 shared I2C and preserve one-step-at-a-time physical verification.

### 2. I2C and module diagnosis
Separated communication faults from measurement faults. A scan returned [60, 64], proving OLED 0x3C and INA219 0x40 communication.

**Evidence**
- First INA219 produced implausible bus voltage despite valid current
- Third tested module produced realistic bus-voltage data

**Decision / next step:** Reject defective/noncompliant modules rather than calibrating around hardware failure.

### 3. Power-monitor calibration and wiring integrity
Moved from a 500 ohm load to a 10 ohm, 100 W load, quantified real connection losses, implemented star grounding, and fitted the voltage calibration.

**Evidence**
- Ground-reference error reduced from approximately 86 mV to approximately 0.2 mV
- Positive-path drop reduced from approximately 0.39 V to approximately 0.076 V using three parallel temporary jumpers
- Voltage fit R^2 approximately 0.999975

**Decision / next step:** Treat parasitic resistance as a physical circuit element; do not calibrate it away.

### 4. Current-channel verification
Rejected an inconsistent multimeter 10 A range result and measured directly across the INA219 R100 shunt.

**Evidence**
- 30.1-30.2 mV across 0.1 ohm implies approximately 0.301-0.302 A
- INA219 simultaneously reported approximately 0.300 A

**Decision / next step:** No software current scale factor is justified.

### 5. Power and energy analyzer
Extended the Power Monitor with charge and energy integration, minimum/peak statistics, running averages, elapsed time, OLED pages, dashboard state, and end-of-session logging.

**Evidence**
- Final dashboard example: 2.996 V, 0.469 A, 1.404 W
- 9.70 mAh and 0.0292 Wh over a 103 s example session

**Decision / next step:** Power/Energy Monitor accepted as a completed subsystem.

### 6. RC analyzer
Built a 2N2222-controlled RC charge/discharge network using a 1000 uF capacitor and 1 kOhm paths. Added live OLED curves, 1/e crossing interpolation, capacitance calculation, dashboard traces, and result logging.

**Evidence**
- Measured tau approximately 1.076-1.079 s
- Calculated capacitance approximately 1076-1079 uF
- Charge curve agreed with the 63.2% first-order checkpoint

**Decision / next step:** RC Analyzer accepted as a completed subsystem.

### 7. Diode analyzer
Added settled single-point diode measurement and a PWM-driven I-V visualization. Corrected an early method error by restricting classification to the settled DC result.

**Evidence**
- 1N4007 silicon example: Vf approximately 0.662 V at 7.09 mA from a 3.000 V source
- 1N5819 Schottky example: Vf approximately 0.248 V at 8.20 mA from a 2.954 V source
- I-V sweep displays 15 points but is not used for quantitative classification

**Decision / next step:** Single-test classification is quantitative; PWM sweep is visualization-only until an analog source is validated.

### 8. Unified instrument UI
Combined Power, RC, Diode, MCU Temperature, and Source Test modes into one startup/menu workflow controlled by one active-low button.

**Evidence**
- Short press navigates/pages; long press selects/returns
- OLED screens and photographed menu/result pages verified

**Decision / next step:** Routine operation no longer depends on separate Thonny scripts.

### 9. Wi-Fi dashboard
Integrated Wi-Fi connection management, shared instrument state, HTTP serving, live status cards, power history, RC traces, diode results, source-test state, MCU telemetry, and logs.

**Evidence**
- Dashboard connected and served on the local network
- User verified all live panels and charts

**Decision / next step:** Networking/dashboard support treated as a completed subsystem.

### 10. MCU temperature telemetry
Read ADC4 with 16-sample averaging every five seconds when the instrument is in an active mode. Corrected TEMP_VREF to 3.24 V and exposed the reading to OLED/dashboard state.

**Evidence**
- Stable readings approximately 45.53-45.68 C
- ADC approximately 0.6739-0.6741 V, raw approximately 13630-13635

**Decision / next step:** Label as MCU/internal-die temperature, not ambient. Preserve the intentional pause in STARTUP and MENU.

### 11. Experiment logging and export
Added persistent completed-test summaries for power sessions, RC tests, diode single tests, diode I-V sweeps, source tests, and faults. Added dashboard history plus CSV/JSON downloads.

**Evidence**
- Experiment table displays type, status, uptime, and summaries
- Separate experiment/fault CSV and JSON export controls verified

**Decision / next step:** Logging/export accepted as a completed software subsystem.

### 12. Guided Source Test
Added manual capture of multiple INA219 V/I operating points and a reusable linear-fit backend for Voc, source resistance, and R^2.

**Evidence**
- Point acceptance and duplicate rejection photographed
- One three-point test returned Voc -0.003 V, Rs -6.395 ohm, R^2 1.000

**Decision / next step:** Retain mode as guided/manual. Flag negative resistance as invalid; add stronger capture workflow and fit validation before treating results as physical.

### 13. Fault and threshold monitoring
Added configurable software monitoring for undervoltage, overcurrent, excessive power, MCU temperature, and INA219 disconnect/restoration, with state transitions and event logging.

**Evidence**
- System status dashboard verified
- UNDERVOLTAGE_ACTIVE example appears in history

**Decision / next step:** State clearly that this is monitoring only; no hardware cutoff is presently installed.

### 14. Final photographic/documentation capture
Captured the full hardware setup, close-ups of the controller, RC section, switches, load resistor, harness, OLED workflows, dashboard charts, telemetry, and logs. Sanitized screen photos to remove laptop branding, browser chrome, bookmarks, tabs, and local IP information.

**Evidence**
- 26 sanitized photographs in the final appendix
- Annotated overview, exact architecture diagram, and conceptual 3D visual prepared

**Decision / next step:** Use photos as engineering evidence with captions explaining what each image proves.


## Final measured examples
### Power / Energy Monitor
- Live voltage/current/power: **2.996 V, 0.469 A, 1.404 W**.
- Session example: **9.70 mAh**, **0.0292 Wh**, **103 s**.
- Minimum/maximum/peak/average values: 2.992 V minimum, 3.301 V maximum, 0.469 A peak current, 1.405 W peak power, 3.064 V average, 0.361 A average, 1.086 W average.

### RC Analyzer
- Final photographed runs produced tau approximately **1.076-1.079 s** and capacitance approximately **1076-1079 uF** for the nominal 1000 uF capacitor.

### Diode Analyzer
- Silicon example: **SILICON**, Vf approximately **0.662 V** at **7.09 mA**, source approximately **3.000 V**.
- Schottky comparison: **1N5819**, Vf approximately **0.248 V** at **8.20 mA**, source approximately **2.954 V**.
- The I-V sweep is retained for visualization only because PWM duty cycle is not equivalent to a settled analog source.

### MCU temperature telemetry
- With `TEMP_VREF = 3.24 V`, a stable active-mode test produced approximately **45.53-45.68 C**, ADC approximately **0.6739-0.6741 V**, and raw counts approximately **13630-13635**.
- The dashboard history captured approximately **41.25-46.02 C** over the observed session. This is internal die temperature, not room temperature.

### Guided Source Test
- Photographed three-point example: Voc approximately **-0.003 V**, source resistance approximately **-6.395 ohm**, `R^2 = 1.000`. The fit is mathematically linear but physically invalid for the assumed source model and must be rejected/flagged.

## Firmware architecture
The current `main.py` imports modular services and fails gracefully if optional modules are absent. The repository update should contain the exact working copies of the following files rather than reconstructed substitutes:
- `firmware/main.py`
- `firmware/instrument_state.py`
- `firmware/wifi_manager.py`
- `firmware/web_server.py`
- `firmware/experiment_logger.py`
- `firmware/fault_monitor.py`
- `firmware/source_characterizer.py`
- `firmware/ssd1306.py`

The main firmware preserves timing-sensitive acquisition by calling `service_background(allow_web=False)` during RC and diode sweep sampling. Temperature sampling is also deferred in `STARTUP` and `MENU` because the user intentionally does not want constant idle measurement.

## Known limitations and explicit boundaries
- Source Test can return a mathematically perfect but physically invalid negative source resistance when captured points or current direction do not represent the assumed V = Voc - I Rs model. Negative Rs must be rejected or clearly marked invalid.
- The diode PWM I-V sweep averages a pulsed waveform and is display-only. Steady-DC single-test data remains the classification source.
- MCU temperature is the RP2350 internal die temperature, not ambient temperature.
- Fault monitoring is software monitoring and logging only; it does not provide a hardware safety cutoff.
- High-current prototype wiring and clip/contact resistance remain measurable. Final construction should use robust low-resistance terminals/conductors.
- Automated electronic load stepping is not yet implemented. Current Source Test is guided/manual until MOSFET/load-bank hardware is added.
- Temperature sampling is intentionally deferred in STARTUP and MENU to avoid continuous background measurements when idle.

## Photographic evidence
All 26 photographs supplied for this final update were sanitized and indexed. Laptop branding, browser tabs/bookmarks, local IP information, and other screen chrome were removed by cropping where required. The complete high-resolution set is in `docs/EE_Lab_Tool_Photo_Appendix_All_26.pdf`; the image files are in `images/sanitized/`.

![Figure 1](../images/sanitized/01_image-1787893448668_sanitized.jpg)
*Figure 1. Overall prototype overview showing the complete Pico 2 W EE Lab Tool on the work mat, including the breadboard, external switch modules, OLED, and surrounding test wiring.*

![Figure 3](../images/sanitized/03_image-1787893461592_sanitized.jpg)
*Figure 3. RC analyzer section close-up showing the 1000 uF electrolytic capacitor, resistors, transistor, and ADC/control wiring.*

![Figure 4](../images/sanitized/04_image-1787893464888_sanitized.jpg)
*Figure 4. OLED RC Analyzer result screen documenting a successful measured time constant and capacitance result.*

![Figure 7](../images/sanitized/07_image-1787893486860_sanitized.jpg)
*Figure 7. Manual ON/OFF switch modules and alligator-clip wiring used as physical circuit selectors/bypass elements during testing.*

![Figure 8](../images/sanitized/08_image-1787893496016_sanitized.jpg)
*Figure 8. 10 ohm, 100 W aluminum power resistor used as the principal high-current load.*

![Figure 9](../images/sanitized/09_image-1787893499406_sanitized.jpg)
*Figure 9. Screw-terminal power-harness breakout and multi-conductor wiring used for detachable source/load connections.*

![Figure 10](../images/sanitized/10_image-1787893506140_sanitized.jpg)
*Figure 10. Sanitized dashboard overview showing MCU temperature, Wi-Fi status, threshold monitoring, live power, Power Monitor statistics, and RC Analyzer results.*

![Figure 11](../images/sanitized/11_1000017942_sanitized.jpg)
*Figure 11. OLED main-menu page showing the unified EE LAB TOOL interface and analyzer selection.*

![Figure 12](../images/sanitized/12_1000017943_sanitized.jpg)
*Figure 12. OLED Source Test result screen. The photographed negative source-resistance result is retained as a validation issue, not accepted as a physical source model.*

![Figure 13](../images/sanitized/13_1000017944_sanitized.jpg)
*Figure 13. OLED Point Capture confirmation with the measured voltage and current for an accepted source-test point.*

![Figure 14](../images/sanitized/14_1000017945_sanitized.jpg)
*Figure 14. OLED duplicate-point rejection message demonstrating source-test data-quality screening.*

![Figure 15](../images/sanitized/15_1000017947_sanitized.jpg)
*Figure 15. OLED I-V sweep visualization from the Diode Analyzer.*

![Figure 16](../images/sanitized/16_1000017946_sanitized.jpg)
*Figure 16. OLED Source Test collection screen showing the current point count and short/long press controls.*

![Figure 21](../images/sanitized/21_image-1787893815724_sanitized.jpg)
*Figure 21. Sanitized dashboard view showing live voltage/current/power, Power Monitor session statistics, RC Analyzer results, and the silicon-diode result.*

![Figure 22](../images/sanitized/22_image-1787893821029_sanitized.jpg)
*Figure 22. Sanitized dashboard close-up showing the silicon-diode result and the three-point Source Test fit that produced a negative resistance and therefore requires validation.*

![Figure 23](../images/sanitized/23_image-1787893828096_sanitized.jpg)
*Figure 23. Sanitized dashboard charts showing recent voltage/current/power history and RC charge/discharge traces.*

![Figure 24](../images/sanitized/24_image-1787893835341_sanitized.jpg)
*Figure 24. Sanitized dashboard view showing RC traces, MCU internal-die temperature history, and experiment/fault export controls.*

![Figure 25](../images/sanitized/25_image-1787893841248_sanitized.jpg)
*Figure 25. Sanitized dashboard view showing MCU temperature history and the experiment-history table with CSV/JSON export controls.*

![Figure 26](../images/sanitized/26_image-1787893852127_sanitized.jpg)
*Figure 26. Sanitized close-up of the experiment-history table and update timestamp.*

### Complete photo index
| Figure | Sanitized file | Diagnostic/documentation significance | Privacy action |
|---:|---|---|---|
| 1 | [`01_image-1787893448668_sanitized.jpg`](../images/sanitized/01_image-1787893448668_sanitized.jpg) | Overall prototype overview showing the complete Pico 2 W EE Lab Tool on the work mat, including the breadboard, external switch modules, OLED, and surrounding test wiring. | none required |
| 2 | [`02_image-1787893452363_sanitized.jpg`](../images/sanitized/02_image-1787893452363_sanitized.jpg) | Close-up of the low-current breadboard test area, preserving component placement and jumper routing around the transistor/resistor network. | none required |
| 3 | [`03_image-1787893461592_sanitized.jpg`](../images/sanitized/03_image-1787893461592_sanitized.jpg) | RC analyzer section close-up showing the 1000 uF electrolytic capacitor, resistors, transistor, and ADC/control wiring. | none required |
| 4 | [`04_image-1787893464888_sanitized.jpg`](../images/sanitized/04_image-1787893464888_sanitized.jpg) | OLED RC Analyzer result screen documenting a successful measured time constant and capacitance result. | none required |
| 5 | [`05_image-1787893467914_sanitized.jpg`](../images/sanitized/05_image-1787893467914_sanitized.jpg) | Top-side close-up of the Pico 2 W, INA219/OLED interconnections, and dense shared-bus/control wiring. | none required |
| 6 | [`06_image-1787893481899_sanitized.jpg`](../images/sanitized/06_image-1787893481899_sanitized.jpg) | Raspberry Pi Pico 2 W controller close-up documenting the header connections used by the integrated instrument. | none required |
| 7 | [`07_image-1787893486860_sanitized.jpg`](../images/sanitized/07_image-1787893486860_sanitized.jpg) | Manual ON/OFF switch modules and alligator-clip wiring used as physical circuit selectors/bypass elements during testing. | none required |
| 8 | [`08_image-1787893496016_sanitized.jpg`](../images/sanitized/08_image-1787893496016_sanitized.jpg) | 10 ohm, 100 W aluminum power resistor used as the principal high-current load. | none required |
| 9 | [`09_image-1787893499406_sanitized.jpg`](../images/sanitized/09_image-1787893499406_sanitized.jpg) | Screw-terminal power-harness breakout and multi-conductor wiring used for detachable source/load connections. | none required |
| 10 | [`10_image-1787893506140_sanitized.jpg`](../images/sanitized/10_image-1787893506140_sanitized.jpg) | Sanitized dashboard overview showing MCU temperature, Wi-Fi status, threshold monitoring, live power, Power Monitor statistics, and RC Analyzer results. | cropped to remove browser/laptop identifiers |
| 11 | [`11_1000017942_sanitized.jpg`](../images/sanitized/11_1000017942_sanitized.jpg) | OLED main-menu page showing the unified EE LAB TOOL interface and analyzer selection. | none required |
| 12 | [`12_1000017943_sanitized.jpg`](../images/sanitized/12_1000017943_sanitized.jpg) | OLED Source Test result screen. The photographed negative source-resistance result is retained as a validation issue, not accepted as a physical source model. | none required |
| 13 | [`13_1000017944_sanitized.jpg`](../images/sanitized/13_1000017944_sanitized.jpg) | OLED Point Capture confirmation with the measured voltage and current for an accepted source-test point. | none required |
| 14 | [`14_1000017945_sanitized.jpg`](../images/sanitized/14_1000017945_sanitized.jpg) | OLED duplicate-point rejection message demonstrating source-test data-quality screening. | none required |
| 15 | [`15_1000017947_sanitized.jpg`](../images/sanitized/15_1000017947_sanitized.jpg) | OLED I-V sweep visualization from the Diode Analyzer. | none required |
| 16 | [`16_1000017946_sanitized.jpg`](../images/sanitized/16_1000017946_sanitized.jpg) | OLED Source Test collection screen showing the current point count and short/long press controls. | none required |
| 17 | [`17_1000017940_sanitized.jpg`](../images/sanitized/17_1000017940_sanitized.jpg) | OLED I-V sweep numerical/statistical page documenting the captured sweep summary. | none required |
| 18 | [`18_1000017941_sanitized.jpg`](../images/sanitized/18_1000017941_sanitized.jpg) | OLED I-V sweep graph, alternate captured frame. | none required |
| 19 | [`19_1000017939_sanitized.jpg`](../images/sanitized/19_1000017939_sanitized.jpg) | OLED I-V sweep graph, alternate captured frame preserving the displayed curve. | none required |
| 20 | [`20_1000017938_sanitized.jpg`](../images/sanitized/20_1000017938_sanitized.jpg) | OLED I-V sweep statistics/graph frame documenting the embedded visualization workflow. | none required |
| 21 | [`21_image-1787893815724_sanitized.jpg`](../images/sanitized/21_image-1787893815724_sanitized.jpg) | Sanitized dashboard view showing live voltage/current/power, Power Monitor session statistics, RC Analyzer results, and the silicon-diode result. | cropped to remove browser/laptop identifiers |
| 22 | [`22_image-1787893821029_sanitized.jpg`](../images/sanitized/22_image-1787893821029_sanitized.jpg) | Sanitized dashboard close-up showing the silicon-diode result and the three-point Source Test fit that produced a negative resistance and therefore requires validation. | cropped to remove browser/laptop identifiers |
| 23 | [`23_image-1787893828096_sanitized.jpg`](../images/sanitized/23_image-1787893828096_sanitized.jpg) | Sanitized dashboard charts showing recent voltage/current/power history and RC charge/discharge traces. | cropped to remove browser/laptop identifiers |
| 24 | [`24_image-1787893835341_sanitized.jpg`](../images/sanitized/24_image-1787893835341_sanitized.jpg) | Sanitized dashboard view showing RC traces, MCU internal-die temperature history, and experiment/fault export controls. | cropped to remove browser/laptop identifiers |
| 25 | [`25_image-1787893841248_sanitized.jpg`](../images/sanitized/25_image-1787893841248_sanitized.jpg) | Sanitized dashboard view showing MCU temperature history and the experiment-history table with CSV/JSON export controls. | cropped to remove browser/laptop identifiers |
| 26 | [`26_image-1787893852127_sanitized.jpg`](../images/sanitized/26_image-1787893852127_sanitized.jpg) | Sanitized close-up of the experiment-history table and update timestamp. | cropped to remove browser/laptop identifiers |

## Repository update summary
The current GitHub repository predates the final integrated firmware and still describes an initial two-subsystem snapshot. The final update should preserve the existing historical material while replacing the top-level project description with the present five-mode instrument, adding the exact working firmware modules, adding sanitized photographs and design assets, and publishing the final log in Markdown, JSON, DOCX, and PDF formats. See `docs/CODEX_REPOSITORY_UPDATE_INSTRUCTIONS.md` for the exact implementation procedure and acceptance criteria.
