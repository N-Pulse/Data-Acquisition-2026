# test_video_play.py
from psychopy import visual, core, event, prefs
import os

# ---- settings ----
prefs.general['moviesLib'] = ['ffpyplayer', 'moviepy']  # try ffpyplayer first
MEDIA_DIR = "Experiment/videos_measures_720p"            # adjust if needed
TEST_VIDEO = "1_up_open_index_3sec.MOV"                 # change to any file you have
VIDEO_PATH = os.path.join(MEDIA_DIR, TEST_VIDEO)

# ---- check path ----
if not os.path.exists(VIDEO_PATH):
    print(f"❌ Video not found at {VIDEO_PATH}")
    core.quit()

print(f"✅ Testing video playback for: {VIDEO_PATH}")

# ---- open window ----
win = visual.Window(fullscr=False, color="white", units="height")

# ---- try to load the video ----
try:
    stim = visual.MovieStim(win, filename=VIDEO_PATH, loop=False, noAudio=True)
    print("✅ MovieStim3 successfully created")
except Exception as e:
    print(f"❌ Could not load video: {e}")
    core.quit()

# ---- play the video ----
clock = core.Clock()
while stim.status != visual.FINISHED:
    if 'escape' in event.getKeys(['escape']):
        break
    stim.draw()
    win.flip()

# ---- clean up ----
print(f"✅ Video played for {clock.getTime():.1f} seconds")
win.close()
core.quit()
