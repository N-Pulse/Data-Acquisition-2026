# EEG/EMG protocol - version 1 used for 14/11/2025 recordings


# -*- coding: utf-8 -*-
from psychopy import core, visual, event, gui, prefs
import psychopy  # for psychopy.__version__
from pylsl import StreamInfo, StreamOutlet, local_clock
import os, random, re, gc
from collections import OrderedDict
import csv, time
from visual_task_simple import Trigger


trigger = Trigger(source="arduino", port="COM6")

# Prefer stable movie backends (harmless if missing)
prefs.general['moviesLib'] = ['ffpyplayer', 'moviepy', 'avbin']

MEDIA_DIR = r"C:\Users\eeguser\Documents\NPulseBCI\github\DSI\code_experiments_fall_2025\Experiment"

import re, gc  # you already import re above; just make sure it's present

# --- movement normalization helpers (position-agnostic move codes) ---
def _movement_signature(key: str) -> str:
    # From keys like '1_up_openhand_slow_3sec' -> 'openhand_slow_3sec'
    m = re.match(r'^\d+_(up|side|down)_(.+)$', key)
    return m.group(2) if m else key

# Canonical per-movement codes (independent of up/side/down)
MOVEMENT_CODES = {
    'openhand_slow_3sec': 1,
    'openhand_fast_1sec': 2,

    'closetofist_allfingerstogether_slow_3sec': 3,
    'closetofist_allfingerstogether_fast_1sec': 4,

    'closetofist_allfingerstogether_normalforce_3sec': 5,
    'closetofist_allfingerstogether_3sec_normalforce': 5, #this is duplicated why
    'closetofist_allfingerstogether_3sec_maxforce': 6,

    'open_fourfingers_together_3sec': 7,
    'close_fourfingers_together_3sec': 8,

    'open_onlythumb_3sec': 9,
    'close_onlythumb_3sec': 10,

    'wrist_palmarflexion_maxforce_3sec': 11,
    'wrist_palmarflexion_normalforce_3sec': 12,
    'wrist_dorsiflexion_normalforce_3sec': 13,
    'wrist_dorsiflexion_maxforce_3sec': 14,

    'grasp_cup_3sec': 15,
    'grasp_donut_3sec': 16,
    'grasping_pinching_pen_allfingers_3sec': 17,
    'grasping_pinching_pen_2fingers_3sec': 17,

    'close_pinky_3sec': 18,
    'close_ring_3sec': 19,
    'close_middle_3sec': 20,
    'close_index_3sec': 21,
    'close_thumb_3sec': 22,

    'open_pinky_3sec': 23,
    'open_ring_3sec': 24,
    'open_middle_3sec': 25,
    'open_index_3sec': 26,
    'open_thumb_3sec': 27,
}

def normalize_movement_codes(MOVEMENTS: dict) -> dict:
    """Return a new dict where 'code' encodes only movement (not position)."""
    out = {}
    for k, v in MOVEMENTS.items():
        sig = _movement_signature(k)
        canonical = MOVEMENT_CODES.get(sig)
        new_code = canonical if canonical is not None else v.get("code", None)
        out[k] = {**v, "code": new_code}
    return out


# ----------------------------- Codes -----------------------------
PHASE = {"cue":1, "prep":2, "move":3, "return":4, "iti":5}
ARM_CODES = {"Left":1, "Right":2}
BASELINE_NAMES = {1: "Palm or fist up", 2: "Palm or fist side", 3: "Palm or fist down"}

# ----------------------------- MOVEMENTS (imported) -----------------------------
try:
    from movement_shared import MOVEMENTS
except ImportError:
    try:
        from code_experiments_fall_2025.MOVEMENTS_shared import MOVEMENTS
    except ImportError as e:
        raise RuntimeError(
            "Could not import MOVEMENTS. Ensure movement_shared.py "
            "or MOVEMENTS_shared.py is in the same directory and defines MOVEMENTS."
        ) from e

# >>> NEW: normalize so codes are position-agnostic <<<
MOVEMENTS = normalize_movement_codes(MOVEMENTS)


# --- helpers for labels/keys ---
_strip_bl = re.compile(r"\s*\((?:up|side|down)\)\s*$", re.IGNORECASE)
def strip_baseline_suffix(lbl: str) -> str:
    return _strip_bl.sub("", lbl)

def movement_root(key_or_file: str) -> str:
    return re.sub(r"^(?:1_up_|2_side_|3_down_)", "", key_or_file)

# ----------------------------- Markers -----------------------------
def make_marker(phase, arm, base, move):
    # phase*1000 + arm*100 + base*10 + move
    return phase*10000 + arm*1000 + base*100 + move

def push_marker(outlet, arm, phase, base, move):
    v = make_marker(PHASE[phase], ARM_CODES[arm], base, move)
    outlet.push_sample([v], timestamp=local_clock())
    trigger.setData(make_trigger(base, move)) 
    return v

def make_trigger(base, move):
    # phase*1000 + arm*100 + base*10 + move
    return move*10 + base


# ----------------------------- Resting-state (optional) -----------------------------
REST_CODES = {"eyes_open": 9701, "eyes_closed": 9702}

def _timed_screen(win, draw_callables, seconds):
    clk = core.Clock()
    while clk.getTime() < float(seconds):
        if 'escape' in event.getKeys(['escape']):
            core.quit()
        for d in draw_callables:
            d.draw()
        win.flip()


def record_resting_state(win, outlet, event_log, label_stim, fix_stim, psycho_ver,
                         subject_id, eeg_fs, emg_fs,
                         do_open=True, open_sec=60.0,
                         do_closed=True, closed_sec=60.0):
    """
    Optional resting-state at the very beginning:
      - eyes open (fixation)
      - eyes closed
    Each segment runs only if enabled and duration > 0.
    """
    # --- Eyes OPEN ---
    if do_open and open_sec > 0:
        label_stim.text = "Resting — eyes OPEN (fixate)"
        t_start = local_clock()
        trigger.setData(1)
        outlet.push_sample([REST_CODES["eyes_open"]])
        _timed_screen(win, [fix_stim, label_stim], float(open_sec))
        t_end = local_clock()
        event_log.append({
            "phase": "rest_open",
            "lsl_t_start": t_start,
            "lsl_t_end": t_end,
            "duration_s": t_end - t_start,
            "trigger": REST_CODES["eyes_open"],
            "subject_id": subject_id,
            "block": 0,
            "rep": 1,
            "arm": None,
            "base_code": None,
            "move_code": None,
            "movement_key": None,
            "file": None,
            "psychopy_version": psycho_ver,
            "eeg_fs": eeg_fs,
            "emg_fs": emg_fs,
        })

    # --- Eyes CLOSED ---
    if do_closed and closed_sec > 0:
        closed_label = visual.TextStim(win, text="Resting — eyes CLOSED", color="white", height=0.035, pos=(0, -0.45))
        t_start = local_clock()
        trigger.setData(2)
        outlet.push_sample([REST_CODES["eyes_closed"]])
        _timed_screen(win, [closed_label], float(closed_sec))
        t_end = local_clock()
        event_log.append({
            "phase": "rest_closed",
            "lsl_t_start": t_start,
            "lsl_t_end": t_end,
            "duration_s": t_end - t_start,
            "trigger": REST_CODES["eyes_closed"],
            "subject_id": subject_id,
            "block": 0,
            "rep": 1,
            "arm": None,
            "base_code": None,
            "move_code": None,
            "movement_key": None,
            "file": None,
            "psychopy_version": psycho_ver,
            "eeg_fs": eeg_fs,
            "emg_fs": emg_fs,
        })

# ----------------------------- GUI (baseline-first, checkboxes) -----------------------------
def setup_gui():
    # -1) Subject & acquisition params
    dS = gui.Dlg(title="Participant / Acquisition")
    dS.addField("Subject ID", "sub-001")
    dS.addField("EEG sampling rate (Hz)", 1000)
    dS.addField("EMG sampling rate (Hz)", 2000)
    okS = dS.show()
    if not dS.OK: core.quit()
    subj_id = str(okS[0]).strip()
    eeg_fs  = float(okS[1])
    emg_fs  = float(okS[2])

    # 0) Resting-state options + Baseline
    d0 = gui.Dlg(title="Experiment Setup — Start Options")
    d0.addText("Resting-state (optional) — runs at the very beginning if enabled:")
    d0.addField("Include eyes OPEN (fixate)?", choices=["Yes", "No"], initial="Yes")
    d0.addField("Eyes OPEN duration (s)", 60.0)
    d0.addField("Include eyes CLOSED?", choices=["Yes", "No"], initial="Yes")
    d0.addField("Eyes CLOSED duration (s)", 60.0)

    d0.addText("")  # spacer
    d0.addText("Choose the baseline orientation:")
    d0.addField("Baseline position",
                choices=[BASELINE_NAMES[1], BASELINE_NAMES[2], BASELINE_NAMES[3]],
                initial=BASELINE_NAMES[2])
    ok0 = d0.show()
    if not d0.OK: core.quit()

    # parse resting-state options
    rest_open   = (ok0[0] == "Yes")
    rest_open_s = float(ok0[1])
    rest_closed = (ok0[2] == "Yes")
    rest_closed_s= float(ok0[3])

    # parse baseline
    base_choice = ok0[4]
    rev_map = {v: k for k, v in BASELINE_NAMES.items()}
    chosen_baseline = rev_map[base_choice]  # 1/2/3

    # 1) Movements (filtered) in two checkbox pages
    avail = [(k, v) for k, v in MOVEMENTS.items()
             if int(v.get("baseline_code", 0)) == int(chosen_baseline)]
    if not avail:
        d = gui.Dlg(title="No videos")
        d.addText(f"No movement videos for {BASELINE_NAMES[chosen_baseline]} (code={chosen_baseline}).")
        d.show(); core.quit()

    avail.sort(key=lambda kv: strip_baseline_suffix(kv[1]["label"]).lower())
    n = len(avail); mid = n // 2 if n > 1 else n

    def movement_page(page_items, title, defaults_yes_budget, offset):
        fields = OrderedDict()
        label_to_key = {}
        for i, (k, v) in enumerate(page_items):
            label = strip_baseline_suffix(v["label"])
            label_to_key[label] = k
            default = (offset + i) < defaults_yes_budget
            fields[label] = default
        dlg = gui.DlgFromDict(dictionary=fields, title=title, order=list(fields.keys()))
        if not dlg.OK: core.quit()
        return {label_to_key[label]: bool(val) for label, val in fields.items()}

    selections = {}
    if mid > 0:
        selections.update(movement_page(avail[:mid],
                           f"Movements (page 1/2) — {BASELINE_NAMES[chosen_baseline]}",
                           defaults_yes_budget=6, offset=0))
    if mid < n:
        selections.update(movement_page(avail[mid:],
                           f"Movements (page 2/2) — {BASELINE_NAMES[chosen_baseline]}",
                           defaults_yes_budget=6, offset=mid))

    if not any(selections.values()):
        d = gui.Dlg(title="Nothing selected")
        d.addText("No movements were selected.")
        d.show(); core.quit()

    # Arms (checkboxes)
    arms_dict = OrderedDict([("Left arm", True), ("Right arm", True)])
    d_arms = gui.DlgFromDict(dictionary=arms_dict, title="Experiment Setup — Arms",
                             order=list(arms_dict.keys()))
    if not d_arms.OK: core.quit()
    arms = []
    if arms_dict["Left arm"]: arms.append("Left")
    if arms_dict["Right arm"]: arms.append("Right")
    if not arms:
        d = gui.Dlg(title="No arms"); d.addText("No arms selected."); d.show(); core.quit()

    # 2) Timing + design
    d2 = gui.Dlg(title="Experiment Setup — Timing and Design")
    d2.addText("Timing (seconds)")
    d2.addField("Cue dur", 3.0)
    d2.addField("Prep countdown", 3.0)
    d2.addField("Perform dur", 3.0)
    d2.addField("Return dur", 2.0)
    d2.addField("ITI", 2.0)
    d2.addField("Fix before cue", 1.0)
    d2.addField("Countdown before first cue", 0)

    d2.addText("Design")
    d2.addField("# reps per movement", 6)
    d2.addField("Order", choices=["Random", "Ordered"], initial="Random")
    d2.addField("Inter-block fix", 5.0)
    d2.addField("Test LSL pings?", choices=["Yes", "No"], initial="Yes")
    d2.addField("Fullscreen?", choices=["Yes", "No"], initial="Yes")
    ok2 = d2.show()
    if not d2.OK: core.quit()

    i = 0
    cue = float(ok2[i]); prep = float(ok2[i+1]); perf = float(ok2[i+2]); ret = float(ok2[i+3])
    iti = float(ok2[i+4]); fix = float(ok2[i+5]); cdown = float(ok2[i+6]); i += 7
    reps = int(ok2[i]); i += 1
    order = ok2[i]; i += 1
    ibfix = float(ok2[i]); i += 1
    test = (ok2[i] == "Yes" or ok2[i] == 0); i += 1
    fs   = (ok2[i] == "Yes" or ok2[i] == 0)

    return dict(
        subject_id=subj_id, eeg_fs=eeg_fs, emg_fs=emg_fs,
        baseline_code=chosen_baseline,
        incl=selections, arms=arms,
        cue=cue, prep=prep, perf=perf, ret=ret, iti=iti, fix=fix, cdown=cdown,
        reps=reps, order=order, ibfix=ibfix,
        test=test, fs=fs,
        # NEW resting-state config
        rest_open=rest_open,
        rest_open_sec=rest_open_s,
        rest_closed=rest_closed,
        rest_closed_sec=rest_closed_s,
    )

# ----------------------------- Media resolution -----------------------------
def arm_candidates(basefile, arm):
    s, e = os.path.splitext(basefile)
    a = arm.lower()
    # try arm-suffixed then generic; try common extensions if needed
    bases = [f"{s}_{a}", s]
    exts = [e] if e else []
    for ext in [".mp4", ".mov", ".MP4", ".MOV"]:
        if ext not in exts: exts.append(ext)
    return [b + ext for b in bases for ext in exts]

def resolve_media_path(move_key, arm):
    basefile = MOVEMENTS[move_key]["file"]
    for fname in arm_candidates(basefile, arm):
        p = os.path.join(MEDIA_DIR, fname)
        if os.path.exists(p):
            return p
    # If not found, return None (we’ll show a label instead of a video)
    return None

# ----------------------------- Playback (robust, legacy MovieStim) -----------------------------
def play_movie_robust(win, path, overlay_text="", dur=None):
    """
    Create a MovieStim (legacy), play it from start, and stop when:
      - movie finishes (status), OR
      - last frame reached / frames stall, OR
      - elapsed time >= dur (if dur specified), else duration + margin.
    """
    # If no path (missing media), show text for requested duration
    if not path or not os.path.exists(path):
        msg = visual.TextStim(win, text=overlay_text or "Missing video", color="black", height=0.05, pos=(0, -0.45))
        clk = core.Clock()
        while dur is None or clk.getTime() < float(dur):
            if 'escape' in event.getKeys(['escape']): core.quit()
            msg.draw(); win.flip()
        return

    # Create legacy MovieStim (your build)
    try:
        stim = visual.MovieStim(win, path, loop=False)
    except Exception as e:
        # fallback: show label if creation fails
        msg = visual.TextStim(win, text=f"Video error:\n{os.path.basename(path)}", color="black", height=0.05)
        clk = core.Clock()
        while dur is None or clk.getTime() < float(dur):
            if 'escape' in event.getKeys(['escape']): core.quit()
            msg.draw(); win.flip()
        return

    # Optional overlay label (movement/arm)
    overlay = visual.TextStim(win, text=overlay_text, color="black", height=0.04, pos=(0, -0.45)) if overlay_text else None

    # Try to read metadata (may not exist in legacy builds)
    fps = n_frames = duration = None
    try: fps = stim.getMovieFrameRate()
    except: pass
    try: n_frames = stim.nFrames
    except: pass
    try: duration = stim.duration
    except: pass
    if duration is None and fps and n_frames:
        duration = float(n_frames) / float(fps)

    # Start playback
    try: stim.play()
    except: pass

    clk = core.Clock()
    last_frame = -999
    stale_time = 0.0
    margin = 0.3  # extra time past duration if we rely on duration

    # If user passed a fixed dur, cap by dur; otherwise play full clip (auto-detect)
    cap = float(dur) if dur is not None else (None if duration is None else duration + margin)

    while True:
        if 'escape' in event.getKeys(['escape']): core.quit()

        stim.draw()
        if overlay: overlay.draw()
        win.flip()

        # A) declared finished
        try:
            if stim.status == visual.FINISHED:
                break
        except: pass

        # B) last frame / frames stall
        try:
            fi = stim.frameIndex
            if n_frames is not None and fi >= (n_frames - 1):
                break
            # crude stall detect
            # (not all builds expose frameIndex reliably)
        except: pass

        # C) cap by time
        if cap is not None and clk.getTime() >= cap:
            break

        # safety
        if clk.getTime() > 300:
            break

    try: stim.stop()
    except: pass
    stim = None
    gc.collect()
    core.wait(0.05)  # brief settle

# ----------------------------- Countdown -----------------------------
def show_countdown(win, secs, txt_stim):
    if secs < 1: return
    for t in range(int(secs), 0, -1):
        if 'escape' in event.getKeys(['escape']): core.quit()
        txt_stim.text = str(t); txt_stim.draw(); win.flip(); core.wait(1.0)

# ----------------------------- Main -----------------------------
def main():
    # LSL outlet once
    info = StreamInfo(name='stimulus_stream', type='Markers', channel_count=1,
                      channel_format='int32', source_id='stimulus_stream_001')
    exp = info.desc().append_child("experiment")
    exp.append_child_value("task", "Upper-limb both arms")
    exp.append_child_value("version", "7.2 (event CSV with triggers)")
    outlet = StreamOutlet(info)

    # Config
    cfg = setup_gui()

    # Single window for the whole run; skip frame-rate measurement
    win = visual.Window(fullscr=cfg["fs"], units='height', color="black", checkTiming=False)

    # UI stims
    fix = visual.TextStim(win, text="+", color="white", height=0.05)
    ready = visual.TextStim(win, text="Start your LabRecorder now.\n\nRecording will begin shortly.", color="white", height=0.035)
    endt = visual.TextStim(win, text="Finished! Thank you.", color="white", height=0.035)
    countdown = visual.TextStim(win, text="", height=0.08, color="white")
    label = visual.TextStim(win, text="", height=0.04, color="white", pos=(0, -0.45))
    retxt = visual.TextStim(win, text="Return to Baseline", height=0.04, color="white", pos=(0, -0.45))

    # --- event log (per-event rows) ---
    event_log = []
    psycho_ver = psychopy.__version__
    subject_id = cfg["subject_id"]
    eeg_fs = cfg["eeg_fs"]
    emg_fs = cfg["emg_fs"]

    # Build blocks list
    moves = [k for k, v in cfg["incl"].items() if v]
    if not moves or not cfg["arms"]:
        visual.TextStim(win, text="No arms/movements selected", color="black").draw()
        win.flip(); core.wait(2); win.close(); core.quit()

    blocks = [(a, m) for a in cfg["arms"] for m in moves]
    if cfg["order"].lower().startswith("rand"): random.shuffle(blocks)

    # Optional LSL test pings
    if cfg["test"]:
        for _ in range(5):
            outlet.push_sample([9999]); core.wait(0.5)

    # Ready screen
    ready.draw(); win.flip(); outlet.push_sample([8888]); core.wait(1.5)

    # Pre-run global countdown
    if cfg["cdown"] > 0: show_countdown(win, cfg["cdown"], countdown)

    # Optional resting-state at experiment start
    if cfg["rest_open"] or cfg["rest_closed"]:
        record_resting_state(
            win=win, outlet=outlet, event_log=event_log,
            label_stim=label, fix_stim=fix,
            psycho_ver=psycho_ver, subject_id=subject_id,
            eeg_fs=eeg_fs, emg_fs=emg_fs,
            do_open=cfg["rest_open"], open_sec=cfg["rest_open_sec"],
            do_closed=cfg["rest_closed"], closed_sec=cfg["rest_closed_sec"]
        )

    # Run blocks
    for bi, (arm, mkey) in enumerate(blocks):
        move_code = MOVEMENTS[mkey]["code"]
        base_code = MOVEMENTS[mkey]["baseline_code"]

        # Resolve best file for this arm (tries *_left/_right then generic)
        media_path = resolve_media_path(mkey, arm)
        nice_label = f"{arm.upper()} — {strip_baseline_suffix(MOVEMENTS[mkey]['label'])}"

        for r in range(cfg["reps"]):
            event.clearEvents()

            # Fixation before cue
            if cfg["fix"] > 0:
                label.text = nice_label
                fix.draw(); label.draw(); win.flip(); core.wait(cfg["fix"])

            # CUE
            t_start = local_clock()
            trig = push_marker(outlet, arm, "cue", base_code, move_code)
            play_movie_robust(win, media_path, overlay_text=nice_label, dur=cfg["cue"])  # or dur=None
            t_end = local_clock()
            event_log.append({
                "phase": "cue",
                "lsl_t_start": t_start,
                "lsl_t_end": t_end,
                "duration_s": t_end - t_start,
                "trigger": trig,
                "subject_id": subject_id,
                "block": bi + 1,
                "rep": r + 1,
                "arm": arm,
                "base_code": base_code,
                "move_code": move_code,
                "movement_key": mkey,
                "file": os.path.basename(media_path) if media_path else None,
                "psychopy_version": psycho_ver,
                "eeg_fs": eeg_fs,
                "emg_fs": emg_fs,
            })

            # PREP
            t_start = local_clock()
            trig = push_marker(outlet, arm, "prep", base_code, move_code)
            show_countdown(win, cfg["prep"], countdown)
            t_end = local_clock()
            event_log.append({
                "phase": "prep",
                "lsl_t_start": t_start,
                "lsl_t_end": t_end,
                "duration_s": t_end - t_start,
                "trigger": trig,
                "subject_id": subject_id,
                "block": bi + 1,
                "rep": r + 1,
                "arm": arm,
                "base_code": base_code,
                "move_code": move_code,
                "movement_key": mkey,
                "file": os.path.basename(media_path) if media_path else None,
                "psychopy_version": psycho_ver,
                "eeg_fs": eeg_fs,
                "emg_fs": emg_fs,
            })

            # MOVE (full video recommended; set dur=cfg["perf"] for fixed window)
            t_start = local_clock()
            trig = push_marker(outlet, arm, "move", base_code, move_code)
            play_movie_robust(win, media_path, overlay_text=nice_label, dur=None)
            t_end = local_clock()
            event_log.append({
                "phase": "move",
                "lsl_t_start": t_start,
                "lsl_t_end": t_end,
                "duration_s": t_end - t_start,
                "trigger": trig,
                "subject_id": subject_id,
                "block": bi + 1,
                "rep": r + 1,
                "arm": arm,
                "base_code": base_code,
                "move_code": move_code,
                "movement_key": mkey,
                "file": os.path.basename(media_path) if media_path else None,
                "psychopy_version": psycho_ver,
                "eeg_fs": eeg_fs,
                "emg_fs": emg_fs,
            })

            # RETURN (text only)
            if cfg["ret"] > 0:
                t_start = local_clock()
                trig = push_marker(outlet, arm, "return", base_code, move_code)
                fix.draw(); retxt.draw(); win.flip(); core.wait(cfg["ret"])
                t_end = local_clock()
                event_log.append({
                    "phase": "return",
                    "lsl_t_start": t_start,
                    "lsl_t_end": t_end,
                    "duration_s": t_end - t_start,
                    "trigger": trig,
                    "subject_id": subject_id,
                    "block": bi + 1,
                    "rep": r + 1,
                    "arm": arm,
                    "base_code": base_code,
                    "move_code": move_code,
                    "movement_key": mkey,
                    "file": os.path.basename(media_path) if media_path else None,
                    "psychopy_version": psycho_ver,
                    "eeg_fs": eeg_fs,
                    "emg_fs": emg_fs,
                })

            # ITI (not requested for the CSV, but still send marker if desired)
            if cfg["iti"] > 0:
                push_marker(outlet, arm, "iti", base_code, move_code)
                fix.draw(); win.flip(); core.wait(cfg["iti"])

        # Inter-block fixation
        if bi < len(blocks) - 1 and cfg["ibfix"] > 0:
            fix.draw(); win.flip(); core.wait(cfg["ibfix"])

    # --- save event log to CSV ---
    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_name = f"stim_log_{time.strftime('%Y%m%d_%H%M%S')}.csv"
    log_path = os.path.join(log_dir, log_name)

    fieldnames = [
        "phase","lsl_t_start","lsl_t_end","duration_s","trigger",
        "subject_id","block","rep","arm","base_code","move_code",
        "movement_key","file","psychopy_version","eeg_fs","emg_fs"
    ]

    with open(log_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(event_log)

    # brief on-screen confirmation
    msg = visual.TextStim(win, text=f"Run summary saved:\n{log_path}\n\nPress any key to exit.",
                          color="black", height=0.035)
    msg.draw(); win.flip(); event.waitKeys()

    # End
    endt.draw(); win.flip(); outlet.push_sample([8899]); core.wait(2)
    win.close(); core.quit()

if __name__ == "__main__":
    main()
