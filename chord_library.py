"""
ChordLibrary - Complete guitar chord database with fingering positions
Each chord has: name, fret positions per string, finger assignments, barre info
"""


class ChordLibrary:
    """
    Comprehensive chord database.
    Format per chord entry:
      "frets": list of 6 ints (string 1=low E to 6=high e)
               -1 = muted, 0 = open, 1-12 = fret number
      "fingers": list of 6 ints (0=none, 1-4=finger)
      "barre": (fret, from_string, to_string) or None
      "name": display name
    """

    def __init__(self):
        self.chords = self._build_library()

    def get(self, chord_name):
        """Get chord data by name. Returns dict or None."""
        return self.chords.get(chord_name)

    def get_all_names(self):
        return list(self.chords.keys())

    def search(self, query):
        """Search chords by partial name"""
        q = query.lower()
        return [k for k in self.chords if q in k.lower()]

    def _build_library(self):
        chords = {}

        # ── OPEN CHORDS ──
        chords["E"] = {
            "name": "E Major", "frets": [0, 2, 2, 1, 0, 0],
            "fingers": [0, 2, 3, 1, 0, 0], "barre": None,
            "notes": ["E", "B", "E", "G#", "B", "E"]
        }
        chords["Em"] = {
            "name": "E Minor", "frets": [0, 2, 2, 0, 0, 0],
            "fingers": [0, 2, 3, 0, 0, 0], "barre": None,
            "notes": ["E", "B", "E", "G", "B", "E"]
        }
        chords["A"] = {
            "name": "A Major", "frets": [-1, 0, 2, 2, 2, 0],
            "fingers": [0, 0, 1, 2, 3, 0], "barre": None,
            "notes": ["x", "A", "E", "A", "C#", "E"]
        }
        chords["Am"] = {
            "name": "A Minor", "frets": [-1, 0, 2, 2, 1, 0],
            "fingers": [0, 0, 2, 3, 1, 0], "barre": None,
            "notes": ["x", "A", "E", "A", "C", "E"]
        }
        chords["D"] = {
            "name": "D Major", "frets": [-1, -1, 0, 2, 3, 2],
            "fingers": [0, 0, 0, 1, 3, 2], "barre": None,
            "notes": ["x", "x", "D", "A", "D", "F#"]
        }
        chords["Dm"] = {
            "name": "D Minor", "frets": [-1, -1, 0, 2, 3, 1],
            "fingers": [0, 0, 0, 2, 3, 1], "barre": None,
            "notes": ["x", "x", "D", "A", "D", "F"]
        }
        chords["G"] = {
            "name": "G Major", "frets": [3, 2, 0, 0, 0, 3],
            "fingers": [2, 1, 0, 0, 0, 4], "barre": None,
            "notes": ["G", "B", "G", "D", "G", "B"] # simplified
        }
        chords["C"] = {
            "name": "C Major", "frets": [-1, 3, 2, 0, 1, 0],
            "fingers": [0, 3, 2, 0, 1, 0], "barre": None,
            "notes": ["x", "C", "E", "G", "C", "E"]
        }
        chords["F"] = {
            "name": "F Major", "frets": [1, 1, 2, 3, 3, 1],
            "fingers": [1, 1, 2, 3, 4, 1], "barre": (1, 0, 5),
            "notes": ["F", "C", "F", "A", "C", "F"]
        }
        chords["B"] = {
            "name": "B Major", "frets": [-1, 2, 4, 4, 4, 2],
            "fingers": [0, 1, 2, 3, 4, 1], "barre": (2, 1, 5),
            "notes": ["x", "B", "F#", "B", "D#", "F#"]
        }
        chords["Bm"] = {
            "name": "B Minor", "frets": [-1, 2, 4, 4, 3, 2],
            "fingers": [0, 1, 3, 4, 2, 1], "barre": (2, 1, 5),
            "notes": ["x", "B", "F#", "B", "D", "F#"]
        }

        # ── BARRE CHORDS ──
        chords["F#m"] = {
            "name": "F# Minor", "frets": [2, 4, 4, 2, 2, 2],
            "fingers": [1, 3, 4, 1, 1, 1], "barre": (2, 0, 5),
            "notes": ["F#", "C#", "F#", "A", "C#", "F#"]
        }
        chords["C#m"] = {
            "name": "C# Minor", "frets": [-1, 4, 6, 6, 5, 4],
            "fingers": [0, 1, 3, 4, 2, 1], "barre": (4, 1, 5),
            "notes": ["x", "C#", "G#", "C#", "E", "G#"]
        }
        chords["G#m"] = {
            "name": "G# Minor", "frets": [4, 6, 6, 4, 4, 4],
            "fingers": [1, 3, 4, 1, 1, 1], "barre": (4, 0, 5),
            "notes": ["G#", "D#", "G#", "B", "D#", "G#"]
        }
        chords["Eb"] = {
            "name": "Eb Major", "frets": [-1, -1, 1, 3, 4, 3],
            "fingers": [0, 0, 1, 2, 4, 3], "barre": None,
            "notes": ["x", "x", "Eb", "Bb", "Eb", "G"]
        }
        chords["Bb"] = {
            "name": "Bb Major", "frets": [-1, 1, 3, 3, 3, 1],
            "fingers": [0, 1, 2, 3, 4, 1], "barre": (1, 1, 5),
            "notes": ["x", "Bb", "F", "Bb", "D", "F"]
        }

        # ── SEVENTH CHORDS ──
        chords["G7"] = {
            "name": "G7", "frets": [3, 2, 0, 0, 0, 1],
            "fingers": [3, 2, 0, 0, 0, 1], "barre": None,
            "notes": ["G", "B", "G", "D", "G", "F"]
        }
        chords["C7"] = {
            "name": "C7", "frets": [-1, 3, 2, 3, 1, 0],
            "fingers": [0, 3, 2, 4, 1, 0], "barre": None,
            "notes": ["x", "C", "E", "Bb", "C", "E"]
        }
        chords["D7"] = {
            "name": "D7", "frets": [-1, -1, 0, 2, 1, 2],
            "fingers": [0, 0, 0, 2, 1, 3], "barre": None,
            "notes": ["x", "x", "D", "A", "C", "F#"]
        }
        chords["A7"] = {
            "name": "A7", "frets": [-1, 0, 2, 0, 2, 0],
            "fingers": [0, 0, 2, 0, 3, 0], "barre": None,
            "notes": ["x", "A", "E", "G", "C#", "E"]
        }
        chords["E7"] = {
            "name": "E7", "frets": [0, 2, 0, 1, 0, 0],
            "fingers": [0, 2, 0, 1, 0, 0], "barre": None,
            "notes": ["E", "B", "D", "G#", "B", "E"]
        }
        chords["B7"] = {
            "name": "B7", "frets": [-1, 2, 1, 2, 0, 2],
            "fingers": [0, 2, 1, 3, 0, 4], "barre": None,
            "notes": ["x", "B", "F#", "A#", "D#", "F#"]
        }

        # ── POWER CHORDS ──
        chords["E5"] = {
            "name": "E5 Power", "frets": [0, 2, 2, -1, -1, -1],
            "fingers": [0, 1, 2, 0, 0, 0], "barre": None,
            "notes": ["E", "B", "E", "x", "x", "x"]
        }
        chords["A5"] = {
            "name": "A5 Power", "frets": [-1, 0, 2, 2, -1, -1],
            "fingers": [0, 0, 1, 2, 0, 0], "barre": None,
            "notes": ["x", "A", "E", "A", "x", "x"]
        }
        chords["D5"] = {
            "name": "D5 Power", "frets": [-1, -1, 0, 2, 3, -1],
            "fingers": [0, 0, 0, 1, 3, 0], "barre": None,
            "notes": ["x", "x", "D", "A", "D", "x"]
        }
        chords["G5"] = {
            "name": "G5 Power", "frets": [3, 5, 5, -1, -1, -1],
            "fingers": [1, 3, 4, 0, 0, 0], "barre": None,
            "notes": ["G", "D", "G", "x", "x", "x"]
        }

        # ── SUSPENDED ──
        chords["Dsus2"] = {
            "name": "Dsus2", "frets": [-1, -1, 0, 2, 3, 0],
            "fingers": [0, 0, 0, 1, 3, 0], "barre": None,
            "notes": ["x", "x", "D", "A", "E", "D"] # simplified
        }
        chords["Dsus4"] = {
            "name": "Dsus4", "frets": [-1, -1, 0, 2, 3, 3],
            "fingers": [0, 0, 0, 1, 2, 3], "barre": None,
            "notes": ["x", "x", "D", "A", "D", "G"]
        }
        chords["Asus2"] = {
            "name": "Asus2", "frets": [-1, 0, 2, 2, 0, 0],
            "fingers": [0, 0, 2, 3, 0, 0], "barre": None,
            "notes": ["x", "A", "E", "A", "B", "E"] # simplified
        }
        chords["Asus4"] = {
            "name": "Asus4", "frets": [-1, 0, 2, 2, 3, 0],
            "fingers": [0, 0, 1, 2, 3, 0], "barre": None,
            "notes": ["x", "A", "E", "A", "D", "E"] # simplified
        }

        return chords
