import numpy as np
from collections import Counter


# Note names
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Standard guitar string frequencies (standard tuning E2 A2 D3 G3 B3 E4)
GUITAR_STRINGS = {
    "E2": 82.41,
    "A2": 110.00,
    "D3": 146.83,
    "G3": 196.00,
    "B3": 246.94,
    "E4": 329.63,
}

# Chord templates (semitone intervals from root)
CHORD_TEMPLATES = {
    "major":      [0, 4, 7],
    "minor":      [0, 3, 7],
    "dom7":       [0, 4, 7, 10],
    "maj7":       [0, 4, 7, 11],
    "min7":       [0, 3, 7, 10],
    "sus2":       [0, 2, 7],
    "sus4":       [0, 5, 7],
    "dim":        [0, 3, 6],
    "aug":        [0, 4, 8],
    "power":      [0, 7],
}


class AudioAnalyzer:
    """
    Analyzes audio samples in real-time:
    - Pitch detection via YIN algorithm
    - Note name conversion
    - Chord detection via chroma vector matching
    """

    def __init__(self, min_confidence=0.15):
        self.min_confidence = min_confidence
        self._note_history = []
        self._history_len = 8

    def analyze(self, samples, sample_rate):
        """
        Analyze a chunk of audio samples.
        Returns: {
          'frequency': float or None,
          'note': str or None,  e.g. 'E4'
          'notes': list of str,
          'chord': str or None,  e.g. 'Am'
          'confidence': float,
          'volume': float,
        }
        """
        result = {
            "frequency": None,
            "note": None,
            "notes": [],
            "chord": None,
            "confidence": 0.0,
            "volume": 0.0,
        }

        if len(samples) == 0:
            return result

        # Volume check
        rms = float(np.sqrt(np.mean(samples ** 2)))
        result["volume"] = rms

        # Silence threshold
        if rms < 0.005:
            return result

        # --- Monophonic pitch via YIN ---
        freq, confidence = self._yin_pitch(samples, sample_rate)
        if freq and confidence > self.min_confidence:
            result["frequency"] = freq
            result["confidence"] = confidence
            note = self._freq_to_note(freq)
            result["note"] = note
            if note:
                result["notes"] = [note]
                self._note_history.append(note)
                if len(self._note_history) > self._history_len:
                    self._note_history.pop(0)

        # --- Chord detection via chroma ---
        chord = self._detect_chord_fft(samples, sample_rate)
        if chord:
            result["chord"] = chord

        return result

    def _yin_pitch(self, samples, sample_rate, max_freq=1400.0, min_freq=70.0):
        """
        YIN pitch detection algorithm.
        Returns (frequency, confidence) or (None, 0.0)
        """
        N = len(samples)
        tau_min = int(sample_rate / max_freq)
        tau_max = min(N // 2, int(sample_rate / min_freq))

        if tau_max <= tau_min:
            return None, 0.0

        # Step 1: Difference function
        d = np.zeros(tau_max)
        for tau in range(1, tau_max):
            diff = samples[:N - tau] - samples[tau:N]
            d[tau] = np.sum(diff ** 2)

        # Step 2: Cumulative mean normalized difference
        cmnd = np.zeros(tau_max)
        cmnd[0] = 1.0
        cumsum = 0.0
        for tau in range(1, tau_max):
            cumsum += d[tau]
            if cumsum == 0:
                cmnd[tau] = 1.0
            else:
                cmnd[tau] = d[tau] * tau / cumsum

        # Step 3: Absolute threshold - find first dip below 0.1
        threshold = 0.1
        tau_est = -1
        for tau in range(tau_min, tau_max):
            if cmnd[tau] < threshold:
                # Find local minimum
                while tau + 1 < tau_max and cmnd[tau + 1] < cmnd[tau]:
                    tau += 1
                tau_est = tau
                break

        if tau_est == -1:
            # Find global minimum
            tau_est = tau_min + int(np.argmin(cmnd[tau_min:tau_max]))

        if tau_est == 0:
            return None, 0.0

        # Step 4: Parabolic interpolation for sub-sample accuracy
        if 0 < tau_est < tau_max - 1:
            a = cmnd[tau_est - 1]
            b = cmnd[tau_est]
            c = cmnd[tau_est + 1]
            denom = 2 * b - a - c
            if denom != 0:
                tau_est = tau_est + (a - c) / (2 * denom)

        freq = sample_rate / tau_est
        confidence = 1.0 - cmnd[int(min(tau_est, tau_max - 1))]
        confidence = max(0.0, min(1.0, confidence))

        # Validate frequency range
        if not (min_freq <= freq <= max_freq):
            return None, 0.0

        return float(freq), float(confidence)

    def _freq_to_note(self, freq):
        """Convert frequency to note name with octave (e.g. 'A4')"""
        if freq <= 0:
            return None
        # A4 = 440 Hz, MIDI note 69
        midi = 69 + 12 * np.log2(freq / 440.0)
        midi_int = int(round(midi))
        if midi_int < 0 or midi_int > 127:
            return None
        octave = (midi_int // 12) - 1
        name = NOTE_NAMES[midi_int % 12]
        return f"{name}{octave}"

    def _detect_chord_fft(self, samples, sample_rate):
        """
        Detect chord using chroma vector from FFT.
        Returns chord string like 'Am' or None.
        """
        N = len(samples)
        # Apply Hann window
        window = np.hanning(N)
        spectrum = np.abs(np.fft.rfft(samples * window))
        freqs = np.fft.rfftfreq(N, 1.0 / sample_rate)

        # Build chroma vector (12 semitones)
        chroma = np.zeros(12)
        for i, f in enumerate(freqs):
            if f < 60 or f > 1400:
                continue
            if spectrum[i] < 0.01:
                continue
            # Map frequency to pitch class
            midi = 69 + 12 * np.log2(f / 440.0)
            pitch_class = int(round(midi)) % 12
            chroma[pitch_class] += spectrum[i]

        if np.max(chroma) == 0:
            return None

        chroma = chroma / np.max(chroma)

        # Find active notes (above threshold)
        active = set(np.where(chroma > 0.3)[0])
        if len(active) < 2:
            return None

        # Match against chord templates
        best_chord = None
        best_score = 0.0

        for root in range(12):
            for chord_type, intervals in CHORD_TEMPLATES.items():
                chord_notes = set((root + i) % 12 for i in intervals)
                overlap = len(active & chord_notes)
                score = overlap / max(len(chord_notes), len(active))
                if score > best_score and score > 0.6:
                    best_score = score
                    suffix = "" if chord_type == "major" else (
                        "m" if chord_type == "minor" else
                        "7" if chord_type == "dom7" else
                        "maj7" if chord_type == "maj7" else
                        "m7" if chord_type == "min7" else
                        "sus2" if chord_type == "sus2" else
                        "sus4" if chord_type == "sus4" else
                        "dim" if chord_type == "dim" else
                        "aug" if chord_type == "aug" else "5"
                    )
                    best_chord = f"{NOTE_NAMES[root]}{suffix}"

        return best_chord

    def note_to_fret_string(self, note_name):
        """
        Convert a note name to possible (string, fret) positions on guitar.
        Returns list of (string_index, fret_index) tuples.
        string_index: 0=low E, 5=high e
        """
        # Standard tuning open string MIDI notes
        open_strings_midi = [40, 45, 50, 55, 59, 64]  # E2 A2 D3 G3 B3 E4

        if not note_name:
            return []

        # Parse note name
        note_base = note_name[:-1] if note_name[-1].isdigit() else note_name
        try:
            octave = int(note_name[-1])
        except ValueError:
            return []

        note_idx = NOTE_NAMES.index(note_base) if note_base in NOTE_NAMES else -1
        if note_idx == -1:
            return []

        target_midi = (octave + 1) * 12 + note_idx
        positions = []

        for string_idx, open_midi in enumerate(open_strings_midi):
            fret = target_midi - open_midi
            if 0 <= fret <= 12:
                positions.append((string_idx, fret))

        return positions
