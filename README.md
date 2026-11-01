# N Pulse – Data Acquisition (EEG/EMG)

| Folder           | Contains                                  |                     |
|-------------------|------------------------------------------|---------------------|
| v3_autumn2026     | Current Version (eeg_emg_v3.py)          | fall 2026           |
| v2_fall2025       | eeg_emg_v2.py (+ sans Arduino)           | from      20/11/2025|
| v1_fall2025       | eeg_emg_v1.py                            | from      14/11/2025|
| common            | Shared code (Arduino-LSL bridge)         | toutes              |
| tools             | XDF lecture, viewer real time, notebooks | -                   |
| stimuli           | audio / videos                           | -                   |
| legacy_2025       | Former code (eye detection, etc.)        | archive             |
| data              | Raw rata                                 | par campagne        |

Données à déplacer À LA MAIN (pas touchées par le script) :
- Data/raw/sub-*  -> data/a_trier/
  (puis data/2025-fall/raw/ ou data/2026-autumn/raw/)
- autumn_2026/data/raw -> data/2026-autumn/raw/
Attention : harmoniser les IDs (sub-010 vs sub-0010, sub-011 vs sub-0011).
