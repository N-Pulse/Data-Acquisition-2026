# movement information for eeg_emg.py

# for each movement :
#     - key : movement string label 
#     - code : unique movement code (used for lsl markers and arduino triggers)
#     - file : name of the video file for movement instruction
#     - label : movement name for display (with spaces)
#     - baseline_code : encoding the hand orientation (used for lsl markers)

MOVEMENTS = {
    '1_up_openhand_slow_3sec': {'code': 1, 'file': '1_up_openhand_slow_3sec.mov', 'label': 'Open hand slow 3 sec (up)', 'baseline_code': 1},
    '1_up_closetofist_allfingerstogether_slow_3sec': {'code': 2, 'file': '1_up_closetofist_allfingerstogether_slow_3sec.mov', 'label': 'Close to fist allfingerstogether slow 3 sec (up)', 'baseline_code': 1},
    '1_up_closetofist_allfingerstogether_3sec_maxforce': {'code': 3, 'file': '1_up_closetofist_allfingerstogether_3sec_maxforce.mov', 'label': 'Close to fist allfingerstogether 3 sec max force (up)', 'baseline_code': 1},
    '1_up_wrist_palmarflexion_normalforce_3sec': {'code': 4, 'file': '1_up_wrist_palmarflexion_normalforce_3sec.mov', 'label': 'Wrist palmarflexion normal force 3 sec (up)', 'baseline_code': 1},
    '1_up_wrist_palmarflexion_maxforce_3sec': {'code': 5, 'file': '1_up_wrist_palmarflexion_maxforce_3sec.mov', 'label': 'Wrist palmarflexion max force 3 sec (up)', 'baseline_code': 1},
    '1_up_close_onlythumb_3sec': {'code': 6, 'file': '1_up_close_onlythumb_3sec.mov', 'label': 'Close only thumb 3 sec (up)', 'baseline_code': 1},
    '1_up_open_onlythumb_3sec': {'code': 7, 'file': '1_up_open_onlythumb_3sec.mov', 'label': 'Open only thumb 3 sec (up)', 'baseline_code': 1},
    '1_up_wrist_dorsiflexion_normalforce_3sec': {'code': 8, 'file': '1_up_wrist_dorsiflexion_normalforce_3sec.mov', 'label': 'Wrist dorsiflexion normal force 3 sec (up)', 'baseline_code': 1},
    '1_up_wrist_dorsiflexion_maxforce_3sec': {'code': 9, 'file': '1_up_wrist_dorsiflexion_maxforce_3sec.mov', 'label': 'Wrist dorsiflexion max force 3 sec (up)', 'baseline_code': 1},
    '1_up_grasp_donut_3sec': {'code': 10, 'file': '1_up_grasp_donut_3sec.mov', 'label': 'Grasp donut 3 sec (up)', 'baseline_code': 1},
    
    '2_side_openhand_slow_3sec': {'code': 1, 'file': '2_side_openhand_slow_3sec.mov', 'label': 'Open hand slow 3 sec (side)', 'baseline_code': 2},
    '2_side_closetofist_allfingerstogether_slow_3sec': {'code': 2, 'file': '2_side_closetofist_allfingerstogether_slow_3sec.mov', 'label': 'Close to fist allfingerstogether slow 3 sec (side)', 'baseline_code': 2},
    '2_side_closetofist_allfingerstogether_maxforce_3sec': {'code': 3, 'file': '2_side_closetofist_allfingerstogether_maxforce_3sec.mov', 'label': 'Close to fist allfingerstogether max force 3 sec (side)', 'baseline_code': 2},
    '2_side_open_onlythumb_3sec': {'code': 7, 'file': '2_side_open_onlythumb_3sec.mov', 'label': 'Open only thumb 3 sec (side)', 'baseline_code': 2},
    '2_side_close_onlythumb_3sec': {'code': 6, 'file': '2_side_close_onlythumb_3sec.mov', 'label': 'Close only thumb 3 sec (side)', 'baseline_code': 2},
    '2_side_wrist_palmarflexion_normalforce_3sec': {'code': 4, 'file': '2_side_wrist_palmarflexion_normalforce_3sec.mov', 'label': 'Wrist palmarflexion normal force 3 sec (side)', 'baseline_code': 2},
    '2_side_wrist_palmarflexion_maxforce_3sec': {'code': 5, 'file': '2_side_wrist_palmarflexion_maxforce_3sec.mov', 'label': 'Wrist palmarflexion max force 3 sec (side)', 'baseline_code': 2},
    '2_side_wrist_dorsiflexion_maxforce_3sec': {'code': 9, 'file': '2_side_wrist_dorsiflexion_maxforce_3sec.mov', 'label': 'Wrist dorsiflexion max force 3 sec (side)', 'baseline_code': 2},
    '2_side_wrist_dorsiflexion_normalforce_3sec': {'code': 8, 'file': '2_side_wrist_dorsiflexion_normalforce_3sec.mov', 'label': 'Wrist dorsiflexion normal force 3 sec (side)', 'baseline_code': 2},
    '2_side_grasp_cup_3sec': {'code': 11, 'file': '2_side_grasp_cup_3sec.mov', 'label': 'Grasp cup 3 sec (side)', 'baseline_code': 2},
    
    '3_down_openhand_slow_3sec': {'code': 1, 'file': '3_down_openhand_slow_3sec.mov', 'label': 'Open hand slow 3 sec (down)', 'baseline_code': 3},
    '3_down_closetofist_allfingerstogether_slow_3sec': {'code': 2, 'file': '3_down_closetofist_allfingerstogether_slow_3sec.mov', 'label': 'Close to fist allfingerstogether slow 3 sec (down)', 'baseline_code': 3},
    '3_down_closetofist_allfingerstogether_maxforce_3sec': {'code': 3, 'file': '3_down_closetofist_allfingerstogether_maxforce_3sec.mov', 'label': 'Close to fist allfingerstogether max force 3 sec (down)', 'baseline_code': 3},
    '3_down_open_onlythumb_3sec': {'code': 7, 'file': '3_down_open_onlythumb_3sec.mov', 'label': 'Open only thumb 3 sec (down)', 'baseline_code': 3},
    '3_down_close_onlythumb_3sec': {'code': 6, 'file': '3_down_close_onlythumb_3sec.mov', 'label': 'Close only thumb 3 sec (down)', 'baseline_code': 3},
    '3_down_wrist_palmarflexion_normalforce_3sec': {'code': 4, 'file': '3_down_wrist_palmarflexion_normalforce_3sec.mov', 'label': 'Wrist palmarflexion normal force 3 sec (down)', 'baseline_code': 3},
    '3_down_wrist_palmarflexion_maxforce_3sec': {'code': 5, 'file': '3_down_wrist_palmarflexion_maxforce_3sec.mov', 'label': 'Wrist palmarflexion max force 3 sec (down)', 'baseline_code': 3},
    '3_down_wrist_dorsiflexion_normalforce_3sec': {'code': 8, 'file': '3_down_wrist_dorsiflexion_normalforce_3sec.mov', 'label': 'Wrist dorsiflexion normal force 3 sec (down)', 'baseline_code': 3},
    '3_down_wrist_dorsiflexion_maxforce_3sec': {'code': 9, 'file': '3_down_wrist_dorsiflexion_maxforce_3sec.mov', 'label': 'Wrist dorsiflexion max force 3 sec (down)', 'baseline_code': 3},
    '3_down_grasping_pinching_pen_allfingers_3sec': {'code': 12, 'file': '3_down_grasping_pinching_pen_allfingers_3sec.mov', 'label': 'Grasping pinching pen allfingers 3 sec (down)', 'baseline_code': 3},
}