#!/usr/bin/env python3
"""
N-Pulse EEG/EMG session QC — run right after a recording.

Checks that the recording is technically sound (inactive channels, ground / reference, noise...)
so that the session can be redone while the participant is still there. See README_QC.md.

Usage:
    python qc_session.py                 -> takes the most recent .xdf (Documents/CurrentStudy, ...)
    python qc_session.py file.xdf        -> this specific file

Install (once): pip install pyxdf numpy scipy
Outputs: on screen + folder <file>_QC/ next to the .xdf (qc_summary.txt, qc_channels.csv)
"""
import argparse, csv, glob, os, sys, time
import importlib
try:
    np = importlib.import_module("numpy")
except ModuleNotFoundError as exc:
    if exc.name == "numpy":
        raise SystemExit("NumPy is required. Install it with: python -m pip install numpy") from exc
    raise

try:
    signal = importlib.import_module("scipy.signal")
except ModuleNotFoundError as exc:
    if exc.name == "scipy":
        raise SystemExit("SciPy is required. Install it with: python -m pip install scipy") from exc
    raise

np.seterr(divide="ignore", invalid="ignore")

# =============================== CONFIGURATION ===============================
SEARCH_DIRS = ["~/Documents/CurrentStudy", "~/Documents", "~/Downloads"]   # where to look for the latest .xdf
MAX_AGE_H = 3                 # warn if the latest .xdf is older than 3 h
MARKER_STREAM = "stimulus_stream"   # LSL markers sent by eeg_emg_v3.py (optional)
SYNC_CODE = 128               # sync pulse sent every second on the TRIGGER channel
EMG_LABEL_PREFIX = ("AUX", "BIP", "EMG")

# Inactive channels
OFFSET_MAX_UV = 200_000       # EEG: DC offset > 200 mV -> electrode not connected
FLAT_STD_UV = 0.5             # (filtered) signal almost zero -> flat channel
STUCK_FRAC = 0.05             # > 5 % identical consecutive samples -> stuck / saturated
EMG_DETECT = 1.10             # connected EMG input: activates (x1.10) in at least 2 trials; empty input: ~x1.00
EMG_MIN_CONNECTED = 4         # fewer than 4 EMG channels with signal -> WARN (0 -> FAIL)
INFO_BAD_EEG = 0.05           # up to 5 % unusable EEG channels -> INFO (can be interpolated)
MAX_BAD_EEG = 0.20            # > 20 % -> FAIL
# Ground / reference
LINE_GLOBAL_MAX = 10.0        # median 50 Hz noise over all EEG channels (relative to 1-40 Hz)
CORR_GLOBAL_MAX = 0.95        # all EEG channels almost identical
# EEG noise per channel
LINE_REL = 5.0                # 50 Hz > 5 x the channel median -> noisy channel
HF_Z = 5.0                    # abnormal high-frequency noise (robust z)
AMP_Z = 5.0                   # abnormal amplitude (robust z)
CORR_REL = 0.35               # resembles the others < 35 % as much as the median channel -> isolated channel
BRIDGE_ED_REL = 0.01          # var(A - B) < 1 % of the median over pairs -> gel bridge
WARN_DOUBT_EEG = 0.10         # > 10 % noisy or bridged channels -> WARN
# EMG noise
EMG_MEDFREQ = (40, 200)       # plausible EMG median frequency (Hz)
EMG_LINE_INFO = 10.0          # 50 Hz peak > x10 -> notch filter recommended (INFO)
EMG_LINE_MAX = 50.0           # 50 Hz peak > x50 -> bad contact / amplifier charging (WARN)
EMG_LF_REL = 5.0              # 2-20 Hz energy > 5 x the other EMG channels -> heartbeat / moving cable (INFO)
EMG_SHORT_R = 0.95            # two EMG channels correlated > 0.95 -> electrodes touching each other
# Stability
DRIFT_X = 2.0                 # rest noise x2 between start and end of session -> degraded channel
# =============================================================================

PASS, INFO, SKIP, WARN, FAIL = "PASS", "INFO", "SKIP", "WARN", "FAIL"
ORDER = [PASS, SKIP, INFO, WARN, FAIL]
PHASES = {1: "cue / rest eyes open", 2: "rest eyes closed", 3: "prep", 5: "move", 7: "return", 9: "iti"}
_log_lines = []


def log(msg=""):
    print(msg, flush=True)
    _log_lines.append(msg)


def worst(*s):
    return max(s, key=ORDER.index)


def robust_z(v):
    v = np.asarray(v, float)
    med = np.median(v)
    mad = 1.4826 * np.median(np.abs(v - med)) or 1e-12
    return (v - med) / mad


# =============================== LOADING =====================================
class _Corruption(__import__("logging").Handler):
    """Collects pyxdf warnings about a corrupted / truncated file."""
    def __init__(self):
        super().__init__()
        self.msgs = []

    def emit(self, record):
        if "corrupt" in record.getMessage().lower():
            self.msgs.append(record.getMessage())


def load_xdf(path):
    import logging, pyxdf
    h = _Corruption()
    logging.getLogger("pyxdf").addHandler(h)
    try:
        streams, _ = pyxdf.load_xdf(path)
    finally:
        logging.getLogger("pyxdf").removeHandler(h)
    data = [s for s in streams if float(s["info"]["nominal_srate"][0]) > 0]
    if not data:
        raise RuntimeError("no signal stream in the file")
    s = max(data, key=lambda s: int(s["info"]["channel_count"][0]))
    try:
        labels = [c["label"][0] for c in s["info"]["desc"][0]["channels"][0]["channel"]]
    except Exception:
        labels = []
    ts = np.asarray(s["time_stamps"])
    fs = float(s["info"]["nominal_srate"][0])
    X = np.asarray(s["time_series"], dtype=np.float32)
    dt = np.diff(ts)
    gaps = dt > 2 / fs
    mk = [st for st in streams if st["info"]["name"][0] == MARKER_STREAM]
    markers = None
    if mk and len(mk[0]["time_stamps"]):
        idx = np.searchsorted(ts, np.asarray(mk[0]["time_stamps"]))
        val = np.array([int(float(v[0])) for v in mk[0]["time_series"]])
        ok = (idx > 0) & (idx < len(ts))
        markers = (idx[ok], val[ok])
    meta = dict(name=s["info"]["name"][0], dur=float(ts[-1] - ts[0]),
                fs_eff=(len(ts) - 1) / float(ts[-1] - ts[0]),
                n_gaps=int(gaps.sum()), lost_s=float((dt[gaps] - 1 / fs).sum()), markers=markers,
                corrupt=len(h.msgs))
    return X, fs, labels, meta


def guess_montage(n_ch, labels):
    """EEG = 64 or 128 electrodes; possible EMG = all bipolar / AUX inputs; TRIGGER = last channel."""
    if len(labels) == n_ch and any(l.upper().startswith(EMG_LABEL_PREFIX) for l in labels):
        emg = [i for i, l in enumerate(labels) if l.upper().startswith(EMG_LABEL_PREFIX)]
        eeg = [i for i, l in enumerate(labels[:-1]) if i not in emg and l.upper() not in ("EOG", "TRIGGER")]
        return dict(name=f"{len(eeg)}-channel EEG cap (named channels)", eeg=eeg, emg=emg)
    n_eeg = 128 if n_ch - 1 >= 136 else 64 if n_ch - 1 >= 72 else None
    if n_eeg is None:
        return None
    return dict(name=f"{n_eeg}-electrode EEG cap", eeg=list(range(n_eeg)), emg=list(range(n_eeg, n_ch - 1)))


def find_latest_xdf():
    files = []
    for d in SEARCH_DIRS:
        files += glob.glob(os.path.join(os.path.expanduser(d), "**", "*.xdf"), recursive=True)
    # skip downloads still in progress (Safari .download, Chrome .crdownload, Firefox .part)
    files = [f for f in files if not any(x in f for x in (".download", ".crdownload", ".part"))]
    if not files:
        sys.exit(f"No .xdf file found in {SEARCH_DIRS} -> give the file path as an argument")
    return max(files, key=os.path.getmtime)


# =============================== TESTS =======================================
class QC:
    def __init__(self, X, fs, labels, meta, mont):
        self.X, self.fs, self.labels, self.meta = X, fs, labels, meta
        self.eeg, self.emg_in = mont["eeg"], mont["emg"]
        self.emg = []                      # EMG inputs carrying a signal (filled in test 3)
        self.mont = mont
        self.issues = {c: [] for c in self.eeg + self.emg_in}
        self.results, self.c = {}, {}

    # ------------------------------------------------------------ helpers
    def nm(self, c):
        return f"{c + 1} ({self.labels[c]})" if len(self.labels) == self.X.shape[1] else str(c + 1)

    def chs(self, lst, n=15):
        out = ", ".join(self.nm(c) for c in lst[:n])
        return out + (f" ... (+{len(lst) - n})" if len(lst) > n else "")

    def flag(self, c, level, reason):
        self.issues[c].append((level, reason))

    def bad(self, lst):
        return [c for c in lst if any(l == FAIL for l, _ in self.issues[c])]

    def good(self, lst):
        b = set(self.bad(lst))
        return [c for c in lst if c not in b]

    def segs(self, p):
        """[start, end) segments of phase p (end = next event)."""
        on, ph = self.c["events"]
        return [(on[i], on[i + 1]) for i in np.where(ph[:-1] == p)[0]]

    def run(self, num, total, title, fn):
        log(f"\n[{num}/{total}] {title} ...")
        t = time.time()
        try:
            st, info, reasons = fn()
        except Exception as e:  # a crashing test must not block the others
            st, info, reasons = FAIL, [], [f"the test crashed: {e!r}"]
        for l in info:
            log(f"      {l}")
        log(f"   -> {st}  ({time.time() - t:.1f} s)")
        for r in reasons:
            log(f"      reason: {r}")
        self.results[title] = (st, reasons)

    # ------------------------------------------------------------ 1. file
    def t_file(self):
        m, n = self.meta, self.X.shape[1]
        info = [f"stream: {m['name']} | {n} channels | {self.fs:.0f} Hz | duration {m['dur'] / 60:.1f} min",
                f"actual sampling rate: {m['fs_eff']:.2f} Hz",
                f"montage: {self.mont['name']} + {len(self.emg_in)} possible EMG inputs (bipolar / AUX)"]
        st, reasons = PASS, []
        if abs(m["fs_eff"] - self.fs) / self.fs > 0.01:
            st = FAIL
            reasons.append(f"actual sampling rate {m['fs_eff']:.1f} Hz very different from {self.fs:.0f} Hz")
        if m["n_gaps"]:
            st = worst(st, FAIL if m["lost_s"] > 0.01 * m["dur"] else WARN)
            reasons.append(f"{m['n_gaps']} gaps ({m['lost_s']:.1f} s lost) -> unstable USB cable / amplifier")
        if m.get("corrupt"):
            st = worst(st, WARN)
            reasons.append("corrupted or truncated file (pyxdf) -> download / copy not finished? "
                           "LabRecorder stopped abruptly? Run the QC again on the complete file")
        if m["dur"] < 60:
            st = FAIL
            reasons.append(f"only {m['dur']:.0f} s recorded -> LabRecorder stopped too early?")
        if self.labels and len(self.labels) != n:
            st = worst(st, INFO)
            reasons.append(f"[info] {len(self.labels)} channel names for {n} channels: wrong names in the file "
                           f"(no consequence for the QC)")
        return st, info, reasons

    # ------------------------------------------------------------ 2. events
    def t_events(self):
        tr = np.rint(self.X[:, -1]).astype(int)                       # TRIGGER channel (Arduino)
        on = np.where((tr[1:] != 0) & (tr[1:] != tr[:-1]))[0] + 1
        vals = tr[on]
        n_sync = int((vals == SYNC_CODE).sum())
        normal = set(vals[vals < SYNC_CODE].tolist())
        coll = (vals > SYNC_CODE) & np.isin(vals - SYNC_CODE, list(normal))
        vals = np.where(coll, vals - SYNC_CODE, vals)
        keep = vals != SYNC_CODE
        on, vals = on[keep], vals[keep]
        src = "TRIGGER channel (Arduino)"
        mk = self.meta.get("markers")
        if not (vals % 10 == 5).any() and mk is not None:                # otherwise: LSL markers
            idx, v = mk
            sel = (v >= 10000) & (v < 100000) | np.isin(v, [9701, 9702])
            on = idx[sel]
            vals = np.where(v[sel] == 9701, 1, np.where(v[sel] == 9702, 2, v[sel] // 10000))
            src = f"LSL markers ({MARKER_STREAM})"
        ph = vals % 10
        self.c["events"] = (on, ph)
        self.c["event_vals"] = vals
        n = {p: int((ph == p).sum()) for p in PHASES}
        info = [f"source: {src}"] + [f"{PHASES[p]:<22}: {n[p]}" for p in PHASES]
        info.append(f"sync pulses (1/s): {n_sync}" + (f" ({int(coll.sum())} collisions corrected)"
                                                      if coll.any() else ""))
        if n[5] == 0:
            if n_sync == 0:
                why = ("TRIGGER channel empty (not even the sync pulses) -> Arduino not connected to the amplifiers, "
                       "or 'trigger = None' left in eeg_emg_v3.py")
            else:
                why = ("sync pulses present but no phase codes -> wrong COM port (COM6 / COM10) "
                       "or 'from visual_task_simple import Trigger' still commented out")
            return FAIL, info, [why]
        seq = "".join(str(p) for p in ph)
        n_ok = seq.count("357")
        info.append(f"complete trials (prep -> move -> return): {n_ok}/{n[5]}")
        dur = {}
        for p in (3, 5, 7, 9):
            idx = np.where(ph[:-1] == p)[0]
            if p == 9:   # the last ITI of a block is followed by the (longer) block transition: ignored
                idx = idx[ph[idx + 1] == 3]
            if len(idx):
                dur[p] = (on[idx + 1] - on[idx]) / self.fs
        info.append("median durations (s): " + "  ".join(f"{PHASES[p]} {np.median(d):.1f}" for p, d in dur.items()))
        reasons = []
        if not (n[3] == n[5] == n[7]):
            reasons.append("different numbers of prep / move / return -> triggers are missing")
        if n_ok < n[5]:
            reasons.append(f"{n[5] - n_ok} trials out of order or incomplete -> triggers lost or duplicated")
        for p, d in dur.items():
            irr = np.abs(d - np.median(d)) > max(1.0, 0.5 * np.median(d))
            if p != 5 and irr.sum() > 0.1 * len(d):
                reasons.append(f"'{PHASES[p]}' duration irregular in {irr.sum()} trials -> triggers lost "
                               f"or script slowed down")
        if n[2] == 0:
            reasons.append("[info] no eyes-closed rest at the start (option disabled in eeg_emg_v3.py?)")
        real = [r for r in reasons if not r.startswith("[info]")]
        return (WARN if real else INFO if reasons else PASS), info, reasons

    # ------------------------------------------------------------ precomputation (filters, spectra)
    def _precompute(self):
        fs, X = self.fs, self.X
        bp_eeg = signal.butter(4, [1, 40], "bandpass", fs=fs, output="sos")
        bp_emg = signal.butter(4, [20, min(450, fs / 2 - 1)], "bandpass", fs=fs, output="sos")
        st = {k: {} for k in ["offset", "stuck", "line", "hf", "std", "medfreq", "lf"]}
        E, M = [], []
        for group, sos, store, dec in [(self.eeg, bp_eeg, E, 4), (self.emg_in, bp_emg, M, 1)]:
            for k in range(0, len(group), 16):
                idx = group[k:k + 16]
                x = X[:, idx].astype(np.float64).T
                off = np.median(x[:, ::256], axis=1)
                x -= off[:, None]
                f, p = signal.welch(x, fs=fs, nperseg=2048, axis=-1)
                band = lambda a, b: p[:, (f >= a) & (f < b)].mean(1)
                y = signal.sosfiltfilt(sos, x, axis=-1)[:, ::dec].astype(np.float32)
                store.append(y)
                for j, c in enumerate(idx):
                    st["offset"][c] = off[j]
                    st["stuck"][c] = np.mean(np.diff(x[j]) == 0)
                    st["std"][c] = y[j].std()
                    if group is self.eeg:
                        st["line"][c] = band(49, 51)[j] / band(1, 40)[j]
                        st["hf"][c] = band(55, 95)[j] / band(1, 40)[j]
                    else:
                        sel = (f >= 20) & (f <= 450) & ~((f > 45) & (f < 55))
                        st["line"][c] = band(49, 51)[j] / p[j, sel].mean()
                        b = (f >= 20) & (f <= 450)
                        cum = np.cumsum(p[j, b])
                        st["medfreq"][c] = f[b][np.searchsorted(cum, cum[-1] / 2)]
                        st["lf"][c] = p[j, (f >= 2) & (f < 20)].sum() / p[j, b].sum()   # low frequencies
        self.c.update(E=np.vstack(E), M=np.vstack(M) if M else np.zeros((0, len(X)), np.float32), st=st)

    # ------------------------------------------------------------ 3. inactive channels
    def t_inactive(self):
        self._precompute()
        s = self.c["st"]
        for c in self.eeg:
            if abs(s["offset"][c]) > OFFSET_MAX_UV:
                self.flag(c, FAIL, f"offset {s['offset'][c] / 1000:.0f} mV (electrode not connected)")
            if s["std"][c] < FLAT_STD_UV:
                self.flag(c, FAIL, "flat signal (records nothing)")
            if s["stuck"][c] > STUCK_FRAC:
                self.flag(c, FAIL, f"stuck / saturated values ({100 * s['stuck'][c]:.0f} % of the time)")

        # EMG: which inputs carry a signal? (the others are simply not plugged in)
        M = self.c["M"]
        move, rest = self.segs(5), self.segs(9)
        act = None
        if len(move) >= 2 and rest and len(M):
            rms = lambda segs: np.array([np.sqrt((M[:, a:b] ** 2).mean(1)) for a, b in segs])
            ratio = rms(move) / np.median(rms(rest), 0)
            act = np.sort(ratio, 0)[-2]          # 2nd most active trial: a muscle may work for only 1 gesture in 10
        conn, empty = [], []
        for j, c in enumerate(self.emg_in):
            dead = (s["std"][c] < FLAT_STD_UV or s["stuck"][c] > STUCK_FRAC
                    or (48 <= s["medfreq"][c] <= 52 and s["line"][c] > EMG_LINE_MAX))     # only 50 Hz
            ok = (act[j] >= EMG_DETECT) if act is not None else EMG_MEDFREQ[0] <= s["medfreq"][c] <= EMG_MEDFREQ[1]
            (conn if ok and not dead else empty).append(c)
        self.emg, self.c["emg_empty"] = conn, empty
        self.c["M"] = M[[self.emg_in.index(c) for c in conn]] if conn else M[:0]

        be = self.bad(self.eeg)
        how = "active during movements" if act is not None else "with an EMG-like spectrum (no events)"
        info = [f"inactive EEG: {len(be)}/{len(self.eeg)}" + (f"  -> {self.chs(be)}" if be else ""),
                f"EMG with signal: {len(conn)}/{len(self.emg_in)} inputs ({how})"
                + (f"  -> {self.chs(conn, 20)}" if conn else ""),
                f"EMG without signal: {len(empty)} inputs (not plugged in: normal)"]
        fe = len(be) / len(self.eeg)
        self.c["inactive_eeg"] = FAIL if fe > MAX_BAD_EEG else WARN if fe > INFO_BAD_EEG else INFO if be else PASS
        self.c["inactive_emg"] = FAIL if not conn else WARN if len(conn) < EMG_MIN_CONNECTED else PASS
        reasons = []
        if not conn:
            reasons.append("no EMG channel with signal -> EMG electrodes not connected, or EMG box not plugged "
                           "into the amplifier's 'Bipolar IN'")
        elif len(conn) < EMG_MIN_CONNECTED:
            reasons.append(f"only {len(conn)} EMG channels with signal -> electrodes detached / badly connected?")
        if self.c["inactive_eeg"] in (WARN, FAIL):
            reasons.append(f"{len(be)} inactive EEG channels ({fe:.0%}) -> reposition / re-gel these electrodes")
        reasons += [f"channel {self.nm(c)}: " + "; ".join(r for _, r in self.issues[c]) for c in be]
        return worst(self.c["inactive_eeg"], self.c["inactive_emg"]), info, reasons

    # ------------------------------------------------------------ 4. ground / reference
    def t_ground(self):
        good = self.good(self.eeg)
        E = self.c["E"][[self.eeg.index(c) for c in good]]
        Cov = np.cov(E)
        d = np.sqrt(np.diag(Cov))
        C = Cov / np.outer(d, d)
        np.fill_diagonal(C, np.nan)
        self.c.update(C=C, C_ch=good, Cov=Cov)
        med_corr = np.nanmedian(np.abs(C))
        line_med = np.median([self.c["st"]["line"][c] for c in good])
        info = [f"median 50 Hz noise (all EEG channels): {line_med:.2f}  (max {LINE_GLOBAL_MAX})",
                f"median similarity between channels:    {med_corr:.2f}  (max {CORR_GLOBAL_MAX})"]
        reasons = []
        if line_med > LINE_GLOBAL_MAX:
            reasons.append("ALL channels have strong 50 Hz noise -> ground (GND) or reference badly placed, "
                           "or amplifier charging during the recording")
        if med_corr > CORR_GLOBAL_MAX:
            reasons.append("ALL channels look too similar -> faulty reference or ground")
        return (FAIL if reasons else PASS), info, reasons

    # ------------------------------------------------------------ 5. EEG noise per channel
    def t_eeg_noise(self):
        s, good, C, Cov = self.c["st"], self.c["C_ch"], self.c["C"], self.c["Cov"]
        line = np.array([s["line"][c] for c in good])
        hfz = robust_z(np.log([s["hf"][c] for c in good]))
        ampz = robust_z(np.log([s["std"][c] for c in good]))
        corr = np.nanmedian(np.abs(C), axis=1)
        lm, cm = np.median(line), np.median(corr)
        for j, c in enumerate(good):
            if line[j] > LINE_REL * lm:
                self.flag(c, WARN, f"50 Hz noise {line[j] / lm:.0f}x stronger than the other channels")
            if hfz[j] > HF_Z:
                self.flag(c, WARN, "abnormal high-frequency noise (muscle / bad contact)")
            if abs(ampz[j]) > AMP_Z:
                self.flag(c, FAIL, "abnormal amplitude compared to the other channels")
            if cm > 0.1 and corr[j] < CORR_REL * cm:
                self.flag(c, FAIL, f"does not resemble any other channel (r={corr[j]:.2f}, median {cm:.2f})")
        noisy = [c for c in good if self.issues[c]]
        v = np.diag(Cov)
        ED = v[:, None] + v[None, :] - 2 * Cov          # variance of the difference between two channels
        iu = np.triu_indices(len(good), 1)
        lim = BRIDGE_ED_REL * np.median(ED[iu])
        bridges = [(good[i], good[j]) for i, j in zip(*iu) if ED[i, j] < lim]
        in_bridge = {c for p in bridges for c in p}
        unusable = [c for c in noisy if any(l == FAIL for l, _ in self.issues[c])]
        doubt = [c for c in noisy if c not in unusable]
        n = len(self.eeg)
        info = [f"unusable channels (amplitude / isolated): {len(unusable)}/{len(good)}",
                f"doubtful channels (50 Hz / high frequency): {len(doubt)}/{len(good)}",
                f"probable gel bridges: {len(bridges)} pairs ({len(in_bridge)} channels)"]
        detail = [f"channel {self.nm(c)}: " + "; ".join(r for _, r in self.issues[c]) + "  [unusable]"
                  for c in unusable] + [f"channel {self.nm(c)}: " + "; ".join(r for _, r in self.issues[c])
                                        for c in doubt][:15]
        if bridges:
            detail.append("gel bridges (pairs): " + ", ".join(f"{a + 1}-{b + 1}" for a, b in bridges[:40]))
        n_bad = len(self.bad(self.eeg))
        if n_bad > MAX_BAD_EEG * n:
            return FAIL, info, [f"{n_bad} unusable EEG channels in total (> {MAX_BAD_EEG:.0%})"] + detail
        causes = []
        if n_bad > INFO_BAD_EEG * n:
            causes.append(f"{n_bad} unusable EEG channels (> {INFO_BAD_EEG:.0%})")
        if len(doubt) > WARN_DOUBT_EEG * n:
            causes.append(f"{len(doubt)} noisy channels (> {WARN_DOUBT_EEG:.0%})")
        if len(in_bridge) > WARN_DOUBT_EEG * n:
            causes.append(f"gel bridges on {len(in_bridge)} channels (> {WARN_DOUBT_EEG:.0%}) -> too much gel")
        if causes:
            return WARN, info, ["; ".join(causes)] + detail
        return (INFO if noisy or bridges else PASS), info, detail

    # ------------------------------------------------------------ 6. EMG noise
    def t_emg_noise(self):
        if not self.emg:
            return SKIP, [], ["no EMG channel with signal (see 'Inactive channels')"]
        s = self.c["st"]
        info = ["median freq. (Hz): " + "  ".join(f"{c + 1}:{s['medfreq'][c]:.0f}" for c in self.emg),
                "50 Hz peak (x level): " + "  ".join(f"{c + 1}:{s['line'][c]:.1f}" for c in self.emg)]
        reasons = []
        for c in self.emg:
            mf, ln = s["medfreq"][c], s["line"][c]
            if mf < EMG_MEDFREQ[0]:
                self.flag(c, WARN, f"low median frequency ({mf:.0f} Hz)")
                reasons.append(f"channel {self.nm(c)}: median frequency {mf:.0f} Hz -> movement / cable artefacts")
            elif mf > EMG_MEDFREQ[1]:
                self.flag(c, WARN, f"high median frequency ({mf:.0f} Hz)")
                reasons.append(f"channel {self.nm(c)}: median frequency {mf:.0f} Hz -> mostly noise")
            if ln > EMG_LINE_MAX:
                self.flag(c, WARN, f"very strong 50 Hz noise (x{ln:.0f})")
                reasons.append(f"channel {self.nm(c)}: 50 Hz x{ln:.0f} -> bad contact, or amplifier charging")
        lf_info = []
        if len(self.emg) >= 3:   # a lot of energy below 20 Hz: heartbeat (ECG), moving cable, slow movement
            lf_med = np.median([s["lf"][c] for c in self.emg])
            for c in self.emg:
                if s["lf"][c] > EMG_LF_REL * lf_med and s["lf"][c] > 0.5:
                    lf_info.append(c)
        R = np.corrcoef(self.c["M"][:, ::2]) if len(self.emg) > 1 else np.zeros((1, 1))
        for a in range(len(self.emg)):
            for b in range(a + 1, len(self.emg)):
                if R[a, b] > EMG_SHORT_R:
                    reasons.append(f"channels {self.nm(self.emg[a])} and {self.nm(self.emg[b])} almost identical "
                                   f"(r={R[a, b]:.2f}) -> electrodes touching each other / short circuit")
                    self.flag(self.emg[b], WARN, f"almost identical to channel {self.emg[a] + 1}")
        st = WARN if reasons else PASS
        if lf_info:   # removed by the 20-500 Hz EMG filter: information only
            st = worst(st, INFO)
            reasons.append(f"[info] a lot of energy below 20 Hz on {self.chs(lf_info)} (heartbeat / moving cable) "
                           f"-> no consequence after 20-500 Hz filtering; tape the cables down")
        notch = [c for c in self.emg if EMG_LINE_INFO < s["line"][c] <= EMG_LINE_MAX]
        if notch:
            st = worst(st, INFO)
            reasons.append(f"[info] marked 50 Hz on {self.chs(notch)} -> 50 Hz notch filter recommended")
        return st, info, reasons

    # ------------------------------------------------------------ 7. stability
    def t_stability(self):
        """Noise during the ITIs (rest) of the first third vs the last third of the session."""
        rest = self.segs(9)
        if len(rest) < 6:
            return SKIP, [], ["fewer than 6 ITIs (missing events): cannot compare start and end"]
        k = len(rest) // 3
        first, last = rest[:k], rest[-k:]
        info, reasons, worse_n = [], [], {}
        for name, chs, A, dec in [("EEG", self.good(self.eeg), self.c["E"], 4), ("EMG", self.emg, self.c["M"], 1)]:
            if not chs:
                continue
            A = A[[(self.eeg if name == "EEG" else self.emg).index(c) for c in chs]]
            rms = lambda segs: np.median([np.sqrt((A[:, a // dec:b // dec] ** 2).mean(1)) for a, b in segs], 0)
            r = rms(last) / rms(first)
            worse = [c for c, x in zip(chs, r) if x > DRIFT_X]
            worse_n[name] = (len(worse), len(chs))
            info.append(f"{name}: rest noise end / start x{np.median(r):.2f} (median); "
                        f"{len(worse)} degraded channels (> x{DRIFT_X:.0f})")
            if worse:
                reasons.append(f"{name} degraded during the session: {self.chs(worse)}")
        we, ne = worse_n.get("EEG", (0, 1))
        wm, _ = worse_n.get("EMG", (0, 1))
        self.c["stab_eeg"] = WARN if we > WARN_DOUBT_EEG * ne else INFO if we else PASS
        self.c["stab_emg"] = WARN if wm >= 2 else INFO if wm else PASS
        st = worst(self.c["stab_eeg"], self.c["stab_emg"])
        if st == WARN:
            reasons.insert(0, "quality drops during the session -> check / re-gel the electrodes between blocks")
        return st, info, reasons


# =============================== VERDICT & OUTPUTS ===========================
def verdict(statuses):
    if FAIL in statuses:
        return "RED - redo / fix"
    if WARN in statuses:
        return "ORANGE - usable with caution"
    return "GREEN - OK" + (" (with info)" if INFO in statuses else "")


def main():
    ap = argparse.ArgumentParser(description="EEG/EMG session QC")
    ap.add_argument("xdf", nargs="?", help=".xdf file (default: the most recent one)")
    a = ap.parse_args()
    if a.xdf is None:
        a.xdf = find_latest_xdf()
        age_h = (time.time() - os.path.getmtime(a.xdf)) / 3600
        log(f"Most recent file: {a.xdf}  (modified {age_h * 60:.0f} min ago)")
        if age_h > MAX_AGE_H:
            log(f"   WARNING: older than {MAX_AGE_H} h, is this really the session that just ended?")
    t0 = time.time()
    log(f"QC of {os.path.basename(a.xdf)}")
    log("Loading the file ...")
    X, fs, labels, meta = load_xdf(a.xdf)
    log(f"   loaded in {time.time() - t0:.0f} s")

    mont = guess_montage(X.shape[1], labels)
    if mont is None:
        log(f"\nVERDICT: RED - {X.shape[1]} channels: neither a 64 nor a 128 cap recognised (adapt guess_montage)")
        return
    qc = QC(X, fs, labels, meta, mont)
    tests = [("File complete", qc.t_file),
             ("Events (triggers)", qc.t_events),
             ("Inactive channels", qc.t_inactive),
             ("EEG: ground / reference", qc.t_ground),
             ("EEG: noise per channel", qc.t_eeg_noise),
             ("EMG: noise", qc.t_emg_noise),
             ("Stability during the session", qc.t_stability)]
    for i, (title, fn) in enumerate(tests, 1):
        qc.run(i, len(tests), title, fn)

    R = {t: s for t, (s, _) in qc.results.items()}
    common = [R["File complete"], R["Events (triggers)"]]
    v_eeg = verdict(common + [qc.c.get("inactive_eeg", SKIP), R["EEG: ground / reference"],
                              R["EEG: noise per channel"], qc.c.get("stab_eeg", SKIP)])
    v_emg = verdict(common + [qc.c.get("inactive_emg", SKIP), R["EMG: noise"], qc.c.get("stab_emg", SKIP)])
    be = qc.bad(qc.eeg)
    log("\n" + "=" * 64)
    log(f"VERDICT EEG: {v_eeg}")
    log(f"VERDICT EMG: {v_emg}")
    log(f"usable EEG: {len(qc.eeg) - len(be)}/{len(qc.eeg)} | "
        f"EMG with signal: {len(qc.emg)} (empty inputs: {len(qc.c.get('emg_empty', []))})")
    for c in be:
        log(f"   EEG {qc.nm(c)} unusable: " + "; ".join(r for l, r in qc.issues[c] if l == FAIL))
    for title, (st, reasons) in qc.results.items():
        main_r = next((r for r in reasons if not r.startswith("[info]")), reasons[0] if reasons else "")
        log(f"   {st:<4}  {title}" + (f"  ({main_r})" if main_r and st != PASS else ""))
    log(f"Total time: {time.time() - t0:.0f} s")
    log("=" * 64)

    out = os.path.splitext(a.xdf)[0] + "_QC"
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "qc_summary.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(_log_lines))
    s = qc.c.get("st", {})
    named = len(labels) == X.shape[1]
    with open(os.path.join(out, "qc_channels.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["channel", "name", "type", "status", "reasons", "offset_mV", "noise_50Hz", "emg_median_freq_Hz"])
        for c in qc.eeg + qc.emg:
            iss = qc.issues[c]
            stat = FAIL if any(l == FAIL for l, _ in iss) else WARN if iss else PASS
            emg = c in qc.emg
            w.writerow([c + 1, labels[c] if named else "", "EMG" if emg else "EEG", stat,
                        "; ".join(r for _, r in iss),
                        round(s["offset"][c] / 1000, 1) if s else "", round(s["line"][c], 2) if s else "",
                        round(float(s["medfreq"][c])) if (emg and s) else ""])
        for c in qc.c.get("emg_empty", []):
            w.writerow([c + 1, labels[c] if named else "", "EMG", "NO SIGNAL", "input not plugged in", "", "", ""])
    log(f"Report saved in {out}")


if __name__ == "__main__":
    main()
