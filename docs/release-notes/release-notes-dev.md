Release Notes (Development)
===========================

Changes merged into master
--------------------------
| Jira Task | GitHub Issue | Type | Description |
|-----------|--------------|------|-------------|
| I04_1-143 | [#62](https://github.com/DiamondLightSource/PuckBarcodeReader/issues/62) | Minor | Record summary table color changes. |
| I04_1-172 | [#64](https://github.com/DiamondLightSource/PuckBarcodeReader/issues/64) | Minor | New Start/Stop scan button added. |

Change Types:
* Major - Backward incompatible change
* Minor - Backward compatible change in API/functionality
* Patch - Bug fix, no change in functionality

A new start/stop scan button has been added to the gui.
The button allows users to start/stop the scan.
The layout of the button changes accordingly to the state of the scanner:
- green start for when the scanner is stopped
- red stop for when the scaner is running

