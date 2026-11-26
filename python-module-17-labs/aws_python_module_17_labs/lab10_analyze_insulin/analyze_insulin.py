"""Lab 10: clean a FASTA/GenBank-style preproinsulin sequence and split it."""

from pathlib import Path
import re

RAW = Path(__file__).with_name("preproinsulin-seq.txt")
OUTPUT = Path(__file__).parent


def clean_sequence(raw_text: str) -> str:
    """Remove the ORIGIN marker, numbering, whitespace, and end marker."""
    body = raw_text.replace("ORIGIN", "").replace("//", "")
    body = re.sub(r"\d+", "", body)
    sequence = re.sub(r"\s+", "", body).lower()
    if not sequence.isalpha():
        raise ValueError("Sequence contains characters other than letters")
    return sequence


def main() -> None:
    sequence = clean_sequence(RAW.read_text(encoding="utf-8"))
    if len(sequence) != 110:
        raise ValueError(f"Expected 110 amino-acid letters; found {len(sequence)}")

    fragments = {
        "lsinsulin-seq-clean.txt": sequence[0:24],
        "binsulin-seq-clean.txt": sequence[24:54],
        "cinsulin-seq-clean.txt": sequence[54:89],
        "ainsulin-seq-clean.txt": sequence[89:110],
    }
    (OUTPUT / "preproinsulin-seq-clean.txt").write_text(sequence + "\n", encoding="utf-8")
    for filename, fragment in fragments.items():
        (OUTPUT / filename).write_text(fragment + "\n", encoding="utf-8")
        print(f"{filename}: {len(fragment)} characters")

    insulin = fragments["binsulin-seq-clean.txt"].strip() + fragments["ainsulin-seq-clean.txt"].strip()
    print(f"Preproinsulin length: {len(sequence)}")
    print(f"Mature insulin length (B + A chains): {len(insulin)}")


if __name__ == "__main__":
    main()
