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
    Channels from the known-broken list start their reasons with `known broken (KNOWN_BAD)`.

---

## Reading the result

- Each test shows **PASS / INFO / WARN / FAIL / SKIP** and the **reason**.
  **INFO** = good to know, no effect on the verdict.
- Two verdicts, **EEG** and **EMG**:
  - 🟢 **GREEN**: OK.
  - 🟠 **ORANGE**: usable with caution (read the reasons).
  - 🔴 **RED**: redo the session or fix the setup.

## The 9 tests

| # | Test | What it checks | Typical problem detected |
|---|---|---|---|
| 1 | File complete | Cap recognised (64 or 128), actual sampling rate, no gaps, sufficient duration, file not corrupted | unstable USB cable, LabRecorder stopped too early, download not finished |
| 2 | Channel names (metadata) | Every channel has a name in the `.xdf` header: `channel_count` = number of names = number of data columns, no empty or duplicated name | names written for the first amplifier only → unnamed channels hidden in the visualisation / decoding |
| 3 | Events (triggers) | Triggers present, complete trials (prep → move → return), regular durations | Arduino not connected, `trigger = None` left in the code, wrong COM port, lost triggers |
| 4 | Markers / TRIGGER channel | The `TRIGGER` label is on the channel that really holds the trigger (last column); trigger codes are known ones; sync pulses (128) present; `stimulus_stream` LSL markers recorded, not empty, inside the EEG recording and consistent with the TRIGGER channel | label on the wrong channel (no markers in the visualisation), other script / Arduino version, `stimulus_stream` not ticked in LabRecorder |
| 5 | Inactive channels | EEG: flat, saturated or disconnected channels. EMG: which inputs carry a signal | dead EEG electrode, EMG box not connected |
| 6 | EEG: ground / reference | All channels noisy at the same time | ground (GND) or reference badly placed, amplifier charging |
| 7 | EEG: noise per channel | 50 Hz, high-frequency noise, isolated channels, gel bridges | badly gelled electrode, too much gel between electrodes |
| 8 | EMG: noise | Plausible muscle signal, 50 Hz, two identical channels | bad contact, electrodes touching each other |
| 9 | Stability | Does quality drop between the start and the end of the session? | gel drying, electrode coming off |

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
  Trigger codes are read as `10 × movement + phase` (e.g. `15` = movement 1, *move*); older sessions
  that only send the phase (`1, 3, 5, 7, 9`) are read the same way. A missing `stimulus_stream` is only
  INFO by default; set `MARKER_STREAM_REQUIRED = True` (top of the script) to make it a WARN.
- **Known broken channels (`KNOWN_BAD`)**: list at the top of the script, per amplifier (key = exact LSL
  stream name, e.g. `eegoSports 0000`, channel numbers as printed by the QC). These channels are still
  tested, but shown as *known, to repair* and no longer turn the verdict orange / red. `bridges` lists
  groups of electrodes known to be shorted together: a bridge inside one group is ignored, any other bridge
  is still reported. When a known channel looks fine again, the QC says so → remove it from the list once
  the electrode is repaired. The current list (Nov 2026) is based on 14 sessions and still has to be
  confirmed by the hardware team, especially for the 64-electrode amplifiers (one participant each).
- **Thresholds**: at the top of the script (`CONFIGURATION` section). They are starting values, tested on
  simulated sessions and on real ones (P012, P0013, P014, P015, P016, P017).

---

## Known problems to fix (found by the QC, Sept–Nov 2026)

### Acquisition / software (to fix first)

- **Channel names on the 128 setup**: only 65 names for 177 channels (`Ch1`–`Ch64` + `TRIGGER`, i.e. the first
  amplifier only), and the `TRIGGER` label sits on channel 65 while the trigger data is in channel 177.
  The data is complete, but the visualisation hides channels 66–177 and a tool that looks up the trigger by
  name reads an EEG channel. The 64 setup is correct (73 names, `TRIGGER` on the last channel).
  → Fix the channel names written by the acquisition (eego / LSL configuration or script). Tests 2 and 4.
- **No `stimulus_stream` in any of the 14 files checked**: the events are only in the TRIGGER channel.
  → Tick `stimulus_stream` in LabRecorder before **Start**.
- **No sync pulses (128) on the 64 setup (Biotech, amplifiers 000650 / 000697)**, present on the 128 setup.
  → Use the same version of `eeg_emg_v3.py` / Arduino code on both computers.
- **Same participant / session IDs used on both setups** (two different "P017 S001" and "P017 S002" files,
  hence the `-2` suffix when downloading), and malformed ID `P0013`.
  → Agree on one ID convention for both setups.

### Hardware to check

128-electrode cap (`eegoSports 0000`, in `KNOWN_BAD`):

- **EEG channel 24 is dead** in every 128-cap session (P012, P014, P015, P016, P017).
  → Check this electrode, its connector and its cable.
- **Channels 12 and 108 are bridged** in almost every session.
- **EEG channels 19, 87, 97 and 106** are isolated from their neighbours, bridged together and noisy at 50 Hz (P017 S001).
  → Check whether they share a connector, then re-gel them.

64-electrode cap (amplifiers `000650` and `000697`, in `KNOWN_BAD`):

- **M1 and CP1** are bad in every session; **AF7 and AF8** too on amplifier 000650.
- **Two blocks of electrodes record identical signals** (correlation ≈ 0.999) in every session and for
  different participants: CP2 / P4 / O2 / P2 / PO4 / PO6 / PO8 (000650; 28/31/57/63 on 000697) and
  PO3 / PO5 / PO7 (both amplifiers). This looks like a short circuit or gel residue in the cap rather than
  too much gel on the day.
  → Inspect / clean the cap at these positions.
- **Strong 50 Hz on all channels with amplifier 000650** (P017 S001-2, S002-2: red).
  → Check ground (GND) and reference on this setup.

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

- **No phase triggers** in P014 S001 and P015 S002 run 1: the sync pulses were there, but not the phase codes.
  → In `eeg_emg_v3.py`, check that the `Trigger` line is uncommented and that the COM port (COM6 / COM10) is right.
- **A file can be overwritten** if *Participant* / *Session* are not changed in LabRecorder.
  → Update them before clicking **Start**.

### To decide: where to run the QC

The `.xdf` is saved by LabRecorder on the CHUV computer, not on the computer running `eeg_emg_v3.py`. Two options, without downloading the files:

- **On the CHUV computer**, between two sessions: `git pull` the repo there, `pip install pyxdf numpy scipy`, run `python qc_session.py` after **Stop**.
- **On our computer**: find a way to access these files from our computer, so we have a local copy and can run the QC there. One idea: run a second LabRecorder on our computer during the session, which records its own copy of the `.xdf`.

→ Test both at the next session and keep the one that works.
