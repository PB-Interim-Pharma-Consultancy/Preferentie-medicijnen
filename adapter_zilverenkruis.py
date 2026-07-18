"""
Adapter voor Zilveren Kruis - Lijst preferente geneesmiddelen.

Werkblad 'Lijst website', header op rij 4.

Gebruik:
    python adapter_zilverenkruis.py <pad_naar_zk.xlsx> <output.json>
"""
import sys
import json
import pathlib
import pandas as pd

COLUMNS = [
    "SST_id", "Stof", "Sterkte", "Toepassing", "Leverancier",
    "ZI_nummer", "Begin", "Eind", "ATC",
    "PRK1", "PRK2", "PRK3", "PRK4", "PRK5", "PRK6", "PRK7",
]


def parse(xlsx_path: str) -> list[dict]:
    df = pd.read_excel(xlsx_path, sheet_name="Lijst website", header=3)
    df.columns = COLUMNS
    df = df.dropna(subset=["Stof"])
    df = df[df["SST_id"] != "SST_id"]  # herhaalde headerregel eruit

    records = []
    for _, row in df.iterrows():
        stof = str(row["Stof"]).strip()
        if not stof:
            continue
        records.append({
            "verzekeraar": "Zilveren Kruis",
            "werkzame_stof": stof.title(),
            "toedieningsweg": str(row["Toepassing"]).strip().lower(),
            "sterkte": str(row["Sterkte"]).strip(),
            "zi_nummer": str(row["ZI_nummer"]).strip(),
            "leverancier": str(row["Leverancier"]).strip(),
            "start": str(row["Begin"])[:10] if pd.notna(row["Begin"]) else "",
            "eind": str(row["Eind"])[:10] if pd.notna(row["Eind"]) else "",
        })
    return records


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    recs = parse(src)
    pathlib.Path(dst).write_text(json.dumps(recs, ensure_ascii=False), encoding="utf-8")
    print(f"Zilveren Kruis: {len(recs)} records weggeschreven naar {dst}")
