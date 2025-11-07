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
    """Parse chord using the same pattern as CHORD_RE."""
    match = CHORD_RE.match(chord)
    if not match:
        return chord, "", ""

    root = match.group("root")
    qual = match.group("qual") or ""
    bass = match.group("bass") or ""

    # Remove leading slash from bass if present
    if bass and bass.startswith("/"):
        bass = bass[1:]

    return root, qual, bass


def transpose_chord(chord: str, steps: int) -> str:
    root, qual, bass = parse_chord(chord)
    if not root or root not in NOTES_SHARP + NOTES_FLAT:
        return chord

    root_t = transpose_note(root, steps)

    if bass:
        bass_t = transpose_note(bass, steps)
        return root_t + qual + "/" + bass_t

    else:
        return root_t + qual


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
    if not root or root not in NOTES_SHARP + NOTES_FLAT:
        return chord

    # Normalize root + key
    root_norm = normalize_note(root)
    key_norm = normalize_note(key)

    # Get degree relative to key
    key_idx = NOTES_SHARP.index(key_norm)
    root_idx = NOTES_SHARP.index(root_norm)
    interval = (root_idx - key_idx) % 12

    # Major scale intervals
    scale = [0, 2, 4, 5, 7, 9, 11]
    if interval in scale:
        degree = scale.index(interval) + 1
    else:
        degree = f"?{interval}"

    # Preserve the original quality
    out = str(degree) + qual

    # Handle bass notes
    if bass:
        bass_norm = normalize_note(bass)
        bass_idx = NOTES_SHARP.index(bass_norm)
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
        chord = m.group(0)
        out = chord
        if transpose_steps != 0:
            out = transpose_chord(out, transpose_steps)
        if nashville:
            out = chord_to_nashville(out, key)
        return f"[{out}]"

    return CHORD_RE.sub(repl, text)


def remove_chords_from_chordpro(chordpro_text):
    """
    Remove chords from ChordPro format, leaving only lyrics.
    Handles chord notations like [C], [G/B], etc.
    """
    import re

    # Remove chord notations [chord]
    lyrics_only = re.sub(r"\[.*?\]", "", chordpro_text)

    # Clean up extra spaces and empty lines
    lines = lyrics_only.split("\n")
    cleaned_lines = []

    for line in lines:
        # Remove lines that are only whitespace or very short (likely chord lines)
        stripped_line = line.strip()
        if stripped_line and len(stripped_line) > 2:  # Adjust threshold as needed
            cleaned_lines.append(stripped_line)

    return "\n".join(cleaned_lines)
