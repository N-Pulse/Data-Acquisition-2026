import re, json, os

def _movement_signature(key: str) -> str:
    """Extract the part of the key that encodes the movement itself,
    e.g. '1_up_openhand_slow_3sec' → 'openhand_slow_3sec'."""
    m = re.match(r'^\d+_(up|side|down)_(.+)$', key)
    return m.group(2) if m else key

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

# Canonical position-independent movement codes
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
    'open_pinky_3sec': 23,
    'open_ring_3sec': 24,
    'open_middle_3sec': 25,
    'open_index_3sec': 26,
    'open_thumb_3sec': 27,
}


def normalize_movement_codes(MOVEMENTS: dict) -> dict:
    """Return a new MOVEMENTS dict where 'code' encodes only movement (not position)."""
    normalized = {}
    for k, v in MOVEMENTS.items():
        sig = _movement_signature(k)
        canonical = MOVEMENT_CODES.get(sig)
        new_code = canonical if canonical is not None else v["code"]
        normalized[k] = {**v, "code": new_code}
    return normalized


def save_movements_dict(MOVEMENTS: dict, filename="MOVEMENTS_normalized.json"):
    """Save the normalized MOVEMENTS dictionary as a nicely formatted JSON file."""
    os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(MOVEMENTS, f, indent=4, ensure_ascii=False)
    print(f"✅ Normalized MOVEMENTS saved to: {os.path.abspath(filename)}")


# Example usage (run this after defining your full MOVEMENTS dict):
MOVEMENTS = normalize_movement_codes(MOVEMENTS)
save_movements_dict(MOVEMENTS, "normalized_MOVEMENTS.json")
