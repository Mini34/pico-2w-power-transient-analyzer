# Image accuracy review — 4 September 2026

Scope: the public `images/designs/` assets in this repository and the corresponding portfolio imagery in `Mini34/signal-and-self`.

## Prototype overview

The earlier overview placed several leader endpoints on the work mat, loose wiring, or beside the intended component. The revision uses the [original overview photograph](../images/sanitized/01_image-1787893448668_sanitized.jpg), checked against the [sensor/display close-up](../images/sanitized/05_image-1787893467914_sanitized.jpg) and [controller close-up](../images/sanitized/06_image-1787893481899_sanitized.jpg).

Callouts identify components, not individual electrical terminals. The partly cropped load resistor and ambiguous general power-wiring pointer are omitted. Consult the source photographs and pin map for physical evidence and electrical details; the annotation layer is an explanatory aid.

The final overlay is deterministic, not an imagegen reconstruction. Two generated candidates were rejected. The [editable SVG](../images/designs/01_annotated_prototype_overview.svg) embeds the original JPEG unchanged; [the builder](../tools/build_annotation.py) verifies that every PNG pixel outside the callout mask matches the decoded source photograph exactly.

## Retired visuals

| Asset | Reason | Replacement |
|---|---|---|
| `02_verified_system_architecture.png` | Unlabelled arrows mixed the external load-power path with controller connections and placed software blocks on an electrical ground line. Several text lines ran outside their boxes. | [Functional architecture and pin map](SYSTEM_ARCHITECTURE.md), grounded in the checked-in firmware and project log. |
| `04_generated_technical_brief_visual.png` | Reconstructed dashboard panels were presented as reference screenshots; its future-tense guard work and repository checklist were outdated. A small concept disclaimer did not resolve that ambiguity. | Original sanitized dashboard photographs, the current README, and firmware status notes. |
| `05_generated_project_timeline_visual.png` | The 400 kHz label conflicts with the current 50 kHz bus; a diode example mixes the Vf/current units; the I-V sweep is described as verified without the display-only boundary. | Dated project log and current README measurement table. |
| `EE_Lab_Tool_Design_Assets.pdf` | Bundles the superseded annotated and generated visuals. | This review, corrected overview, and functional architecture. |

The conceptual 3D image was already absent from the remote repository before this review. It was not restored.

## Retained material

- All original and sanitized hardware/dashboard photographs remain unchanged. Photographs of invalid measurements are still evidence of debugging, with their existing limitations.
- The older export manifests, illustrated log, and repository-update instructions remain dated historical records. Their references to retired design assets do not describe the current asset inventory.
- The portfolio's social artwork and decorative world-map background contain no project measurements or pin assignments. They remain in use; neither is used as engineering proof. The map's numerical information is supplied separately by its sourced data table.
- Website QA screenshots are historical layout evidence, not generated representations of the instrument.

No new hardware test or measurement is claimed by this visual review.
