"""
Adapter voor DSW - Preferente Geneesmiddelen.

DSW's PDF-tabel heeft kolommen: ZI-NR, STOFNAAM, ETIKETNAAM, LEVERANCIER,
INGANGSDATUM, EINDDATUM. Geen aparte sterkte/toedieningsweg-kolom - die
info zit in de ETIKETNAAM (bv. "... TABLET 80MG").

Gebruik:
    python adapter_dsw.py <pad_naar_dsw.pdf> <output.json>
"""
import re
import sys
import json
import subprocess
import tempfile
import pathlib


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
        line = raw.rstrip("\n")
        if line.startswith("\x0c"):
            line = line[1:]
        if not line.strip():
            continue
        if line.strip().startswith("ZI-NR") or line.strip().startswith("LIJST PREFERENTE"):
            continue
        if re.match(r"^\s*20\d{2}\s*-\s*20\d{2}\s*$", line):
            continue
        lines.append(line)

    grouped = []
    buf = None
    for line in lines:
        cols = re.split(r"\s{2,}", line.strip())
        starts_with_zi = bool(cols) and re.match(r"^\d{5,}$", cols[0])
        if starts_with_zi:
            if buf:
                grouped.append(buf)
            buf = {"zi": cols[0], "parts": cols[1:]}
        elif buf:
            buf["parts"].extend(cols)
    if buf:
        grouped.append(buf)

    records = []
    for r in grouped:
        parts = r["parts"]
        dates = [p for p in parts if re.match(r"^\d{2}-\d{2}-\d{4}$", p)]
        if len(dates) < 2:
            continue
        start, eind = dates[-2], dates[-1]
        rest = [p for p in parts if p not in (start, eind)]
        if len(rest) < 3:
            continue
        stof, etiket = rest[0], rest[1]
        lev = " ".join(rest[2:]).strip()
        records.append({
            "verzekeraar": "DSW",
            "werkzame_stof": stof.title(),
            "etiketnaam": etiket,
            "leverancier": lev,
            "zi_nummer": r["zi"],
            "start": start,
            "eind": eind,
        })
    return records


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    recs = parse(src)
    pathlib.Path(dst).write_text(json.dumps(recs, ensure_ascii=False), encoding="utf-8")
    print(f"DSW: {len(recs)} records weggeschreven naar {dst}")
