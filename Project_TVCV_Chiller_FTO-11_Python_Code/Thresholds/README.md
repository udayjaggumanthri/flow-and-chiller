### Thresholds_controller.py

Location: TVCV_stable_Code/Thresholds/Thresholds_controller.py

Purpose:
Defines all threshold rules used to evaluate incoming telemetry (Temperature, Vibration, Voltage, Current, etc.) for all TVCV devices.  
These thresholds drive alarm generation through `param_Check_Controller.py`, determining when parameters exceed acceptable operating ranges.

The module provides a dictionary named `THRESHOLDS` organized by device token:

- tvcv1
- tvcv2 (duplicate of tvcv1)
- tvcv3 (800TR chiller)
- tvcv4
- tvcv5

Threshold Structure:
Each device entry contains keys representing telemetry parameters.  
Each parameter may define:

1. **Single-number threshold**  
   Example:  
   `"Temperature": { "minor": 50 }`  
   Meaning: Temperature > 50 triggers a MINOR alert.

2. **Multi-severity thresholds**  
   Example:  
   `"RN_Voltage": { "major": 245.0, "critical": 250.0 }`  
   Meaning:

   - Value > 245 → MAJOR
   - Value > 250 → CRITICAL

3. **Flat numeric thresholds (not used here but supported)**
4. **Tuple ranges (min, max)**  
   Example (Voltage LL):  
   `"RY_Voltage": { "minor": (430), "major": (440) }`  
   Expected values are above these thresholds; breaching triggers alerts.

Device-Specific Threshold Profiles:

1. tvcv1

- Temperature (minor)
- RMS Velocities (minor)
- Line voltages: RY, YB, BR (minor/major)
- RN, BN, YN voltages (major/critical)

2. tvcv2

- Duplicate of tvcv1 for convenience:
  `THRESHOLDS["tvcv2"] = {**THRESHOLDS["tvcv1"]}`

3. tvcv3 (800TR chiller)

- Higher temperature limit (60)
- RMS velocities similar to tvcv1
- Voltage thresholds same as tvcv1/tvcv2
- Installs major/critical thresholds for RN/BN/YN voltages

4. tvcv4

- Full vibration set (RMS + Peak accelerations)
- Current thresholds (minor = 750)
- Voltage, PF, frequency ranges enabled
- Includes full average voltage and current-related checks

5. tvcv5

- Similar to tvcv1/tvcv3 but with fewer vibration parameters enabled

Notes:

- Several thresholds are commented out; they can be reactivated when needed.
- This configuration directly affects:
  - Alarm generation severity
  - Email notification content
  - Daily alarm summaries
- Threshold values represent operational safety limits and must be validated with engineering teams before deployment.

Usage:
Imported by:

- `param_Check_Controller.py` for threshold evaluation
- `mail_Controller.py` to display threshold limits in alert emails

Extending:
To add a new device:
