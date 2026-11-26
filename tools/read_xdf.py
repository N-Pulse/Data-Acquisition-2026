"""
read_xdf.py
-----------
Load an .xdf file with pyxdf and plot a regularly-sampled stream (EMG) with MNE.

Usage:
    python read_xdf.py [path_to_file.xdf] [stream_name]
"""

import sys
import numpy as np
import mne
import pyxdf

DEFAULT_XDF = r'C:\Users\eeguser\Documents\CurrentStudy\sub-P080\ses-S001\emg_kraken\sub-P080_ses-S001_task-Default_run-001_emg_kraken.xdf'
DEFAULT_STREAM = "EMG_Stream"


def load_xdf_as_raw(xdf_path, stream_name=DEFAULT_STREAM):
    """Load an XDF file and convert the stream called `stream_name` to an MNE Raw object."""
    print(f"Loading XDF file: {xdf_path}")
    streams, fileheader = pyxdf.load_xdf(xdf_path)
    print(f"Loaded {len(streams)} streams:")
    for i, s in enumerate(streams):
        print(f"  [{i}] {s['info']['name'][0]} | type={s['info']['type'][0]} | "
              f"channels={s['info']['channel_count'][0]} | "
              f"nominal fs={s['info']['nominal_srate'][0]} | "
              f"n_samples={len(s['time_series'])}")

    # Pick the stream by name (the marker stream has no sampling rate and can't be a Raw)
    matches = [s for s in streams if s['info']['name'][0] == stream_name]
    if not matches:
        raise ValueError(f"No stream named '{stream_name}' in this file.")
    stream = matches[0]

    n_ch = int(stream['info']['channel_count'][0])
    fs = float(stream['info']['nominal_srate'][0])
    data = np.asarray(stream['time_series'], dtype=float).T  # (n_channels, n_times)

    if fs <= 0 or data.shape[1] < 2:
        raise ValueError(
            f"Stream '{stream_name}' has no usable data "
            f"(nominal fs={fs}, n_samples={data.shape[1]}). "
            "Check that the bridge was pushing samples and that LabRecorder "
            "was recording this stream."
        )

    # Channel labels (fall back to EMG1..EMGn if the stream has none)
    try:
        chans = stream['info']['desc'][0]['channels'][0]['channel']
        ch_names = [ch['label'][0] for ch in chans]
    except (IndexError, KeyError, TypeError):
        ch_names = []
    if len(ch_names) != n_ch:
        ch_names = [f"EMG{i+1}" for i in range(n_ch)]

    print(f"Stream name: {stream_name}")
    print(f"Channels: {ch_names}")
    print(f"Sampling rate: {fs} Hz")
    print(f"Data shape: {data.shape}")

    # Remove the ADC offset (~8192) for display only
    data = data - data.mean(axis=1, keepdims=True)

    info = mne.create_info(ch_names=ch_names, sfreq=fs, ch_types='emg')
    raw = mne.io.RawArray(data, info)
    raw.info['description'] = stream_name
    return raw


def main():
    xdf_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_XDF
    stream_name = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_STREAM

    raw = load_xdf_as_raw(xdf_path, stream_name=stream_name)

    print("Plotting data...")
    raw.plot(scalings='auto', title=f"{stream_name}", block=False)
    raw.compute_psd(fmin=0, fmax=raw.info['sfreq'] / 2 - 1).plot()


if __name__ == "__main__":
    main()