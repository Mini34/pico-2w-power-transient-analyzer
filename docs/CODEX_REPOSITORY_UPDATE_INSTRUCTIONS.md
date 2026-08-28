# Codex Repository Update Instructions

## Target

Update the existing private repository:

- **Repository:** `Mini34/pico-2w-power-transient-analyzer`
- **Default branch:** `main`
- **Recommended working branch:** `docs/final-ee-lab-tool-integration`

The current repository is an earlier Power/RC snapshot. This update must preserve its historical engineering evidence while bringing the repository to the final verified EE Lab Tool state.

## Non-negotiable constraints

1. Do not invent or reconstruct firmware that has not been verified on the Pico.
2. Copy the exact working MicroPython files from the current ChatGPT Work/Thonny project workspace.
3. Preserve all tested GPIO assignments and hardware behavior.
4. Do not expose Wi-Fi credentials, local IP addresses, browser tabs/bookmarks, laptop branding, user names, or other personal/system identifiers.
5. Do not describe MCU temperature as ambient temperature.
6. Do not describe software fault monitoring as electrical protection or automatic cutoff.
7. Do not treat a negative fitted source resistance as valid. Flag it as invalid and retain it only as a documented test/validation issue.
8. Preserve the user's intentional behavior that temperature sampling is deferred while the device is in `STARTUP` or `MENU`.
9. Preserve the timing-sensitive calls that suppress web/temperature work during RC acquisition and diode sweep acquisition.
10. Do not change working UI, dashboard, logger, or analyzer behavior merely for stylistic cleanup.

## Source bundle

Use the files in this documentation package as the authoritative repository-update input:

- `README.md`
- `docs/PROJECT_LOG.md`
- `docs/PROJECT_LOG.json`
- `docs/EE_Lab_Tool_Final_Project_Log.docx`
- `docs/EE_Lab_Tool_Final_Project_Log.pdf`
- `docs/EE_Lab_Tool_Photo_Appendix_All_26.pdf`
- `docs/EE_Lab_Tool_Design_Assets.pdf`
- `docs/PHOTO_INDEX.md`
- `images/sanitized/` (26 cropped/sanitized photographs)
- `images/designs/` (annotated overview, verified architecture, conceptual designs)
- `firmware/main.py` (the supplied current working main file)

The exact working copies of the following additional modules must be obtained from the active project workspace and committed without semantic changes unless a test proves a required correction:

- `instrument_state.py`
- `wifi_manager.py`
- `web_server.py`
- `experiment_logger.py`
- `fault_monitor.py`
- `source_characterizer.py`
- `ssd1306.py`

## Exact verified hardware contract

| Resource | Assignment |
|---|---|
| I2C SDA | GP6 |
| I2C SCL | GP7 |
| I2C implementation | SoftI2C, 50 kHz |
| Menu/select button | GP2, active low |
| RC charge | GP0 |
| RC transistor control/discharge | GP1 |
| RC ADC | GP26 / ADC0 |
| Diode source | GP3 |
| Diode source-side ADC | GP27 / ADC1 |
| Diode forward-voltage ADC | GP28 / ADC2 |
| Internal temperature | ADC4 |
| INA219 address | 0x40 |
| OLED address | 0x3C |

Preserve these calibration constants in the working firmware:

```python
V_SLOPE = 0.98896
V_OFFSET = -0.03531
SHUNT_OHMS = 0.1
TEMP_VREF = 3.24
```

## Required repository operations

### 1. Create a safe branch

```bash
git checkout main
git pull --ff-only
git checkout -b docs/final-ee-lab-tool-integration
```

### 2. Preserve the original snapshot

Do not delete the original 13 diagnostic photographs or the earlier log. Move/rename the old full DOCX only if needed for clarity, for example:

```text
docs/archive/EE_Summer_Project_Log_GitHub_Export_2026-08-24.docx
```

Retain Git history and avoid a destructive rewrite.

### 3. Replace/update documentation

- Replace the top-level `README.md` with the supplied final README.
- Replace `docs/PROJECT_LOG.md` with the supplied final Markdown log.
- Add `docs/PROJECT_LOG.json`.
- Add the final DOCX and all PDF deliverables.
- Add `docs/PHOTO_INDEX.md`.
- Add a short `docs/README.md` that links the log, photo appendix, design assets, and Codex brief.

### 4. Add sanitized photo assets

- Add all 26 files from `images/sanitized/`.
- Add all files from `images/designs/`.
- Do not replace these with the uncropped laptop/dashboard originals.
- Verify that no local IP such as the photographed dashboard address remains visible.
- Verify that no browser tabs, bookmarks, laptop logo/brand, or user-specific interface content remains visible.

### 5. Add exact working firmware

- Add the supplied `firmware/main.py`.
- Export/copy the exact working service modules listed above.
- Update `firmware/README.md` to describe deployment to the Pico.
- Add an example credentials/configuration template only if required by the working Wi-Fi manager.
- Never commit real SSIDs/passwords.

Recommended `.gitignore` additions:

```gitignore
# Local credentials and device-generated data
secrets.py
wifi_config.py
config.py
logs/
*.jsonl
__pycache__/
*.mpy
.thonny/
```

Only ignore `config.py` if the working project actually stores credentials there; do not hide a required public configuration file accidentally.

### 6. Source Test validation changes

Inspect the existing `source_characterizer.py` and UI workflow. Do not silently change the regression formula. Add validation around it:

- Require at least two distinct-current points; recommend at least three.
- Reject nearly identical current values.
- Confirm current polarity/sign convention before fitting.
- For the assumed source model `V = Voc - I*Rs`, require the fitted slope to be negative within a configurable tolerance.
- Calculate `Rs = -slope`.
- If `Rs < 0`, `Voc` is implausible, current span is too small, or numerical conditioning is poor, return `status = "invalid"` with a reason instead of `completed`.
- Keep the photographed `Voc = -0.003 V`, `Rs = -6.395 ohm`, `R^2 = 1.000`, 3-point result in documentation only as an invalid example.
- Add tests for a valid synthetic source and the invalid negative-Rs example.

Do not add automatic load switching or new GPIO assignments. The present mode is guided/manual.

### 7. Dashboard documentation and boundaries

The dashboard has already been verified. Preserve its working layout and endpoints. Documentation must state:

- MCU temperature is internal die temperature.
- Fault monitoring is monitoring/logging only.
- CSV/JSON downloads exist for experiments and faults.
- Diode PWM I-V data is display-only.
- Source Test invalid results are visibly marked.

### 8. Firmware validation

Perform checks appropriate for MicroPython without pretending CPython can execute hardware APIs:

- Parse/syntax-check every `.py` file.
- Search for accidental credentials and local IP addresses.
- Confirm all imports resolve on the Pico filesystem.
- Confirm no GPIO assignments changed.
- Confirm `main.py` still enters the menu and all five modes.
- Confirm RC and diode acquisition still call `service_background(allow_web=False)`.
- Confirm temperature sampling remains disabled in STARTUP/MENU per user preference.
- Confirm logging/network failures remain non-fatal.

Suggested static checks:

```bash
python -m compileall firmware
rg -n "password|passwd|ssid|10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\." .
rg -n "GP[0-9]+|ADC[0-9]+|SoftI2C|TEMP_VREF|V_SLOPE|V_OFFSET" firmware
```

Review false positives manually; do not remove legitimate private-range examples from generic documentation unless they identify the user's actual network.

### 9. Link and asset checks

- Verify every README and Markdown image link resolves.
- Verify every PDF/DOCX exists and is non-empty.
- Verify the 26-photo manifest matches the 26 files.
- Verify generated/conceptual images are labeled as conceptual where applicable.
- Ensure the exact architecture diagram, not a concept render, is used as the authoritative pin-map figure.

### 10. Commit and pull request

Use a clear commit sequence, for example:

```text
docs: add final illustrated project log and sanitized photo archive
firmware: add verified integrated EE Lab Tool sources
docs: update README for dashboard, logging, telemetry, source test, and faults
test: validate source-characterizer fit quality and invalid-result handling
```

Open a pull request against `main` with:

- a summary of all added capabilities;
- a note that the dashboard was user-verified;
- a note that source-test negative resistance remains invalid/pending refinement;
- a privacy statement confirming dashboard photos were sanitized;
- a checklist showing all 26 photographs and final PDFs were added.

## Acceptance criteria

The repository update is complete only when:

- The README describes the five-mode integrated instrument, not the old two-subsystem snapshot.
- The final Markdown, JSON, DOCX, and PDF logs are present.
- All 26 sanitized photographs are present and indexed.
- The photo appendix and design-assets PDFs open correctly.
- The exact working firmware modules are present, with no credentials.
- Pin assignments and calibration constants match the verified hardware.
- Dashboard documentation covers live power, RC traces, diode results, MCU telemetry, Source Test, faults, history, and CSV/JSON export.
- Source Test invalid negative resistance is rejected/flagged.
- No automatic load bank or hardware cutoff is falsely claimed.
- All internal links and image paths pass review.
- The pull request explains what was verified on hardware and what remains future work.
