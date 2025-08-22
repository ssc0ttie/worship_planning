import re

# --- Chord regex and utilities ---
CHORD_RE = re.compile(
    r"(?<!\w)"
    r"(?P<root>[A-G][b#]?)"
    r"(?P<qual>(?:maj|min|dim|aug|sus|add|m|M)?[0-9#b]*)?"
    r"(?P<bass>/[A-G][b#]?)?"
    r"(?!\w)"
)

# Chromatic scale (sharps)
NOTES_SHARP = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
NOTES_FLAT = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]


def normalize_note(note: str) -> str:
    """Normalize enharmonics (Db -> C#, Gb -> F#)."""
    if note in NOTES_SHARP:
        return note
    if note in NOTES_FLAT:
        return NOTES_SHARP[NOTES_FLAT.index(note)]
    return note


def transpose_note(note: str, steps: int) -> str:
    """Transpose a root/bass note by steps semitones."""
    note_norm = normalize_note(note)
    idx = NOTES_SHARP.index(note_norm)
    return NOTES_SHARP[(idx + steps) % 12]


def parse_chord(chord: str):
    """
    Split chord into (root, quality, bass).
    Handles:
      - Major, minor, diminished, augmented
      - sus chords
      - 7ths, 9ths, add chords
      - Slash chords (e.g., C/G)
    """
    # Regex explanation:
    #   ([A-G][#b]?)  -> root note
    #   (m|maj|dim|aug|sus[24]?|7|9|add\d+)?  -> optional quality
    #   (?:/([A-G][#b]?))?  -> optional bass note after slash
    m = re.fullmatch(
        r"([A-G][#b]?)(m|maj|dim|aug|sus[24]?|7|9|add\d+)?(?:/([A-G][#b]?))?", chord
    )
    if not m:
        return chord, "", ""
    root, qual, bass = m.groups()
    return root, qual or "", bass or ""


def transpose_chord(chord: str, steps: int) -> str:
    root, qual, bass = parse_chord(chord)
    if not root:
        return chord
    root_t = transpose_note(root, steps)
    if bass:
        bass_note = bass[1:]  # strip '/'
        bass_t = transpose_note(bass_note, steps)
        bass = "/" + bass_t
    return root_t + qual + bass


# --- Nashville number system ---
NASHVILLE_NUMBERS = {
    "C": 1,
    "C#": 2,
    "Db": 2,
    "D": 2,
    "D#": 3,
    "Eb": 3,
    "E": 3,
    "F": 4,
    "F#": 5,
    "Gb": 5,
    "G": 5,
    "G#": 6,
    "Ab": 6,
    "A": 6,
    "A#": 7,
    "Bb": 7,
    "B": 7,
}


def chord_to_nashville(chord: str, key: str) -> str:
    root, qual, bass = parse_chord(chord)
    if not root:
        return chord

    # Normalize root + key
    root = normalize_note(root)
    key = normalize_note(key)

    # Get degree relative to key
    key_idx = NOTES_SHARP.index(key)
    root_idx = NOTES_SHARP.index(root)
    interval = (root_idx - key_idx) % 12

    # Major scale intervals
    scale = [0, 2, 4, 5, 7, 9, 11]
    if interval in scale:
        degree = scale.index(interval) + 1
    else:
        degree = f"?{interval}"  # non-diatonic chord

    # Detect chord quality
    qual = qual or ""
    suffix = ""
    if qual.startswith("m") and not qual.startswith("maj"):
        suffix = "m"  # minor
    elif "dim" in qual:
        suffix = "dim"
    elif "aug" in qual:
        suffix = "aug"
    elif "sus" in qual:
        suffix = "sus" + "".join(filter(str.isdigit, qual))  # sus2/sus4

    out = str(degree) + suffix

    # Handle bass notes
    if bass:
        bass_note = bass[1:]
        bass_note_norm = normalize_note(bass_note)
        bass_idx = NOTES_SHARP.index(bass_note_norm)
        interval_bass = (bass_idx - key_idx) % 12
        if interval_bass in scale:
            degree_bass = scale.index(interval_bass) + 1
        else:
            degree_bass = f"?{interval_bass}"
        out += f"/{degree_bass}"

    return out


# --- Apply transformation to entire song ---
def transform_chordpro(text: str, transpose_steps=0, nashville=False, key=""):
    def repl(m):
        chord = m.group(1)
        out = chord
        if transpose_steps != 0:
            out = transpose_chord(out, transpose_steps)
        if nashville:
            out = chord_to_nashville(out, key)
        return f"[{out}]"

    return CHORD_RE.sub(repl, text)
