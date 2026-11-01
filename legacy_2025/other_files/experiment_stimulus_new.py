# -*- coding: utf-8 -*-
from psychopy import core, visual, event, gui
from pylsl import StreamInfo, StreamOutlet, local_clock
import os, random

MEDIA_DIR = "Experiment"

# ----------------------------- Codes -----------------------------
PHASE = {"cue":1, "prep":2, "move":3, "return":4, "iti":5}
ARM_CODES = {"Left":1, "Right":2}
BASELINE_CODES = {"Palm or fist up":1, "Palm or fist side":2, "Palm or fist down":3}


# For each baseline, override the base file used for existing movement keys.
# If a movement isn't listed here for a given baseline, it will fall back to MOVEMENTS[k]["base"].
MOVIE_OVERRIDES = {
    "down": {
        "open_hand_slow": "down_openhand_slow.MOV",
        "open_hand_fast": "down_openhand_fast.MOV",
        "close_fist_all_together_slow": "down_closetofist_allfingerstogether_slow.MOV",
        "close_fist_all_together_fast": "down_closetofist_allfingerstogether_fast.MOV",
        "close_fist_all_together_max": "down_closetofist_allfingerstogether_maximalforce.MOV",
        "only_thumb": "down_only_thumb.MOV",
        # Choose where to map "grasp_donut" — here we align it with grasp_cup (adjust if you prefer grasp_ball)
        "grasp_cup": "down_grasp_donut.MOV",
    },
    "side": {
        "close_fist_all_together_slow": "side_closetofist_allfingerstogether_slow.MOV",
        "four_fingers_together": "side_fourfingersonly.MOV",
        # Filenames provided as "palmiflection" — using as-is
        "wrist_palmarflexion_max": "side_palmiflection_maximalforce.MOV",
        "wrist_palmarflexion_normal": "side_palmiflection_normalforce.MOV",
    },
    "up": {
        "open_hand_slow": "up_open_hand_slow.MOV",
        "open_hand_fast": "up_open_hand_fast.MOV",
        "close_fist_all_together_max": "up_closetofist_allfingerstogether_maximalforce.MOV",
        "wrist_dorsiflexion_normal": "up_dorsiflexion_normalforce.MOV",
        # Provided as "palmaflexion" — using as-is
        "wrist_palmarflexion_max": "up_palmaflexion_maximalforce.MOV",
    },
}


MOVEMENTS = {
    "open_hand_slow": {"code":1, "base":"open_hand_slow.mp4", "label":"Open hand (slow)"},
    "open_hand_fast": {"code":2, "base":"open_hand_fast.mp4", "label":"Open hand (fast)"},
    "close_fist_all_together_slow": {"code":3, "base":"close_fist_all_together_slow.mp4", "label":"Close to fist – slow"},
    "close_fist_all_together_fast": {"code":4, "base":"close_fist_all_together_fast.mp4", "label":"Close to fist – fast"},
    "close_fist_all_together_max": {"code":5, "base":"close_fist_all_together_max.mp4", "label":"Close to fist – max"},
    "close_fist_all_together_normal": {"code":6, "base":"close_fist_all_together_normal.mp4", "label":"Close to fist – normal"},
    "four_fingers_together": {"code":7, "base":"four_fingers_together.mp4", "label":"Four fingers together"},
    "only_thumb": {"code":8, "base":"only_thumb.mp4", "label":"Only thumb"},
    "grasp_cup": {"code":9, "base":"grasp_cup.mp4", "label":"Grasp cup"},
    "pinch_pen": {"code":10, "base":"pinch_pen.mp4", "label":"Pinch pen"},
    "wrist_palmarflexion_max": {"code":11, "base":"wrist_palmarflexion_max.mp4", "label":"Wrist palmarflexion – max"},
    "wrist_palmarflexion_normal": {"code":12, "base":"wrist_palmarflexion_normal.mp4", "label":"Wrist palmarflexion – normal"},
    "wrist_dorsiflexion_max": {"code":13, "base":"wrist_dorsiflexion_max.mp4", "label":"Wrist dorsiflexion – max"},
    "wrist_dorsiflexion_normal": {"code":14, "base":"wrist_dorsiflexion_normal.mp4", "label":"Wrist dorsiflexion – normal"},
    "supination": {"code":15, "base":"supination.mp4", "label":"Supination"},
    "pronation": {"code":16, "base":"pronation.mp4", "label":"Pronation"},
    "grasp_ball": {"code":17, "base":"grasp_ball.mp4", "label":"Grasp ball"},
}

# Marker generator: 4 digits, arm now second
def make_marker(phase, arm, base, move):
    return phase*10000 + arm*1000 + base*100 + move

def arm_candidates(basefile, arm):
    s,e=os.path.splitext(basefile); a=arm.lower()
    return [f"{s}_{a}{e}", basefile]

def safe_wait(t):
    c=core.Clock()
    while c.getTime()<t:
        if 'escape' in event.getKeys(['escape']): core.quit()
        core.wait(0.01)

def load_movie_or_text(win, path, label):
    try:
        if path and os.path.exists(path):
            return visual.MovieStim3(win,filename=path,loop=True,noAudio=True)
    except Exception as e:
        print(f"[WARN] Can't load {path}: {e}")
    return visual.TextStim(win,text=label,color="black",height=0.08)

# ----------------------------- GUI -----------------------------
def setup_gui():
    # ---------- 1️⃣ MOVEMENTS + ARMS ----------
    d1 = gui.Dlg(title="Experiment Setup — Movements and Arms")
    d1.addText("Select movements:")
    defaults = {
        k: ("Yes" if k in ["open_hand_slow", "open_hand_fast", "supination", "pronation"] else "No")
        for k in MOVEMENTS
    }
    for k in MOVEMENTS:
        d1.addField(MOVEMENTS[k]["label"], choices=["Yes", "No"], initial=defaults[k])

    d1.addText("Arms")
    d1.addField("Left arm?", choices=["Yes", "No"], initial="Yes")
    d1.addField("Right arm?", choices=["Yes", "No"], initial="Yes")

    ok1 = d1.show()
    if not d1.OK:
        core.quit()

    # Parse first dialog
    i = 0
    incl = {k: (ok1[i + j] == "Yes") for j, k in enumerate(MOVEMENTS)}
    i += len(MOVEMENTS)
    left = (ok1[i] == "Yes")
    i += 1
    right = (ok1[i] == "Yes")

    arms = []
    if left:
        arms.append("Left")
    if right:
        arms.append("Right")

    # ---------- 2️⃣ TIMING + DESIGN ----------
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
    d2.addField("Baseline position", choices=list(BASELINE_CODES.keys()), initial="Palm or fist side")
    d2.addField("Test LSL pings?", choices=["Yes", "No"], initial="Yes")
    d2.addField("Fullscreen?", choices=["Yes", "No"], initial="Yes")

    ok2 = d2.show()
    if not d2.OK:
        core.quit()

    # Parse second dialog
    i = 0
    cue = float(ok2[i]); prep = float(ok2[i+1]); perf = float(ok2[i+2]); ret = float(ok2[i+3])
    iti = float(ok2[i+4]); fix = float(ok2[i+5]); cdown = float(ok2[i+6]); i += 7
    reps = int(ok2[i]); i += 1
    order = ok2[i]; i += 1
    # ...
    ibfix = float(ok2[i]); i += 1
    baseline_name = ok2[i]                 # e.g., "Palm or fist side"
    baseline = BASELINE_CODES[baseline_name]
    i += 1
    test = (ok2[i] == "Yes"); i += 1
    fs = (ok2[i] == "Yes")

    # ---------- Return config ----------
    return dict(
        incl=incl, arms=arms,
        cue=cue, prep=prep, perf=perf, ret=ret, iti=iti, fix=fix, cdown=cdown,
        reps=reps, order=order, ibfix=ibfix,
        baseline=baseline,                      # int code (unchanged usage)
        baseline_name=baseline_name,            # string for filename selection
        test=test, fs=fs
    )


# def setup_gui():
#     d=gui.Dlg(title="Experiment Setup (Both arms)")
#     d.addText("Select movements:")
#     defaults={k:("Yes" if k in ["open_hand_slow","open_hand_fast","supination","pronation"] else "No") for k in MOVEMENTS}
#     for k in MOVEMENTS: d.addField(MOVEMENTS[k]["label"],choices=["Yes","No"],initial=defaults[k])
#     d.addText("Arms"); d.addField("Left arm?",choices=["Yes","No"],initial="Yes"); d.addField("Right arm?",choices=["Yes","No"],initial="Yes")
#     d.addText("Timing")
#     d.addField("Cue dur (s)",3.0); d.addField("Prep countdown (s)",3.0); d.addField("Perform dur (s)",3.0)
#     d.addField("Return dur (s)",2.0); d.addField("ITI (s)",2.0); d.addField("Fix before cue (s)",1.0)
#     d.addField("Countdown before first cue (s)",0)
#     d.addText("Design")
#     d.addField("# reps per movement",6); d.addField("Order",choices=["Random","Ordered"],initial="Random")
#     d.addField("Inter-block fix (s)",5.0)
#     d.addField("Baseline position",choices=list(BASELINE_CODES.keys()),initial="Palm side")
#     d.addField("Test LSL pings?",choices=["Yes","No"],initial="Yes")
#     d.addField("Fullscreen?",choices=["Yes","No"],initial="Yes")
#     ok=d.show()
#     if not d.OK: core.quit()

#     i=0
#     incl={k:(ok[i+j]=="Yes") for j,k in enumerate(MOVEMENTS)}; i+=len(MOVEMENTS)
#     left=(ok[i]=="Yes"); i+=1; right=(ok[i]=="Yes"); i+=1
#     cue=float(ok[i]); prep=float(ok[i+1]); perf=float(ok[i+2]); ret=float(ok[i+3]); iti=float(ok[i+4]); fix=float(ok[i+5]); cdown=float(ok[i+6]); i+=7
#     reps=int(ok[i]); i+=1; order=ok[i]; i+=1; ibfix=float(ok[i]); i+=1; baseline=BASELINE_CODES[ok[i]]; i+=1
#     test=(ok[i]=="Yes"); i+=1; fs=(ok[i]=="Yes")
#     arms=[]; 
#     if left: arms.append("Left"); 
#     if right: arms.append("Right")
#     return dict(incl=incl,arms=arms,cue=cue,prep=prep,perf=perf,ret=ret,iti=iti,fix=fix,cdown=cdown,
#                 reps=reps,order=order,ibfix=ibfix,baseline=baseline,test=test,fs=fs)

# ----------------------------- Helpers -----------------------------
def play_stim(win,stim,dur):
    clk=core.Clock(); 
    try: stim.seek(0.0)
    except: pass
    while clk.getTime()<dur:
        if 'escape' in event.getKeys(['escape']): core.quit()
        stim.draw(); win.flip()
    try: stim.pause()
    except: pass

def show_countdown(win,secs,txt):
    if secs<1: return
    for t in range(int(secs),0,-1):
        txt.text=str(t); txt.draw(); win.flip(); safe_wait(1.0)

def push_marker(outlet,arm,phase,base,move):
    v=make_marker(PHASE[phase],ARM_CODES[arm],base,move)
    outlet.push_sample([v],timestamp=local_clock()); return v

# def load_arm_stim(win,move,arm):
#     for f in arm_candidates(MOVEMENTS[move]["base"],arm):
#         p=os.path.join(MEDIA_DIR,f)
#         if os.path.exists(p):
#             return load_movie_or_text(win,p,f"{arm.upper()} — {MOVEMENTS[move]['label']}")
#     return load_movie_or_text(win,None,f"{arm.upper()} — {MOVEMENTS[move]['label']}")

def load_arm_stim(win, move, arm, baseline_name):
    # Normalize baseline_name into {"up","side","down"} keys
    bl = baseline_name.lower()
    if "up" in bl:
        bl_key = "up"
    elif "side" in bl:
        bl_key = "side"
    elif "down" in bl:
        bl_key = "down"
    else:
        bl_key = None

    # Pick override basefile if available, else default to MOVEMENTS[move]["base"]
    basefile = MOVEMENTS[move]["base"]
    if bl_key and bl_key in MOVIE_OVERRIDES:
        basefile = MOVIE_OVERRIDES[bl_key].get(move, basefile)

    # Keep your existing arm-specific preference logic
    for f in arm_candidates(basefile, arm):
        p = os.path.join(MEDIA_DIR, f)
        if os.path.exists(p):
            return load_movie_or_text(win, p, f"{arm.upper()} — {MOVEMENTS[move]['label']}")
    return load_movie_or_text(win, None, f"{arm.upper()} — {MOVEMENTS[move]['label']}")


# ----------------------------- Main -----------------------------
def main():
    info=StreamInfo(name='stimulus_stream',type='Markers',channel_count=1,channel_format='int32',source_id='stimulus_stream_001')
    exp=info.desc().append_child("experiment")
    exp.append_child_value("task","Upper-limb both arms"); exp.append_child_value("version","5.0")
    outlet=StreamOutlet(info)
    cfg=setup_gui()

    win=visual.Window(fullscr=cfg["fs"],units='height',color="white")
    fix=visual.TextStim(win,text="+",color="black",height=0.05)
    ready=visual.TextStim(win,text="Start your LabRecorder now.\n\nRecording will begin shortly.",color="black",height=0.035)
    endt=visual.TextStim(win,text="Finished! Thank you.",color="black",height=0.035)
    countdown=visual.TextStim(win,text="",height=0.08,color="black")
    label=visual.TextStim(win,text="",height=0.04,color="black",pos=(0,-0.45))
    retxt=visual.TextStim(win,text="Return to start",height=0.04,color="black",pos=(0,-0.45))

    moves=[k for k,v in cfg["incl"].items() if v]; 
    if not moves or not cfg["arms"]:
        visual.TextStim(win,text="No arms/movements selected",color="black").draw(); win.flip(); safe_wait(2); core.quit()
    blocks=[(a,m) for a in cfg["arms"] for m in moves]
    if cfg["order"].lower().startswith("rand"): random.shuffle(blocks)
    #stimmap={(a,m):load_arm_stim(win,m,a) for a,m in blocks}
    stimmap = {(a, m): load_arm_stim(win, m, a, cfg["baseline_name"]) for a, m in blocks}

    if cfg["test"]:
        for _ in range(5): outlet.push_sample([9999]); safe_wait(0.5)
    ready.draw(); win.flip(); outlet.push_sample([8888]); safe_wait(1.5)

    if cfg["cdown"]>0: show_countdown(win,cfg["cdown"],countdown)
    base=cfg["baseline"]

    for bi,(arm,m) in enumerate(blocks):
        ac=ARM_CODES[arm]; mc=MOVEMENTS[m]["code"]; stim=stimmap[(arm,m)]
        label.text=f"{arm.upper()} — {MOVEMENTS[m]['label']}"
        for r in range(cfg["reps"]):
            if cfg["fix"]>0: fix.draw(); label.draw(); win.flip(); safe_wait(cfg["fix"])
            push_marker(outlet,arm,"cue",base,mc); play_stim(win,stim,cfg["cue"])
            push_marker(outlet,arm,"prep",base,mc); show_countdown(win,cfg["prep"],countdown)
            push_marker(outlet,arm,"move",base,mc); play_stim(win,stim,cfg["perf"])
            if cfg["ret"]>0: push_marker(outlet,arm,"return",base,mc); fix.draw(); retxt.draw(); win.flip(); safe_wait(cfg["ret"])
            if cfg["iti"]>0: push_marker(outlet,arm,"iti",base,mc); fix.draw(); win.flip(); safe_wait(cfg["iti"])
        if bi<len(blocks)-1 and cfg["ibfix"]>0: fix.draw(); win.flip(); safe_wait(cfg["ibfix"])

    win.flip(); endt.draw(); win.flip(); outlet.push_sample([8899]); safe_wait(2); win.close(); core.quit()

if __name__=="__main__": 
    main()
