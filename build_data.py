"""
Bouwt data.json door alle vijf adapters te draaien op de brondata en de
resultaten samen te voegen.

Bij een maandelijkse update: nieuwe bronbestanden in `bronbestanden/`
zetten (zelfde bestandsnamen, of de paden hieronder aanpassen) en dit
script opnieuw draaien.

Gebruik:
    python build_data.py
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "adapters"))

import adapter_cz
import adapter_menzis
import adapter_dsw
import adapter_vgz
import adapter_zilverenkruis

BRONBESTANDEN = pathlib.Path("bronbestanden")

SOURCES = [
    (adapter_cz, BRONBESTANDEN / "lijstvoorkeursgeneesmiddelen_CZ.pdf"),
    (adapter_menzis, BRONBESTANDEN / "Menzis_Lijst_preferente_middelen_2026.pdf"),
    (adapter_dsw, BRONBESTANDEN / "DSW_Preferente_Geneesmiddelen_voor_2026_2027.pdf"),
    (adapter_vgz, BRONBESTANDEN / "VGZ_Lijst_preferente_middelen_vanaf_1_juli_2026.xlsx"),
    (adapter_zilverenkruis, BRONBESTANDEN / "preferent_assortiment_met_artikelnummers_2026_Zilveren_Kruis.xlsx"),
]


def main():
    all_records = []
    for adapter, path in SOURCES:
        if not path.exists():
            print(f"WAARSCHUWING: bronbestand niet gevonden, wordt overgeslagen: {path}")
            continue
        records = adapter.parse(str(path))
        print(f"{path.name}: {len(records)} records")
        all_records.extend(records)

    out_path = pathlib.Path("data.json")
    out_path.write_text(json.dumps(all_records, ensure_ascii=False), encoding="utf-8")
    print(f"\nTotaal: {len(all_records)} records weggeschreven naar {out_path.resolve()}")


if __name__ == "__main__":
    main()
