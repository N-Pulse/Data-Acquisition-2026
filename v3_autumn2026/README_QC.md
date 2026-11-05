# EEG/EMG session QC — `qc_session.py`

**Purpose:** right after a session, check in ~30 s that the recording is technically sound
(inactive channels, ground / reference, noise), so that the session can be **redone** while the participant
is still there.

---

## How to use it (terminal)

### 1. One-time setup

On the computer where LabRecorder saves the `.xdf` files:

```bash
cd ~/Data-Acquisition-2026
pip install pyxdf numpy scipy       # only these 3 are needed for the QC (add --user if permission denied)
```

### 2. After each session

1. In LabRecorder, click **Stop** and wait until the file is saved.
2. Run the QC:

```bash
cd ~/Data-Acquisition-2026/v3_autumn2026
python qc_session.py
```

Without a file name, the script takes the **most recent `.xdf`** in `~/Documents/CurrentStudy`,
`~/Documents` or `~/Downloads`. It prints which file it took and how old it is.
Check that it is the session that just ended.

To check a specific file:

```bash
python qc_session.py ~/Documents/CurrentStudy/sub-P017/ses-S001/eeg/sub-P017_ses-S001_task-Default_run-001_eeg.xdf
```

Tip: type `python qc_session.py ` (with a space), then drag the file from the Finder / file explorer
into the terminal to paste its path.

### 3. Check several files at once

```bash
for f in ~/Downloads/*.xdf; do python qc_session.py "$f" > "${f%.xdf}_qc.txt" 2>&1; done
grep -H "VERDICT" ~/Downloads/*_qc.txt              # one verdict per file
grep -H -E "^   (WARN|FAIL)" ~/Downloads/*_qc.txt   # only the problems, with their reason
```

### 4. Outputs

- On screen: each test with its status and reason, then the verdicts.
- Next to the `.xdf`, in the folder `<file>_QC/`:
  - `qc_summary.txt`: everything printed on screen;
  - `qc_channels.csv`: one line per channel (status, reasons, offset, 50 Hz noise...).

---

## Reading the result

- Each test shows **PASS / INFO / WARN / FAIL / SKIP** and the **reason**.
  **INFO** = good to know, no effect on the verdict.
- Two verdicts, **EEG** and **EMG**:
  - 🟢 **GREEN**: OK.
  - 🟠 **ORANGE**: usable with caution (read the reasons).
  - 🔴 **RED**: redo the session or fix the setup.

## The 7 tests

| # | Test | What it checks | Typical problem detected |
|---|---|---|---|
| 1 | File complete | Cap recognised (64 or 128), actual sampling rate, no gaps, sufficient duration, file not corrupted | unstable USB cable, LabRecorder stopped too early, download not finished |
| 2 | Events (triggers) | Triggers present, complete trials (prep → move → return), regular durations | Arduino not connected, `trigger = None` left in the code, wrong COM port, lost triggers |
| 3 | Inactive channels | EEG: flat, saturated or disconnected channels. EMG: which inputs carry a signal | dead EEG electrode, EMG box not connected |
| 4 | EEG: ground / reference | All channels noisy at the same time | ground (GND) or reference badly placed, amplifier charging |
| 5 | EEG: noise per channel | 50 Hz, high-frequency noise, isolated channels, gel bridges | badly gelled electrode, too much gel between electrodes |
| 6 | EMG: noise | Plausible muscle signal, 50 Hz, two identical channels | bad contact, electrodes touching each other |
| 7 | Stability | Does quality drop between the start and the end of the session? | gel drying, electrode coming off |

## Good to know

- **Cap**: 64 or 128 electrodes, recognised automatically.
- **EMG**: the script looks among all bipolar / AUX inputs for those that carry a signal (they activate
  during movements). Inputs that are not plugged in are normal and are not penalised.
  Fewer than 4 EMG channels with signal → orange; none → red.
- **Events**: the script reads the TRIGGER channel (Arduino). During sessions, the Arduino must be enabled in
  `eeg_emg_v3.py`:

  ```python
  from visual_task_simple import Trigger                 # uncomment this import (top of the file)
  #trigger = None
  trigger = Trigger(source="arduino", port="COM6")       # COM6 or COM10, see the Notion protocol
  ```

  If the Arduino is disabled, the script can use the `stimulus_stream` markers instead
  (tick `stimulus_stream` in LabRecorder after launching `eeg_emg_v3.py` and clicking *Update*).
- **Thresholds**: at the top of the script (`CONFIGURATION` section). They are starting values, tested on
  simulated sessions and on real ones (P012, P0013, P015, P017).

---

## Known problems to fix (found by the QC, Sept–Nov 2026)

### Hardware to check (128-electrode cap)

- **EEG channel 24 is dead** in every 128-cap session (P012, P015, P017).
  → Check this electrode, its connector and its cable.
- **EEG channels 19, 87, 97 and 106** are isolated from their neighbours, bridged together and noisy at 50 Hz (P017 S001, S002).
  → Check whether they share a connector, then re-gel them.

### At setup

- **Too much gel** creates gel bridges: neighbouring electrodes with identical signals (P012 ≈ 50 channels, P015 S001 ≈ 30, P0013 posterior).
  → Use less gel and make sure it does not spread to the next electrode.
- **Missing EMG pairs**: only 6 of 8 pairs had signal (P012, P015 S003).
  → Check that all 8 pairs are plugged into the EMG box.
- **50 Hz on some EMG channels** (P0013, P017 channel 142).
  → Check the electrode contact; do not charge the amplifiers during the recording.
- **Slow drift on EMG** from heartbeat or moving cables (P0013 AUX12, AUX14).
  → Tape the EMG cables down. Harmless after the usual 20–500 Hz filter.

### Before each recording

- **No phase triggers** in P015 S002: the sync pulses were there, but not the phase codes.
  → In `eeg_emg_v3.py`, check that the `Trigger` line is uncommented and that the COM port (COM6 / COM10) is right.
- **A file can be overwritten** if *Participant* / *Session* are not changed in LabRecorder.
  → Update them before clicking **Start**.

### To decide: where to run the QC

The `.xdf` is saved by LabRecorder on the CHUV computer, not on the computer running `eeg_emg_v3.py`. Two options, without downloading the files:

- **On the CHUV computer**, between two sessions: `git pull` the repo there, `pip install pyxdf numpy scipy`, run `python qc_session.py` after **Stop**.
- **On our computer**: find a way to access these files from our computer, so we have a local copy and can run the QC there. One idea: run a second LabRecorder on our computer during the session, which records its own copy of the `.xdf`.

→ Test both at the next session and keep the one that works.

### Not urgent

- **Wrong channel names** in 128-cap files (65 names for 177 channels). Comes from the ANT-LSL configuration; the QC works around it.
