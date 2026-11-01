# EEG/EMG Upper-Limb Movement Task

This repository contains a PsychoPy-based experiment for **video-guided upper-limb movements** (left and/or right arm) with simultaneous EEG/EMG acquisition.

The script:
- Presents movement instruction videos.
- Sends event markers over **LSL** (`stimulus_stream`).
- Sends **Arduino triggers** via a `Trigger` device (e.g. on `COM6`).
- Logs detailed per-event information to CSV.
- Exports **BIDS-style** metadata and event files for integration with EDF recordings saved via LabRecorder.

---

## 1. Main Files and Directories

- **Main experiment script**  
  `eeg_emg_v2.py` 
  Contains all PsychoPy logic (GUI, timing, playback, markers, logging, BIDS export).

- **Movement definitions**  
  `MOVEMENTS_shared.py`
  This is where the **`MOVEMENTS` dictionary** is defined:
  - movement labels
  - baseline codes (`baseline_code`)
  - video filenames (`file`)
  - movement codes (`code`)

- **Past scripts** 
  `eeg_emg_v1.py`
  Contains the PsychoPy code version used for 14/11/2025 recordings

  `MOVEMENTS_shared_14112025.py`
  Contains the movements definitions used for 14/11/2025 recordings

  > ⚠️ **Important:**  
  All changes to which movements exist, how they’re named, or which video file they use should be made in **`MOVEMENTS_shared.py`** not in the main experiment script.

- **Videos**  
  `Experiment/videos_measures_720p/`  
  Contains the movement instruction videos. The script searches for files there using the filenames defined in `MOVEMENTS`.

- **Logs**  
  `logs/`  
  Contains per-run CSV logs, e.g.:
  - `stim_log_YYYYMMDD_HHMMSS.csv`

- **BIDS-like data**  
  `Data/raw/<sub>/<ses>/eeg-emg/`  
  Automatically created at the end of each run. For example:
  - `Data/raw/sub-001/ses-009/eeg-emg/sub-001_ses-009_task_movement.edf` (expected EDF name from LabRecorder)
  - `sub-001_ses-009_task_movement.json` (EDF sidecar)
  - `sub-001_ses-009_task_events.tsv` (events)
  - `sub-001_ses-009_task_events.json` (events metadata)
  - `channels.tsv`, `electrodes.tsv`, `coordsystem.json` (templates)

---

## 2. Code Structure (High-Level)

The main script is structured into the following sections:

1. **Imports & Global Configuration**
   - Imports PsychoPy, pylsl, `Trigger`, standard libraries.
   - Sets:
     - `MEDIA_DIR` → folder with instructional videos.
     - `PHASE` codes (cue, prep, move, return, iti).
     - `ARM_CODES` (`Left`, `Right`).
     - `BASELINE_NAMES` (up / side / down).
     - `REST_CODES` (eyes open/closed for resting-state).
   - Imports `MOVEMENTS` from `MOVEMENTS_shared.py` / `movement_shared.py`.

2. **Helpers for Labels & Movement Keys**
   - `strip_baseline_suffix()`  
     Removes `(up)`, `(side)`, `(down)` from labels (nicer GUI text).
   - `movement_root()`  
     Removes prefixes like `1_up_`, `2_side_`, `3_down_` from keys/filenames.

3. **Markers & Triggers**
   - `make_marker(phase_code, arm_code, base_code, move_code)`  
     Builds an integer LSL marker:
     ```text
     marker = phase*10000 + arm*1000 + base*100 + move
     ```
   - `make_trigger(phase_code, move_code)`  
     Builds an Arduino trigger:
     ```text
     trigger = move*10 + phase
     ```
   - `push_event_codes(outlet, arm, phase, base_code, move_code, trigger_dev)`  
     Sends both:
       - LSL marker via `outlet.push_sample([marker])`
       - Arduino trigger via `trigger_dev.setData(trigger)` (if `trigger_dev` is not `None`)

4. **Resting-State Routines**
   - `_timed_screen()`  
     Generic “draw for N seconds” loop.
   - `record_resting_state()`  
     Optional eyes-open and eyes-closed blocks at the start, with LSL markers and Arduino triggers.

5. **GUI Configuration**
   - `setup_gui()`  
     Shows configuration dialogs to set:
     - Subject ID, EEG/EMG sampling rates.
     - Whether to include resting-state (eyes open/closed) and durations.
     - Baseline orientation (up / side / down).
     - Which movements (from `MOVEMENTS`) to include for the chosen baseline.
     - Which arms (Left, Right) to use.
     - Timing parameters (cue, prep, move, return, ITI, etc.).
     - Design parameters (#reps, random vs ordered blocks, inter-block fixation).
     - Fullscreen vs windowed, LSL test pings.

6. **Media Resolution & Playback**
   - `arm_candidates(basefile, arm)`  
     Proposes candidate filenames like:
     - `<base>_left.mp4`, `<base>_right.mov`, `<base>.mp4`, etc.
   - `resolve_media_path(move_key, arm)`  
     Uses `MOVEMENTS[move_key]["file"]` to find the actual file in `MEDIA_DIR`.
   - `play_movie_robust()`  
     Plays the video with a text fallback if loading fails.

7. **Countdown**
   - `show_countdown(win, secs, txt_stim)`  
     Simple on-screen countdown before movement.

8. **Main Experiment (`main()`)**
   - Creates LSL outlet (`stimulus_stream`).
   - Calls `setup_gui()` to get all configuration parameters.
   - Opens a PsychoPy window.
   - Optionally sends test LSL pings (marker 9999).
   - Shows “ready” message and global countdown.
   - Optionally runs resting-state (eyes open/closed).
   - Builds blocks = `arms × movements`.
   - For each block and repetition:
     - Shows block intro text.
     - Plays cue video (instruction only).
     - PREP: countdown with markers.
     - MOVE: plays movement video while participant performs movement.
     - RETURN: “Return to baseline” text.
     - ITI: fixation and optional markers.
     - Each phase logs to `event_log`.
   - After all blocks:
     - Saves `logs/stim_log_*.csv`.
     - Writes BIDS-style events and metadata in `Data/raw/.../eeg-emg/`.
     - Shows on-screen summary and waits for keypress.
     - Sends final LSL marker (8899) and closes.

---

## 3. Movement Definitions (`MOVEMENTS`)

All information about the movements is defined in **`MOVEMENTS_shared.py`** (or `movement_shared.py`):

- Each entry in `MOVEMENTS` typically includes fields such as:
  - `"label"`: Human-readable name (shown in GUI).
  - `"baseline_code"`: 1 (up), 2 (side), or 3 (down).
  - `"file"`: Base video filename (without arm suffix).
  - `"code"`: Canonical integer code for the movement.

Example (pseudocode style):

```python
MOVEMENTS = {
    "1_up_openhand_slow_3sec": {
        "label": "Open hand slow (up)",
        "baseline_code": 1,
        "file": "openhand_slow_3sec",
        "code": 1,
    },
    ...
}
