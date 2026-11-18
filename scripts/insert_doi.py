"""Insert a minted Zenodo DOI into the paper and CITATION.cff.

Run after the Zenodo deposit exists:

    .venv/bin/python scripts/insert_doi.py 10.5281/zenodo.NNNNNNNN

Idempotent: running it twice with the same DOI changes nothing.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: The paper promises no DOI: its artifact statement names the repository and
#: the release, and says nothing archival, because an unkept promise in a
#: posted preprint is worse than silence. So there is nothing to *replace* --
#: the DOI sentence is appended after this anchor. Matched as a regex because
#: LaTeX source is hard-wrapped, so the sentence spans a line break.
ANCHOR_RE = re.compile(r"which\s+is\s+the\s+revision\s+this\s+paper\s+was\s+built\s+from\.")

#: Older spelling, kept so this still works on an unrevised checkout.
PLACEHOLDER = "ZENODO_DOI_PLACEHOLDER"


def main(doi: str) -> int:
    if not re.fullmatch(r"10\.5281/zenodo\.\d+", doi):
        print(f"not a Zenodo DOI: {doi}")
        return 1

    tex = ROOT / "paper" / "fap.tex"
    body = tex.read_text()
    escaped = doi.replace("_", r"\_")
    if escaped in body or doi in body:
        print("  paper already carries this DOI")
    elif ANCHOR_RE.search(body):
        tex.write_text(ANCHOR_RE.sub(
            lambda m: m.group(0) + f" The release is archived at DOI \\texttt{{{escaped}}}.",
            body, count=1))
        print(f"  paper/fap.tex <- {doi}")
    elif PLACEHOLDER in body:
        tex.write_text(body.replace(PLACEHOLDER, escaped))
        print(f"  paper/fap.tex <- {doi}")
    else:
        print("  ERROR: no anchor, no placeholder and no matching DOI")
        return 1

    cff = ROOT / "CITATION.cff"
    text = cff.read_text()
    if "\ndoi:" in text:
        text = re.sub(r"\ndoi: .*", f"\ndoi: {doi}", text)
    else:
        # Zenodo's reader is strict: doi goes on its own unquoted line after
        # license, and date-released must stay unquoted or the whole file is
        # rejected with "Citation metadata load failed".
        text = text.replace("\nlicense: MIT\n", f"\nlicense: MIT\ndoi: {doi}\n")
    cff.write_text(text)
    print(f"  CITATION.cff <- {doi}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
