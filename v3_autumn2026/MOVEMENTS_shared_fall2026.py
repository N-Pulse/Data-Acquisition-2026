# MOVEMENTS_shared_fall2026.py
# Now 6 baselines instead of 3, and a few new movements while some were removed. 
# The baseline code is now computed from the view and the start state of the hand :
#   'start'      : state of the hand at the beginning ('open' / 'closed')
#   'rule'       : name with "close_hand" or movement "open_*"/"openhand_*" = closed hand at the beginning ; else, open hand.
#   'baseline_code' : computed in the bottom of the file from (view, start) with BASELINE_CODE.

MOVEMENTS_VERSION = "fall2026"

BASELINE_CODE = {
    ('up',   'open'):   1,
    ('side', 'open'):   2,
    ('down', 'open'):   3,
    ('up',   'closed'): 4,
    ('side', 'closed'): 5,
    ('down', 'closed'): 6,
}
 
MOVEMENTS = {
    '1_up_closetofist_allfingerstogether_3sec_normalforce': {'code': 12, 'file': '1_up_closetofist_allfingerstogether_3sec_normalforce.mov', 'label': 'Close to fist allfingerstogether 3 sec normal force (up)', 'start': 'open'},
    '1_up_close_fourfingers_together_3sec': {'code': 1, 'file': '1_up_close_fourfingers_together_3sec.mov', 'label': 'Close four fingers together 3 sec (up)', 'start': 'open'},
    '1_up_open_fourfingers_together_3sec': {'code': 18, 'file': '1_up_open_fourfingers_together_3sec.mov', 'label': 'Open four fingers together 3 sec (up)', 'start': 'closed'},
    '1_up_close_onlythumb_3sec': {'code': 4, 'file': '1_up_close_onlythumb_3sec.mov', 'label': 'Close only thumb 3 sec (up)', 'start': 'open'},
    '1_up_open_onlythumb_3sec': {'code': 21, 'file': '1_up_open_onlythumb_3sec.mov', 'label': 'Open only thumb 3 sec (up)', 'start': 'closed'},
    '1_up_wrist_palmarflexion_normalforce_3sec': {'code': 31, 'file': '1_up_wrist_palmarflexion_normalforce_3sec.mov', 'label': 'Wrist palmarflexion normal force 3 sec (up)', 'start': 'open'},
    '1_up_wrist_dorsiflexion_normalforce_3sec': {'code': 29, 'file': '1_up_wrist_dorsiflexion_normalforce_3sec.mov', 'label': 'Wrist dorsiflexion normal force 3 sec (up)', 'start': 'open'},
    '1_up_close_pinky_3sec': {'code': 5, 'file': '1_up_close_pinky_3sec.mov', 'label': 'Close pinky 3 sec (up)', 'start': 'open'},
    '1_up_close_ring_3sec': {'code': 6, 'file': '1_up_close_ring_3sec.mov', 'label': 'Close ring 3 sec (up)', 'start': 'open'},
    '1_up_close_middle_3sec': {'code': 3, 'file': '1_up_close_middle_3sec.mov', 'label': 'Close middle 3 sec (up)', 'start': 'open'},
    '1_up_close_index_3sec': {'code': 2, 'file': '1_up_close_index_3sec.mov', 'label': 'Close index 3 sec (up)', 'start': 'open'},
    '1_up_open_pinky_3sec': {'code': 23, 'file': '1_up_open_pinky_3sec.mov', 'label': 'Open pinky 3 sec (up)', 'start': 'closed'},
    '1_up_open_ring_3sec': {'code': 24, 'file': '1_up_open_ring_3sec.mov', 'label': 'Open ring 3 sec (up)', 'start': 'closed'},
    '1_up_open_middle_3sec': {'code': 20, 'file': '1_up_open_middle_3sec.mov', 'label': 'Open middle 3 sec (up)', 'start': 'closed'},
    '1_up_open_index_3sec': {'code': 19, 'file': '1_up_open_index_3sec.mov', 'label': 'Open index 3 sec (up)', 'start': 'closed'},
    '2_side_closetofist_allfingerstogether_normalforce_3sec': {'code': 12, 'file': '2_side_closetofist_allfingerstogether_normalforce_3sec.mov', 'label': 'Close to fist allfingerstogether normal force 3 sec (side)', 'start': 'open'},
    '2_side_open_fourfingers_together_3sec': {'code': 18, 'file': '2_side_open_fourfingers_together_3sec.mov', 'label': 'Open four fingers together 3 sec (side)', 'start': 'closed'},
    '2_side_close_fourfingers_together_3sec': {'code': 1, 'file': '2_side_close_fourfingers_together_3sec.mov', 'label': 'Close four fingers together 3 sec (side)', 'start': 'open'},
    '2_side_open_onlythumb_3sec': {'code': 21, 'file': '2_side_open_onlythumb_3sec.mov', 'label': 'Open only thumb 3 sec (side)', 'start': 'closed'},
    '2_side_close_onlythumb_3sec': {'code': 4, 'file': '2_side_close_onlythumb_3sec.mov', 'label': 'Close only thumb 3 sec (side)', 'start': 'open'},
    '2_side_wrist_palmarflexion_normalforce_3sec': {'code': 31, 'file': '2_side_wrist_palmarflexion_normalforce_3sec.mov', 'label': 'Wrist palmarflexion normal force 3 sec (side)', 'start': 'open'},
    '2_side_wrist_dorsiflexion_normalforce_3sec': {'code': 29, 'file': '2_side_wrist_dorsiflexion_normalforce_3sec.mov', 'label': 'Wrist dorsiflexion normal force 3 sec (side)', 'start': 'open'},
    '2_side_grasp_cup_3sec': {'code': 14, 'file': '2_side_grasp_cup_3sec.mov', 'label': 'Grasp cup 3 sec (side)', 'start': 'open'},
    '2_side_close_pinky_3sec': {'code': 5, 'file': '2_side_close_pinky_3sec.mov', 'label': 'Close pinky 3 sec (side)', 'start': 'open'},
    '2_side_close_ring_3sec': {'code': 6, 'file': '2_side_close_ring_3sec.mov', 'label': 'Close ring 3 sec (side)', 'start': 'open'},
    '2_side_close_middle_3sec': {'code': 3, 'file': '2_side_close_middle_3sec.mov', 'label': 'Close middle 3 sec (side)', 'start': 'open'},
    '2_side_close_index_3sec': {'code': 2, 'file': '2_side_close_index_3sec.mov', 'label': 'Close index 3 sec (side)', 'start': 'open'},
    '2_side_open_pinky_3sec': {'code': 23, 'file': '2_side_open_pinky_3sec.mov', 'label': 'Open pinky 3 sec (side)', 'start': 'closed'},
    '2_side_open_ring_3sec': {'code': 24, 'file': '2_side_open_ring_3sec.mov', 'label': 'Open ring 3 sec (side)', 'start': 'closed'},
    '2_side_open_middle_3sec': {'code': 20, 'file': '2_side_open_middle_3sec.mov', 'label': 'Open middle 3 sec (side)', 'start': 'closed'},
    '2_side_open_index_3sec': {'code': 19, 'file': '2_side_open_index_3sec.mov', 'label': 'Open index 3 sec (side)', 'start': 'closed'},
    '3_down_closetofist_allfingerstogether_normalforce_3sec': {'code': 12, 'file': '3_down_closetofist_allfingerstogether_normalforce_3sec.mov', 'label': 'Close to fist allfingerstogether normal force 3 sec (down)', 'start': 'open'},
    '3_down_open_fourfingers_together_3sec': {'code': 18, 'file': '3_down_open_fourfingers_together_3sec.mov', 'label': 'Open four fingers together 3 sec (down)', 'start': 'closed'},
    '3_down_close_fourfingers_together_3sec': {'code': 1, 'file': '3_down_close_fourfingers_together_3sec.mov', 'label': 'Close four fingers together 3 sec (down)', 'start': 'open'},
    '3_down_open_onlythumb_3sec': {'code': 21, 'file': '3_down_open_onlythumb_3sec.mov', 'label': 'Open only thumb 3 sec (down)', 'start': 'closed'},
    '3_down_close_onlythumb_3sec': {'code': 4, 'file': '3_down_close_onlythumb_3sec.mov', 'label': 'Close only thumb 3 sec (down)', 'start': 'open'},
    '3_down_wrist_palmarflexion_normalforce_3sec': {'code': 31, 'file': '3_down_wrist_palmarflexion_normalforce_3sec.mov', 'label': 'Wrist palmarflexion normal force 3 sec (down)', 'start': 'open'},
    '3_down_wrist_dorsiflexion_normalforce_3sec': {'code': 29, 'file': '3_down_wrist_dorsiflexion_normalforce_3sec.mov', 'label': 'Wrist dorsiflexion normal force 3 sec (down)', 'start': 'open'},
    '3_down_grasping_pinching_pen_allfingers_3sec': {'code': 17, 'file': '3_down_grasping_pinching_pen_allfingers_3sec.mov', 'label': 'Grasping pinching pen allfingers 3 sec (down)', 'start': 'open'},
    '3_down_grasping_pinching_pen_2fingers_3sec': {'code': 16, 'file': '3_down_grasping_pinching_pen_2fingers_3sec.mov', 'label': 'Grasping pinching pen 2fingers 3 sec (down)', 'start': 'open'},
    '3_down_close_pinky_3sec': {'code': 5, 'file': '3_down_close_pinky_3sec.mov', 'label': 'Close pinky 3 sec (down)', 'start': 'open'},
    '3_down_close_ring_3sec': {'code': 6, 'file': '3_down_close_ring_3sec.mov', 'label': 'Close ring 3 sec (down)', 'start': 'open'},
    '3_down_close_middle_3sec': {'code': 3, 'file': '3_down_close_middle_3sec.mov', 'label': 'Close middle 3 sec (down)', 'start': 'open'},
    '3_down_close_index_3sec': {'code': 2, 'file': '3_down_close_index_3sec.mov', 'label': 'Close index 3 sec (down)', 'start': 'open'},
    '3_down_open_pinky_3sec': {'code': 23, 'file': '3_down_open_pinky_3sec.mov', 'label': 'Open pinky 3 sec (down)', 'start': 'closed'},
    '3_down_open_ring_3sec': {'code': 24, 'file': '3_down_open_ring_3sec.mov', 'label': 'Open ring 3 sec (down)', 'start': 'closed'},
    '3_down_open_middle_3sec': {'code': 20, 'file': '3_down_open_middle_3sec.mov', 'label': 'Open middle 3 sec (down)', 'start': 'closed'},
    '3_down_open_index_3sec': {'code': 19, 'file': '3_down_open_index_3sec.mov', 'label': 'Open index 3 sec (down)', 'start': 'closed'},
    '1_up_wrist_close_hand_palmarflexion_normalforce_3sec': {'code': 32, 'file': '1_up_wrist_close_hand_palmarflexion_normalforce_3sec.mov', 'label': 'Wrist close hand palmarflexion normal force 3 sec (up)', 'start': 'closed'},
    '3_down_wrist_close_hand_palmarflexion_normalforce_3sec': {'code': 32, 'file': '3_down_wrist_close_hand_palmarflexion_normalforce_3sec.mov', 'label': 'Wrist close hand palmarflexion normal force 3 sec (down)', 'start': 'closed'},
    '2_side_wrist_close_hand_palmarflexion_normalforce_3sec': {'code': 32, 'file': '2_side_wrist_close_hand_palmarflexion_normalforce_3sec.mov', 'label': 'Wrist close hand palmarflexion normal force 3 sec (side)', 'start': 'closed'},
    '1_up_wrist_close_hand_dorsiflexion_normalforce_3sec': {'code': 33, 'file': '1_up_wrist_close_hand_dorsiflexion_normalforce_3sec.mov', 'label': 'Wrist close hand dorsiflexion normal force 3 sec (up)', 'start': 'closed'},
    '3_down_wrist_close_hand_dorsiflexion_normalforce_3sec': {'code': 33, 'file': '3_down_wrist_close_hand_dorsiflexion_normalforce_3sec.mov', 'label': 'Wrist close hand dorsiflexion normal force 3 sec (down)', 'start': 'closed'},
    '2_side_wrist_close_hand_dorsiflexion_normalforce_3sec': {'code': 33, 'file': '2_side_wrist_close_hand_dorsiflexion_normalforce_3sec.mov', 'label': 'Wrist close hand dorsiflexion normal force 3 sec (side)', 'start': 'closed'},
    '1_up_rotation_3sec': {'code': 34, 'file': '1_up_rotation_3sec.mov', 'label': 'Wrist rotation 3 sec (up)', 'start': 'open'},
    '3_down_rotation_3sec': {'code': 34, 'file': '3_down_rotation_3sec.mov', 'label': 'Wrist rotation 3 sec (down)', 'start': 'open'},
    '2_side_rotation_up_3sec': {'code': 34, 'file': '2_side_rotation_up_3sec.mov', 'label': 'Wrist rotation up direction 3 sec (side)', 'start': 'open'},
    '2_side_rotation_down_3sec': {'code': 34, 'file': '2_side_rotation_down_3sec.mov', 'label': 'Wrist rotation down direction 3 sec (side)', 'start': 'open'},
    '1_up_close_hand_rotation_3sec': {'code': 34, 'file': '1_up_close_hand_rotation_3sec.mov', 'label': 'Wrist close hand rotation 3 sec (up)', 'start': 'closed'},
    '3_down_close_hand_rotation_3sec': {'code': 34, 'file': '3_down_close_hand_rotation_3sec.mov', 'label': 'Wrist close hand rotation 3 sec (down)', 'start': 'closed'},
    '2_side_close_hand_rotation_up_3sec': {'code': 34, 'file': '2_side_close_hand_rotation_up_3sec.mov', 'label': 'Wrist close hand rotation up direction 3 sec (side)', 'start': 'closed'},
    '2_side_close_hand_rotation_down_3sec': {'code': 34, 'file': '2_side_close_hand_rotation_down_3sec.mov', 'label': 'Wrist close hand rotation down direction 3 sec (side)', 'start': 'closed'},
    '1_up_open_onlythumb_palm_3sec': {'code': 35, 'file': '1_up_open_onlythumb_palm_3sec.mov', 'label': 'Open only thumb over fingers 3 sec (up)', 'start': 'closed'},
    '3_down_open_onlythumb_palm_3sec': {'code': 35, 'file': '3_down_open_onlythumb_palm_3sec.mov', 'label': 'Open only thumb over fingers 3 sec (down)', 'start': 'closed'},
    '2_side_open_onlythumb_palm_3sec': {'code': 35, 'file': '2_side_open_onlythumb_palm_3sec.mov', 'label': 'Open only thumb over fingers 3 sec (side)', 'start': 'closed'},
    '1_up_close_onlythumb_palm_3sec': {'code': 36, 'file': '1_up_close_onlythumb_palm_3sec.mov', 'label': 'Close only thumb over fingers 3 sec (up)', 'start': 'open'},
    '3_down_close_onlythumb_palm_3sec': {'code': 36, 'file': '3_down_close_onlythumb_palm_3sec.mov', 'label': 'Close only thumb over fingers 3 sec (down)', 'start': 'open'},
    '2_side_close_onlythumb_palm_3sec': {'code': 36, 'file': '2_side_close_onlythumb_palm_3sec.mov', 'label': 'Close only thumb over fingers 3 sec (side)', 'start': 'open'},
    '1_up_open_allfingers_together_3sec': {'code': 37, 'file': '1_up_open_allfingers_together_3sec.mov', 'label': 'Open all fingers together 3 sec (up)', 'start': 'closed'},
    '3_down_open_allfingers_together_3sec': {'code': 37, 'file': '3_down_open_allfingers_together_3sec.mov', 'label': 'Open all fingers together 3 sec (down)', 'start': 'closed'},
    '2_side_open_allfingers_together_3sec': {'code': 37, 'file': '2_side_open_allfingers_together_3sec.mov', 'label': 'Open all fingers together 3 sec (side)', 'start': 'closed'},
    '2_side_grasp_cup_4fingers_3sec': {'code': 38, 'file': '2_side_grasp_cup_4fingers_3sec.mov', 'label': 'Grasp cup 4 fingers 3 sec (side)', 'start': 'open'},
    '3_down_grasping_pinching_pen_3fingers_3sec': {'code': 39, 'file': '3_down_grasping_pinching_pen_3fingers_3sec.mov', 'label': 'Grasping pinching pen 3 fingers 3 sec (down)', 'start': 'open'},
}
 
_VIEW = {'1': 'up', '2': 'side', '3': 'down'}
for _k, _v in MOVEMENTS.items():
    _v['baseline_code'] = BASELINE_CODE[(_VIEW[_k[0]], _v['start'])]
    _v['start_state'] = _v['start']