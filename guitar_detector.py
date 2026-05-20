import cv2
import numpy as np


class GuitarDetector:
    """
    Detects guitar presence and fretboard location in a video frame.
    Uses a combination of:
    - HSV color masking for wood/lacquer tones
    - Canny + Hough line detection for fret lines (parallel horizontal lines)
    - Contour analysis for body shape
    """

    def __init__(self):
        # String colors for overlay (standard tuning E A D G B e)
        self.string_colors = [
            (0, 140, 255),   # E low  - orange
            (0, 200, 255),   # A      - yellow
            (0, 255, 150),   # D      - green
            (100, 255, 50),  # G      - lime
            (255, 200, 0),   # B      - cyan-blue
            (255, 100, 200), # e high - pink
        ]
        self.fret_count = 12  # detect up to 12 frets
        self._last_bounds = None
        self._stability_buffer = []
        self._buffer_size = 5

    def detect(self, frame):
        """
        Main detection pipeline.
        Returns dict with:
          - bounds: (x, y, w, h) or None
          - fretboard_corners: 4-point polygon or None
          - strings: list of (x1,y1,x2,y2) per string
          - frets: list of (x1,y1,x2,y2) per fret
          - confidence: 0.0-1.0
          - detected: bool
        """
        result = {
            "bounds": None,
            "fretboard_corners": None,
            "strings": [],
            "frets": [],
            "confidence": 0.0,
            "detected": False,
        }

        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # --- Step 1: Find candidate fretboard regions ---
        fretboard = self._detect_fretboard(frame, gray, hsv)
        if fretboard is None:
            result["detected"] = False
            result["bounds"] = self._last_bounds  # keep last known
            return result

        x, y, bw, bh = fretboard
        result["bounds"] = fretboard
        result["detected"] = True
        result["confidence"] = 0.75

        # Stability smoothing
        self._stability_buffer.append(fretboard)
        if len(self._stability_buffer) > self._buffer_size:
            self._stability_buffer.pop(0)
        smooth = self._smooth_bounds(self._stability_buffer)
        result["bounds"] = smooth
        self._last_bounds = smooth
        x, y, bw, bh = smooth

        # --- Step 2: Estimate string positions ---
        result["strings"] = self._estimate_strings(x, y, bw, bh)

        # --- Step 3: Estimate fret positions ---
        result["frets"] = self._estimate_frets(x, y, bw, bh)

        # --- Step 4: Fretboard corners for perspective ---
        result["fretboard_corners"] = np.array([
            [x, y], [x+bw, y], [x+bw, y+bh], [x, y+bh]
        ], dtype=np.float32)

        return result

    def _detect_fretboard(self, frame, gray, hsv):
        """
        Detect the fretboard using Hough line detection.
        Guitar fretboards have many near-parallel lines (frets).
        Returns (x, y, w, h) bounding box or None.
        """
        h, w = frame.shape[:2]

        # Blur and edge detect
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 30, 90)

        # Find line segments
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180,
            threshold=50,
            minLineLength=w // 8,
            maxLineGap=20,
        )

        if lines is None:
            # Fall back to contour-based detection
            return self._detect_by_contour(frame, gray)

        # Filter near-horizontal lines (frets) and near-vertical (strings)
        horizontal = []
        vertical = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = abs(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
            if angle < 20 or angle > 160:
                horizontal.append(line[0])
            elif 70 < angle < 110:
                vertical.append(line[0])

        # Need at least 3 horizontal lines for a fretboard
        if len(horizontal) < 3:
            return self._detect_by_contour(frame, gray)

        # Find bounding box of horizontal lines cluster
        all_y = [l[1] for l in horizontal] + [l[3] for l in horizontal]
        all_x = [l[0] for l in horizontal] + [l[2] for l in horizontal]

        if not all_y or not all_x:
            return None

        y_min = max(0, min(all_y) - 20)
        y_max = min(h, max(all_y) + 20)
        x_min = max(0, min(all_x) - 10)
        x_max = min(w, max(all_x) + 10)

        bw = x_max - x_min
        bh = y_max - y_min

        # Sanity check: fretboard is usually much wider than tall
        if bw < 80 or bh < 30:
            return None

        return (x_min, y_min, bw, bh)

    def _detect_by_contour(self, frame, gray):
        """Fallback: detect long narrow rectangle (neck/fretboard shape)"""
        h, w = frame.shape[:2]
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        best = None
        best_score = 0
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 5000:
                continue
            x, y, cw, ch = cv2.boundingRect(cnt)
            aspect = cw / max(ch, 1)
            # Guitar neck: very wide aspect ratio OR very tall (vertical position)
            if aspect > 3 or (0.1 < aspect < 0.4):
                score = area
                if score > best_score:
                    best_score = score
                    best = (x, y, cw, ch)

        return best

    def _estimate_strings(self, x, y, bw, bh):
        """Estimate 6 string positions evenly spaced within fretboard bounds"""
        strings = []
        padding = bh * 0.1
        for i in range(6):
            t = i / 5.0
            sy = int(y + padding + t * (bh - 2 * padding))
            strings.append((x, sy, x + bw, sy))
        return strings

    def _estimate_frets(self, x, y, bw, bh):
        """Estimate fret positions. Real frets use logarithmic spacing."""
        frets = []
        # Standard fret spacing ratio: each fret = prev / 17.817
        scale_length = bw
        pos = 0.0
        for i in range(self.fret_count + 1):
            fret_x = int(x + pos)
            if fret_x > x + bw:
                break
            frets.append((fret_x, y, fret_x, y + bh))
            remaining = scale_length - pos
            pos += remaining / 17.817

        return frets

    def _smooth_bounds(self, buffer):
        """Average bounding boxes for stability"""
        if not buffer:
            return None
        arr = np.array(buffer, dtype=np.float32)
        avg = np.mean(arr, axis=0).astype(int)
        return tuple(avg)

    def get_fret_string_position(self, bounds, fret_index, string_index):
        """
        Get pixel position for a specific fret/string intersection.
        string_index: 0=low E, 5=high e
        fret_index: 0=open, 1-12=fret
        """
        if bounds is None:
            return None
        x, y, bw, bh = bounds
        strings = self._estimate_strings(x, y, bw, bh)
        frets = self._estimate_frets(x, y, bw, bh)

        if string_index >= len(strings) or fret_index >= len(frets):
            return None

        sx = frets[fret_index][0] if fret_index < len(frets) else x + bw
        sy = strings[string_index][1]
        return (sx, sy)
