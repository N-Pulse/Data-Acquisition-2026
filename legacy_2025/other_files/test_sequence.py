# play_video_list_legacy_quiet.py
from psychopy import visual, core, event, prefs
import os, sys, gc

# Use stable backends (harmless if not installed)
prefs.general['moviesLib'] = ['ffpyplayer', 'moviepy', 'avbin']

# --------------------------------------------------------------------
# Provide your list of video files, in the order you want:
VIDEOS = [
    r"Experiment/videos_measures_720p/1_up_open_index_3sec.mov",
    r"Experiment/videos_measures_720p/2_side_wrist_dorsiflexion_normalforce_3sec.mov",
    r"Experiment/videos_measures_720p/3_down_open_thumb_3sec.mov",
]
# Or pass paths from command line:
#   python play_video_list_legacy_quiet.py file1.mp4 file2.mov ...
# --------------------------------------------------------------------

if len(sys.argv) > 1:
    VIDEOS = sys.argv[1:]

# Normalize paths and verify existence
videos = []
for p in VIDEOS:
    p = os.path.abspath(p)
    if os.path.exists(p):
        videos.append(p)
    else:
        print(f"❌ Not found: {p}")

if not videos:
    print("No valid video files to play.")
    sys.exit(1)

print("🎬 Will play automatically:")
for i, p in enumerate(videos, 1):
    print(f" {i:2d}. {os.path.basename(p)}")
print(f"Total: {len(videos)}\n")

# Ensure legacy MovieStim exists
if not hasattr(visual, "MovieStim"):
    print("❌ This PsychoPy build has no visual.MovieStim.")
    sys.exit(1)

def play_one(path, idx, total):
    # Disable frame-rate testing with checkTiming=False
    win = visual.Window(
        fullscr=False,
        color="grey",
        units="height",
        checkTiming=False,
    )
    overlay = visual.TextStim(
        win,
        color="white",
        pos=(0, -0.45),
        height=0.04,
        text=f"{idx}/{total} — {os.path.basename(path)}  (Space=skip  Esc=quit)"
    )

    event.clearEvents()
    gc.collect()

    print(f"▶️  {idx}/{total}: {os.path.basename(path)}")

    try:
        stim = visual.MovieStim(win, path, loop=False)
    except Exception as e:
        print("  ❌ load error:", e)
        win.close()
        return

    try:
        stim.play()
    except Exception as e:
        print("  ⚠️ play() failed:", e)
        win.close()
        return

    clk = core.Clock()
    last_frame = -999
    stale_time = 0.0
    while True:
        keys = event.getKeys()
        if 'escape' in keys:
            print("  ⏹ ESC pressed, exiting")
            win.close()
            core.quit()
        if 'space' in keys:
            print("  ⏭ skip")
            break

        stim.draw()
        overlay.draw()
        win.flip()

        # Detect end of playback
        try:
            fi = stim.frameIndex
            if fi == last_frame:
                stale_time += 1.0 / 60.0
            else:
                stale_time = 0.0
                last_frame = fi
            if stale_time > 1.0:
                print(f"  ✅ finished (auto) at {clk.getTime():.2f}s")
                break
        except Exception:
            pass

        if clk.getTime() > 300:
            print("  ⚠️ timeout; skipping")
            break

    try:
        stim.stop()
    except Exception:
        pass
    stim = None
    gc.collect()
    core.wait(0.05)
    win.close()

# --- Play all videos sequentially ---
for i, p in enumerate(videos, 1):
    play_one(p, i, len(videos))

print("\n✅ All videos played.")
core.quit()
