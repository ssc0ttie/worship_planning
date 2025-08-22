import re

# Match a chord symbol (root + optional quality/extensions + optional slash bass)
CHORD_SYMBOL_RE = re.compile(
    r"(?<!\w)"  # not preceded by a word char
    r"("
    r"(?:[A-G][#b]?)"  # root note
    r"(?:maj|min|dim|aug|sus|add|m|M)?"  # optional quality (m, maj, min, sus, add, etc.)
    r"(?:[0-9]+)?"  # optional extension numbers (7, 9, 13…)
    r"(?:[#b][0-9]+)?"  # optional altered tones (#11, b9…)
    r"(?:/[A-G][#b]?)?"  # optional slash bass
    r")"
    r"(?!\w)"  # not followed by a word char
)


def _strip_meta(line: str) -> str:
    """Remove [Section] tags and (notes) from a chord line for cleaner detection."""
    line = re.sub(r"\[[^\]]*\]", "", line)  # [Intro], [Verse], etc.
    line = re.sub(r"\([^)]*\)", "", line)  # (play loud), (x2), etc.
    return line


def looks_like_chord_line(line: str) -> bool:
    """Heuristic: a 'chord line' is mostly chord tokens and spaces."""
    cleaned = _strip_meta(line).expandtabs(4)
    tokens = cleaned.strip().split()
    if not tokens:
        return False
    # Consider it a chord line if >= 70% of tokens look like chords and there are at least 2 chords
    chordish = [bool(CHORD_SYMBOL_RE.fullmatch(t)) for t in tokens]
    return sum(chordish) >= max(2, int(0.7 * len(tokens)))


def insert_chords_into_lyrics(chord_line: str, lyric_line: str) -> str:
    """
    Insert [Chord] tags into lyric_line based on the starting column of each chord in chord_line.
    Does not remove any lyric characters; only inserts.
    """
    chord_src = _strip_meta(chord_line).expandtabs(4)
    lyrics = lyric_line.expandtabs(4)

    # We insert into a working string and keep track of shift due to prior inserts
    out = lyrics
    shift = 0
    for m in CHORD_SYMBOL_RE.finditer(chord_src):
        chord = m.group(1)
        pos = m.start() + shift
        # Clamp position to the current string length (in case chord is beyond lyric length)
        pos = max(0, min(pos, len(out)))
        out = out[:pos] + f"[{chord}]" + out[pos:]
        shift += len(chord) + 2  # account for the newly inserted [..]
    return out


def ug_to_chordpro(text: str) -> str:
    """
    Convert Ultimate-Guitar-style text (chord line above lyric line) into ChordPro.
    - Keeps lines that aren't chord+lyric pairs unchanged.
    - Preserves [Section] lines as-is.
    """
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    lines = [ln.expandtabs(4) for ln in lines]

    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # If this is a chord line and the next line exists (likely lyrics), merge them
        if looks_like_chord_line(line) and i + 1 < len(lines):
            next_line = lines[i + 1]
            # Avoid merging two chord lines accidentally
            if not looks_like_chord_line(next_line):
                merged = insert_chords_into_lyrics(line, next_line)
                out.append(merged)
                i += 2
                continue
        # Otherwise keep the line as-is
        out.append(line)
        i += 1

    # Optional tidy: collapse excessive trailing spaces (but keep alignment within lines)
    return "\n".join(out).rstrip()
