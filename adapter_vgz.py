"""
Adapter voor VGZ - Lijst preferente middelen.

De header staat op rij 4 van het werkblad 'Blad1'. Werkzame stof en
sterkte zitten samen in één kolom en worden hier uit elkaar getrokken.

Gebruik:
    python adapter_vgz.py <pad_naar_vgz.xlsx> <output.json>
"""
import re
import sys
import json
import pathlib
import pandas as pd

COLUMNS = [
    "status", "artikelnummer", "artikelnaam", "conditie",
    "fabrikant", "stof_sterkte", "start", "eind", "atc",
]


def parse(xlsx_path: str) -> list[dict]:
    df = pd.read_excel(xlsx_path, sheet_name="Blad1", header=3)
    df = df.iloc[:, : len(COLUMNS)]
    df.columns = COLUMNS
    df = df.iloc[1:]  # eerste rij is de herhaalde headerregel
    df = df.dropna(subset=["artikelnaam"])

    records = []
    for _, row in df.iterrows():
        stof_sterkte = str(row["stof_sterkte"]).strip()
        m = re.match(r"^(?P<stof>.+?)\s+(?P<sterkte>[\d,\./A-Za-z\-][\d,\./A-Za-z\- ]*)$", stof_sterkte)
        stof = m.group("stof").strip() if m else stof_sterkte
        sterkte = m.group("sterkte").strip() if m else ""
        try:
            zi = str(int(row["artikelnummer"]))
        except (ValueError, TypeError):
            zi = str(row["artikelnummer"])
        records.append({
            "verzekeraar": "VGZ",
            "werkzame_stof": stof.title(),
            "sterkte": sterkte,
            "artikelnaam": str(row["artikelnaam"]).strip(),
            "leverancier": str(row["fabrikant"]).strip().title(),
            "zi_nummer": zi,
            "start": str(row["start"])[:10] if pd.notna(row["start"]) else "",
            "eind": str(row["eind"])[:10] if pd.notna(row["eind"]) else "",
        })
    return records


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    recs = parse(src)
    pathlib.Path(dst).write_text(json.dumps(recs, ensure_ascii=False), encoding="utf-8")
    print(f"VGZ: {len(recs)} records weggeschreven naar {dst}")
