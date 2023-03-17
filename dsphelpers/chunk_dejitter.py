import numpy as np

def chunk_jitter_removal(stream, sampling_freq, chunk_size,
                         chunk_gap_sec=0.02, chunk_size_threshold=0.95):
    '''
    Dejitter timestamps within chunks (sample packets) where
    only the first timestamp is correct and the remaining sample timestamps
    are squeezed tightly together (not containing real time information).

    Identifies chunks based on timestamp gaps (distance between the first sample
    of a chunk to the last sample of the previous chunks) and extrapolates
    within-chunk timestamps based on the first sample timestamp with
    step size of 1/sampling_freq.

     Also shifts short chunks (with less than typically received samples) into place
     (that would otherwise appear as overlaps with previous chunks).

    This method was applied in particular for recordings with the OpenBCI Cyton
    that were streamed to LSL using the OpenBCI_LSL code base:
    https://github.com/openbci-archive/OpenBCI_LSL/blob/master/openbci_lsl.py

    Args:
        stream : LSL stream object (e.g. previously loaded using pyxdf.load_xdf()
        sampling_freq : Sampling frequency of the amplifier
        chunk_size : Regular size of the received sample packets (chunks)
        chunk_gap_sec : Threshold used to detect gaps between chunks
        chunk_size_threshold : Threshold used to determine if a shunk was short (Pct of typical samples)
    Returns:
        stream : The stream object with dejittered timestamps
        n_short_chunks : Number of detected short chunks

    Based on the pyxdf jitter_removal function:
    https://github.com/xdf-modules/pyxdf/blob/main/pyxdf/pyxdf.py
    '''

    # Get time stamps from stream
    time_stamps = stream['time_stamps']
    nsamples = len(time_stamps)

    # Identify chunks
    # - i.e. segmenting data based on gaps
    diffs = np.diff(time_stamps)
    b_breaks = diffs > np.max((chunk_gap_sec))

    # Get chunk indices (+ 1 to compensate for lost sample in np.diff)
    break_inds = np.where(b_breaks)[0] + 1
    seg_starts = np.hstack(([0], break_inds))
    seg_stops = np.hstack((break_inds - 1, nsamples - 1))  # inclusive

    # Process each chunk separately
    # - i.e. extrapolate timestamps for each chunk
    chunk_lengths = []
    for start_ix, stop_ix in zip(seg_starts, seg_stops):
        # Adjust and map TS on original chunk TS
        idx = np.arange(start_ix, stop_ix + 1, 1)[:, None]
        first_ts = time_stamps[idx[0]]
        chunk_samples = idx[-1] - idx[0] + 1
        last_ts = first_ts + (chunk_samples-1)*(1/sampling_freq)
        # Correct TS
        time_stamps[idx] = np.linspace(first_ts, last_ts, chunk_samples[0])

        # Store information about chunk lengths for summary metrics
        chunk_lengths.append(chunk_samples < chunk_size * chunk_size_threshold)

        # Shift out of place chunks
        # - by checking if the chunk was short
        # - and checking that this is not done for the first chunk
        if start_ix > 0 and chunk_lengths[-1]:
            # Determine overlap size
            overlap = time_stamps[start_ix] - time_stamps[start_ix - 1]
            # Shift the timestamps
            time_stamps[idx] = time_stamps[idx] -(overlap) + (1 / sampling_freq)

    # Report the frequency of bad chunks
    n_short_chunks = sum(chunk_lengths)[0]

    # Change out time stamp information in stream object
    stream['time_stamps'] = time_stamps

    return stream, n_short_chunks