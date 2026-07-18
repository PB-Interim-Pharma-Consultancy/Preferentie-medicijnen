"""
Adapter voor Menzis - Lijst preferente middelen.

Gebruikt `pdftotext -layout` (uit poppler-utils) om de kolomopmaak van
de PDF-tabel te behouden, en parsed daarna regel voor regel.

Gebruik:
    python adapter_menzis.py <pad_naar_menzis.pdf> <output.json>
"""
import re
import sys
import json
import subprocess
import tempfile
import pathlib

ROUTES = (
    "Oraal|Parenteraal|Rectaal|Cutaan|Nasaal|Vaginaal|Inhalatie|Inhalalie|"
    "Inhalatoe|Ter inhalatie|Sublinguaal|Intraveneus|Intramusculair|"
    "Subcutaan|Transdermaal|Oculair|Dermaal|Otisch|Lokaal|Oog"
)
PATTERN = re.compile(
    r"^(?P<stof>.+?)\s+(?P<route>" + ROUTES + r")\s+(?P<sterkte>.+?)\s+"
    r"(?P<lev>[A-Za-zÀ-ÿ0-9&\.\-/,\(\) ]+?)\s+(?P<zi>[\d/]+)\s+"
    r"(?P<start>\d{2}\.\d{2}\.\d{4})\s+(?P<eind>\d{2}\.\d{2}\.\d{4})"
    r"(?:\s+(?P<notes>.+))?$"
)
SKIP_PREFIXES = ("werkzame stof", "Lijst preferente", "versienummer", "product")


def extract_layout_text(pdf_path: str) -> list[str]:
    with tempfile.NamedTemporaryFile(suffix=".txt") as tmp:
        subprocess.run(
            ["pdftotext", "-layout", pdf_path, tmp.name],
            check=True, stderr=subprocess.DEVNULL,
        )
        return pathlib.Path(tmp.name).read_text(encoding="utf-8").splitlines()


def parse(pdf_path: str) -> list[dict]:
    raw_lines = extract_layout_text(pdf_path)

    lines = []
    for raw in raw_lines:
        line = raw.strip()
        if not line:
            continue
        if line.startswith(SKIP_PREFIXES) or "Z-indexnummer" in line or line.startswith("FO."):
            continue
        lines.append(line)

    records = []
    buf = ""
    for line in lines:
        buf = (buf + " " + line).strip() if buf else line
        m = PATTERN.match(buf)
        if m:
            records.append({
                "verzekeraar": "Menzis",
                "werkzame_stof": m.group("stof").strip(),
                "toedieningsweg": m.group("route").lower(),
                "sterkte": m.group("sterkte").strip(),
                "zi_nummer": m.group("zi"),
                "leverancier": m.group("lev").strip(),
                "start": m.group("start"),
                "eind": m.group("eind"),
            })
            buf = ""
        elif buf.count(" ") > 45:
            buf = ""
    return records


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    recs = parse(src)
    pathlib.Path(dst).write_text(json.dumps(recs, ensure_ascii=False), encoding="utf-8")
    print(f"Menzis: {len(recs)} records weggeschreven naar {dst}")
