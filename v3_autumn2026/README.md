# Data Acquisition — v3 (autumn 2026)

PsychoPy protocol for **video-guided upper-limb movements** (left and/or right arm) with simultaneous
**EEG + EMG** acquisition. Used for the recordings starting in **November 2026**.

The script shows instruction videos, sends event markers over **LSL** (`stimulus_stream`) and optionally
**Arduino hardware triggers**, then writes a CSV log and BIDS-style event files for each run.
The EEG/EMG signal itself is recorded separately with **LabRecorder** (`.xdf`).

> Previous versions: [`../v1_fall2025`](../v1_fall2025) (14/11/2025), [`../v2_fall2025`](../v2_fall2025) (from 20/11/2025).
> Session quality check: see [`README_QC.md`](README_QC.md).

---

## 1. Folder content

| File | Role |
|---|---|
| `eeg_emg_v3.py` | **Main script**: GUI, timing, video playback, markers/triggers, logging, BIDS export |
| `MOVEMENTS_shared_fall2026.py` | **Movement definitions** (the `MOVEMENTS` dictionary, 73 movements). Edit movements here, not in the main script |
| `baselines.py` | 6 baseline positions, `baseline_of()` and `validate_movements()` (consistency checks at launch) |
| `visual_task_simple.py` | `Trigger` class (Arduino serial trigger) |
| `qc_session.py` + `README_QC.md` | Post-session quality check of the `.xdf` file |
| `eeg_emg_v3_backup.py` | Backup copy of an earlier state of the main script |
| `logs/` | Per-run CSV logs (`stim_log_YYYYMMDD_HHMMSS.csv`) |
| `Data/raw/<sub>/ses-001/eeg-emg/` | BIDS-style event files and templates, created at the end of each run |

Shared resources live outside this folder:

- `../stimuli/videos_reencoded/` — `.mp4` videos used by the script (`MEDIA_DIR`)
- `../stimuli/videos_measures_720p/` — original `.mov` videos (101 files)
- `../stimuli/audio/eyes_open.wav` — sound played at the end of the eyes-closed resting state
- `../common/` — Arduino → LSL bridge (EMG)
- `../tools/` — `.xdf` reading, real-time viewer, EMG-only script

---

## 2. Setup

**Requirements:** Python 3.10, [PsychoPy](https://www.psychopy.org/), `pylsl`, `pyserial`
(and `pyxdf`, `numpy`, `scipy` for the QC).

```bash
conda create -n npulse python=3.10
conda activate npulse
pip install psychopy pylsl pyserial pyxdf numpy scipy
```

`requirements.txt` at the root is a full environment freeze (Windows); you normally do not need all of it.

---

## 3. Running a session

1. Start the LSL streams for the amplifiers (EEG, EMG) and open **LabRecorder**.
2. Run the script **from the `v3_autumn2026` folder** (logs and `Data/` are created in the current directory):

   ```bash
   cd v3_autumn2026
   python eeg_emg_v3.py
   ```

3. Fill in the dialogs:
   - **Participant / Acquisition**: subject ID (e.g. `sub-001`), EEG and EMG sampling rates (default 1024 Hz).
   - **Start options**: optional resting state (eyes open / eyes closed, 60 s each by default) and the
     **baseline position** (see §5).
   - **Movements** (2 pages): tick the movements to record. Only movements of the chosen baseline are listed.
   - **Arms**: left, right, or both.
   - **Timing and design**: durations, repetitions per movement (default **3**), order (random / ordered),
     LSL test pings, fullscreen.
4. On the "Start your LabRecorder now" screen, click **Update** in LabRecorder, tick `stimulus_stream`
   next to the EEG/EMG streams, set *Participant* and *Session*, then **Start**.
5. At the end, the screen shows "Finished! Thank you." and the terminal prints where the log and event files were saved.
   Click **Stop** in LabRecorder, then run the QC (see [`README_QC.md`](README_QC.md)).

`Esc` quits the experiment at any time.

> ⚠️ **Before each session, check at the top of `eeg_emg_v3.py`:**
> - `session_label` (hard-coded `"ses-001"`) — change it for a new session.
> - **Arduino trigger**: in the repository version the trigger is **disabled** (`trigger = None`).
>   To send hardware triggers, uncomment `from visual_task_simple import Trigger` and
>   `trigger = Trigger(source="arduino", port="COM6")` (the name of the port depends on the computer used).
> - In LabRecorder, change *Participant* / *Session* before **Start**, otherwise a file can be overwritten.

---

## 4. Trial structure

For each **block** (one movement × one arm):

```
new-block screen → instruction → fixation + label
→ CUE (instruction video)
→ for each repetition:
      instruction → PREP (countdown) → MOVE (video, perform in sync) → RETURN → ITI
→ inter-block fixation
```

Default timings (editable in the GUI): cue 3 s, prep 3 s, return 2 s, ITI 2 s, fixation 1 s, inter-block fixation 5 s.
The MOVE phase lasts as long as the video. The marker is sent on the first displayed frame (video loading excluded).

If a video file cannot be found, a message is shown on screen, marker `9801` is sent and the script moves on to the next block.

---

## 5. Baseline positions

The participant starts each movement from one of **6 baseline positions**
(orientation of the palm × state of the hand):

| Code | Position | | Code | Position |
|---|---|---|---|---|
| 1 | Palm up (hand open) | | 4 | Fist up (hand closed) |
| 2 | Palm side (hand open) | | 5 | Fist side (hand closed) |
| 3 | Palm down (hand open) | | 6 | Fist down (hand closed) |

`orientation = ((code − 1) % 3) + 1` (1 up, 2 side, 3 down) and the hand is closed if `code ≥ 4`.

Video file names are prefixed with the orientation (`1_up_`, `2_side_`, `3_down_`). The start state of each
movement is set in `MOVEMENTS_shared_fall2026.py` (`start`), and the baseline code is computed from both.
Movements per baseline: 11 / 14 / 14 / 11 / 12 / 11.

---

## 6. Event codes

### LSL markers (`stimulus_stream`)

```
marker = phase × 10000 + arm × 1000 + baseline × 100 + movement
```

| Field | Values |
|---|---|
| phase | `cue` 1, `prep` 3, `move` 5, `return` 7, `iti` 9 |
| arm | `Left` 1, `Right` 2 |
| baseline | 1–6 (§5) |
| movement | `code` from `MOVEMENTS_shared_fall2026.py` |

Example: `11205` = cue, left arm, baseline 2 (palm side, open), movement 5.

Special markers:

| Marker | Meaning |
|---|---|
| `9701` / `9702` | Resting state eyes open / eyes closed |
| `9999` | LSL test ping (×5 at start, optional) |
| `8888` | "Ready" screen (LabRecorder reminder) |
| `8899` | End of the run |
| `9801` | Block skipped (video not found) |

### Arduino trigger

Currently the Arduino trigger only carries the **phase code** (`make_trigger()` returns `phase_code`);
resting state uses `1` (eyes open) and `2` (eyes closed). Encoding the movement in the 8-bit trigger is not implemented yet (see §8).

---

## 7. Outputs

Created in the **current working directory** at the end of the run:

- `logs/stim_log_YYYYMMDD_HHMMSS.csv` — one row per event (`phase`, `lsl_t_start`, `lsl_t_end`, `duration_s`,
  `lsl_marker`, `arduino_trigger`, `subject_id`, `block`, `rep`, `arm`, `base_code`, `move_code`, `movement_key`,
  `file`, `psychopy_version`, `eeg_fs`, `emg_fs`).
- `Data/raw/<sub>/ses-001/eeg-emg/`:
  - `<sub>_ses-001_task_events.tsv` / `.json` — BIDS events (onset relative to the first event)
  - `<sub>_ses-001_task_movement.json` — sidecar for the recording
  - `channels.tsv`, `electrodes.tsv`, `coordsystem.json` — empty templates, to fill in with the real montage

The `.xdf` / EDF recording is saved by LabRecorder, not by this script. Expected name: `<sub>_ses-001_task_movement`.

Example of an events file: [`Data/raw/sub-001/ses-001/eeg-emg/`](Data/raw/sub-001/ses-001/eeg-emg/).

---

## 8. Known issues / to do

- **Arduino 8-bit trigger**: the highest movement code is 39, so `movement × 10 + phase` would exceed 255.
  The trigger currently carries the phase only. The `arduino_trigger` description in `events.json` still says `move*10 + phase` and needs to be updated.
- **Duplicate movement codes** reported by `validate_movements()` at launch (`[CHECK]` lines in the terminal): wrist
  flexion/extension with and without closed hand have different codes (31/32, 29/33), and code 34 is shared by
  several rotation movements. Check whether this is intended before analysis.
- **"Perform dur"** in the timing dialog is not used: the MOVE phase always lasts the full video.
- **Log saving** happens at the end of the run only; if the script crashes, the CSV is lost (the LSL markers remain in the `.xdf`).
- Hardware issues found by the QC (dead channel 24, gel bridges, …): see `README_QC.md`.
- Link to the dataset / videos: *to add* (access to the N-Pulse Drive required).
