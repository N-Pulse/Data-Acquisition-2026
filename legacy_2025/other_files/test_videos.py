from psychopy import visual, core, event
import os

MEDIA_DIR = "Experiment"
VIDEO_FILE = "down_grasp_donut.MOV"
path = os.path.join(MEDIA_DIR, VIDEO_FILE)

# Use pixel units so resizing is robust with legacy MovieStim
win = visual.Window(size=(1280, 720), units="pix", color="black", fullscr=False)

stim = visual.MovieStim(win, path, loop=False, noAudio=True)
stim.seek(0); stim.play()

# --- Resize to COVER the window (no bars; may crop a little) ---
# Get native video size (in pix). In pixel units this reports the movie's intrinsic size.
native_w, native_h = stim.size
win_w, win_h = win.size

scale_w = win_w / float(native_w)
scale_h = win_h / float(native_h)
scale   = max(scale_w, scale_h)                # cover (use min(...) for contain)

stim.size = (int(native_w * scale), int(native_h * scale))

# Center (default), then play
while stim.status != visual.FINISHED:
    if 'escape' in event.getKeys(['escape']): break
    stim.draw(); win.flip()

stim.pause(); win.close(); core.quit()
