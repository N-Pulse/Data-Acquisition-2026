"""
visualize_xdf_with_mne.py
--------------------------
Load and visualize a .xdf file using pyxdf and MNE.

Usage:
    python visualize_xdf_with_mne.py path_to_file.xdf
"""

import sys
import numpy as np
import mne
import pyxdf


def load_xdf_as_raw(xdf_path, stream_index=0):
    """
    Load an XDF file and convert a selected stream to an MNE Raw object.

    Parameters
    ----------
    xdf_path : str
        Path to the .xdf file
    stream_index : int
        Index of the stream to load (default=0)

    Returns
    -------
    raw : mne.io.RawArray
        The data loaded as an MNE Raw object
    """

    print(f"Loading XDF file: {xdf_path}")
    streams, fileheader = pyxdf.load_xdf(xdf_path)
    print(f"Loaded {len(streams)} streams.")

    # Choose one stream (usually EEG or physiological data)
    stream = streams[stream_index]
    name = stream['info']['name'][0]
    ch_names = [ch['label'][0] for ch in stream['info']['desc'][0]['channels'][0]['channel']]
    fs = float(stream['info']['nominal_srate'][0])
    data = np.array(stream['time_series']).T  # shape: (n_channels, n_times)

    print(f"Stream name: {name}")
    print(f"Channels: {ch_names}")
    print(f"Sampling rate: {fs} Hz")
    print(f"Data shape: {data.shape}")

    # Create MNE info object
    info = mne.create_info(ch_names=ch_names, sfreq=fs, ch_types='eeg')

    # Create MNE Raw object
    raw = mne.io.RawArray(data, info)
    raw.info['description'] = name

    return raw


def main():
    if len(sys.argv) < 2:
        print("Usage: python visualize_xdf_with_mne.py path_to_file.xdf [stream_index]")
        sys.exit(1)

    xdf_path = 'Users\eeguser\Documents\CurrentStudy\sub-007\ses-James_Bond\eeg\sub-007_ses-James_Bond_task-Default_run-001_eeg.xdf'
    stream_index = int(sys.argv[2]) if len(sys.argv) > 2 else 0

    raw = load_xdf_as_raw(xdf_path, stream_index=stream_index)

    print("Plotting data...")
    raw.plot(scalings='auto', title=f"Stream {stream_index}: {raw.info['description']}")
    mne.viz.plot_raw_psd(raw, fmin=0, fmax=50)


if __name__ == "__main__":
    main()
