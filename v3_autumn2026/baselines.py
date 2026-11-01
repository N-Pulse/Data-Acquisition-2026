# -*- coding: utf-8 -*-
"""
Baselines w/ 6 positions 

    code   position
    1      Palm up    (open hand)
    2      Palm side  (open hand)
    3      Palm down  (open hand)
    4      Fist up    (closed hand)
    5      Fist side  (closed hand)
    6      Fist down  (closed hand)

baseline = orientation (1 up / 2 side / 3 down) + 3 if closed hand
Decoding : orientation = ((code - 1) % 3) + 1 ; closed hand if code >= 4.
"""
import os
import re

BASELINE_NAMES = {
    1: "Palm up (hand open)",
    2: "Palm side (hand open)",
    3: "Palm down (hand open)",
    4: "Fist up (hand closed)",
    5: "Fist side (hand closed)",
    6: "Fist down (hand closed)",
}

ORIENTATION_NAMES = {1: "up", 2: "side", 3: "down"}
VALID_STATES = ("open", "closed")


def baseline_of(entry):
    """Baseline 1..6 of a MOVEMENTS entry (computed in MOVEMENTS_shared)."""
    code = entry.get("baseline_code")
    if code not in BASELINE_NAMES:
        raise ValueError(
            f"baseline_code missing or invalid ({code!r}) for : {entry.get('label')}"
        )
    return int(code)


def orientation_of(baseline_code):
    return ((int(baseline_code) - 1) % 3) + 1


def hand_state_of(baseline_code):
    return "closed" if int(baseline_code) >= 4 else "open"


# --------------------------------------------------------------------------- #
# Contrôles au lancement
# --------------------------------------------------------------------------- #
_ORIENT_PREFIX = re.compile(r"^(?:1_up_|2_side_|3_down_)")


def _signature(key):
    root = _ORIENT_PREFIX.sub("", key)
    toks = [t for t in root.split("_") if not re.fullmatch(r"\d+se[cx]", t)]
    if "close_hand" in root:
        out, i = [], 0
        while i < len(toks):
            if toks[i] == "close" and i + 1 < len(toks) and toks[i + 1] == "hand":
                i += 2
                continue
            out.append(toks[i])
            i += 1
        toks = out
    return frozenset(toks)


def _candidate_files(basefile, arm):
    s, e = os.path.splitext(basefile)
    bases = [f"{s}_{arm.lower()}", s]
    exts = [e] if e else []
    for ext in (".mp4", ".mov", ".MP4", ".MOV"):
        if ext not in exts:
            exts.append(ext)
    return [b + ext for b in bases for ext in exts]


def validate_movements(movements, media_dir=None, max_trigger=255):
    """Renvoie la liste des problèmes détectés (liste vide = tout est cohérent).

    Vérifie : champs obligatoires, start_state, un seul code par geste,
    libellés uniques dans chaque baseline (l'interface s'en sert comme clé),
    fichiers vidéo présents (si media_dir est fourni) et plage du trigger Arduino.
    """
    problems = []

    # 1) champs et valeurs
    for k, v in movements.items():
        for field in ("code", "file", "label", "baseline_code", "start_state"):
            if field not in v:
                problems.append(f"{k} : '{field}' missing")
        if v.get("start_state") not in VALID_STATES:
            problems.append(f"{k} : start_state invalid ({v.get('start_state')!r})")

    # 2) un geste = un code, quelle que soit la baseline
    by_gesture = {}
    for k, v in movements.items():
        by_gesture.setdefault(_signature(k), set()).add(v.get("code"))
    for sig, codes in by_gesture.items():
        if len(codes) > 1:
            problems.append(f"codes différents pour le même geste {sorted(sig)} : {sorted(codes)}")

    # 3) un code = un seul geste
    by_code = {}
    for k, v in movements.items():
        by_code.setdefault(v.get("code"), set()).add(_signature(k))
    for code, sigs in by_code.items():
        if len(sigs) > 1:
            problems.append(f"le code {code} est utilisé par plusieurs gestes : "
                            f"{[sorted(s) for s in sigs]}")

    # 4) libellés uniques par baseline (clé du dictionnaire de l'interface)
    seen = {}
    for k, v in movements.items():
        try:
            b = baseline_of(v)
        except ValueError:
            continue
        label = re.sub(r"\s*\((?:up|side|down)\)\s*$", "", v.get("label", ""), flags=re.I)
        if (b, label) in seen:
            problems.append(f"libellé en double dans la baseline {b} : {label!r} "
                            f"({seen[(b, label)]} et {k})")
        seen[(b, label)] = k

    # 5) vidéos présentes
    if media_dir is not None:
        for k, v in movements.items():
            cands = _candidate_files(v["file"], "Left") + _candidate_files(v["file"], "Right")
            if not any(os.path.exists(os.path.join(media_dir, c)) for c in cands):
                problems.append(f"vidéo introuvable : {v['file']}")

    # 6) plage du trigger Arduino (move*10 + phase, phase max = 9)
    biggest = max((v["code"] for v in movements.values() if "code" in v), default=0)
    if biggest * 10 + 9 > max_trigger:
        problems.append(
            f"trigger Arduino : le code de geste {biggest} donne jusqu'à {biggest * 10 + 9}, "
            f"au-delà de {max_trigger} (à vérifier dans Trigger.setData)"
        )
    return problems


def summary(movements):
    """Nombre de mouvements par baseline (1..6)."""
    counts = {b: 0 for b in BASELINE_NAMES}
    for v in movements.values():
        counts[baseline_of(v)] += 1
    return counts


if __name__ == "__main__":
    import sys
    from MOVEMENTS_shared_fall2026 import MOVEMENTS, MOVEMENTS_VERSION

    media = sys.argv[1] if len(sys.argv) > 1 else None
    print(f"MOVEMENTS {MOVEMENTS_VERSION} : {len(MOVEMENTS)} mouvements")
    for b, n in summary(MOVEMENTS).items():
        print(f"  baseline {b} ({BASELINE_NAMES[b]}) : {n} mouvements")
    issues = validate_movements(MOVEMENTS, media_dir=media)
    print(f"{len(issues)} problème(s)")
    for p in issues:
        print("  -", p)