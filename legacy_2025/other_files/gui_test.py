# test_gui_checkboxes.py
from psychopy import gui, core

BASELINE_NAMES = {1: "Palm or fist up", 2: "Palm or fist side", 3: "Palm or fist down"}

# Minimal sample movements (intentionally include all three baselines)
MOVEMENTS = {
    '1_up_open_index_3sec':   {'label': 'Open index 3 sec (up)',   'baseline_code': 1, 'code': 24},
    '1_up_open_thumb_3sec':   {'label': 'Open thumb 3 sec (up)',   'baseline_code': 1, 'code': 25},
    '2_side_open_index_3sec': {'label': 'Open index 3 sec (side)', 'baseline_code': 2, 'code': 24},
    '2_side_open_thumb_3sec': {'label': 'Open thumb 3 sec (side)', 'baseline_code': 2, 'code': 25},
    '3_down_open_index_3sec': {'label': 'Open index 3 sec (down)', 'baseline_code': 3, 'code': 24},
    '3_down_open_thumb_3sec': {'label': 'Open thumb 3 sec (down)', 'baseline_code': 3, 'code': 25},
}

def main():
    # 1) Baseline choice (string)
    d0 = gui.Dlg(title="Baseline test (checkboxes)")
    d0.addText("Choose baseline:")
    d0.addField("Baseline position",
                choices=[BASELINE_NAMES[1], BASELINE_NAMES[2], BASELINE_NAMES[3]],
                initial=BASELINE_NAMES[2])
    ok0 = d0.show()
    if not d0.OK: core.quit()

    base_choice = ok0[0]
    rev = {v: k for k, v in BASELINE_NAMES.items()}
    chosen_baseline = rev[base_choice]  # 1/2/3 int

    # 2) Filter movements for that baseline
    avail = [(k, v) for k, v in MOVEMENTS.items()
             if int(v.get("baseline_code", 0)) == int(chosen_baseline)]
    if not avail:
        d = gui.Dlg(title="No videos")
        d.addText(f"No movements for baseline_code={chosen_baseline}")
        d.show(); core.quit()

    # 3) Movement selection via CHECKBOXES (DlgFromDict mutates dict in place)
    #    Use movement keys as labels to avoid any return-type ambiguity.
    from collections import OrderedDict
    fields = OrderedDict((k, True) for k, _ in avail)  # default all True so it's obvious
    d1 = gui.DlgFromDict(dictionary=fields,
                         title=f"Select movements — {BASELINE_NAMES[chosen_baseline]}",
                         order=list(fields.keys()))
    if not d1.OK: core.quit()

    selected = [k for k, v in fields.items() if bool(v)]
    if not selected:
        d = gui.Dlg(title="Nothing selected")
        d.addText("No movements were selected.")
        d.show(); core.quit()

    # 4) Arms via CHECKBOXES
    arms_dict = OrderedDict([("Left", True), ("Right", True)])
    d2 = gui.DlgFromDict(dictionary=arms_dict, title="Select arms", order=["Left", "Right"])
    if not d2.OK: core.quit()
    arms = [a for a, on in arms_dict.items() if bool(on)]
    if not arms:
        d = gui.Dlg(title="No arms")
        d.addText("No arms selected.")
        d.show(); core.quit()

    # 5) Show results + print to console
    print("Baseline:", chosen_baseline, BASELINE_NAMES[chosen_baseline])
    print("Movements selected:", selected)
    print("Arms:", arms)

    d = gui.Dlg(title="Results")
    d.addText("Baseline: " + BASELINE_NAMES[chosen_baseline])
    d.addText("Movements:\n- " + "\n- ".join(selected))
    d.addText("Arms: " + ", ".join(arms))
    d.show()

    core.quit()

if __name__ == "__main__":
    main()
