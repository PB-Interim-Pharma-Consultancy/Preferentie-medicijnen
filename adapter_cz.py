"""
Adapter voor CZ - Lijst voorkeursgeneesmiddelen.

CZ levert dit bestand aan als .pdf, maar de bron die wij ontvingen was
in feite een zip-archief met daarin een los .txt-bestand per pagina
(al platte tekst, geen scan). Dit script pakt dat archief uit en
parsed elke regel naar het gemeenschappelijke schema.

Gebruik:
    python adapter_cz.py <pad_naar_cz_bestand.pdf> <output.json>
"""
import re
import sys
import json
import zipfile
import tempfile
import pathlib

ROUTES = (
    "oraal|dermaal|oculair|inhalatie|transdermaal|subcutaan|intramusculair|"
    "intraveneus|rectaal|nasaal|otisch|aerosol|vaginaal|sublinguaal|"
    "parenteraal|cutaan"
)
PATTERN = re.compile(
    r"^(?P<stof>.+?)\s+(?P<route>" + ROUTES + r")\s+(?P<sterkte>.+?)\s+"
    r"(?P<prk>\d+(?:\s*-\s*\d+)*)\s+(?P<start>\d{1,2}-\d{1,2}-\d{4})\s+"
    r"(?P<eind>\d{1,2}-\d{1,2}-\d{4})\s+(?P<zi>\d+)\s+(?P<lev>.+?)\s*$"
)
SKIP_PREFIXES = (
    "Werkzame stof", "Lijst voorkeursgeneesmiddelen", "Binnen een groep",
    "kunnen deze", "voorkeursgeneesmiddel", "*",
)


def extract_text_lines(source_path: str) -> list[str]:
    """CZ-bestand is een zip met 1.txt, 2.txt, ... per pagina."""
    lines: list[str] = []
    with zipfile.ZipFile(source_path) as zf:
        txt_names = sorted(
            (n for n in zf.namelist() if n.endswith(".txt")),
            key=lambda n: int(re.sub(r"\D", "", n) or 0),
        )
        for name in txt_names:
            content = zf.read(name).decode("utf-8", errors="replace")
            lines.extend(content.splitlines())
    return lines


def parse(source_path: str) -> list[dict]:
    raw_lines = extract_text_lines(source_path)

    lines = []
    for line in raw_lines:
        line = line.strip().rstrip("\r")
        if not line or line.startswith(SKIP_PREFIXES):
            continue
        if re.match(r"^\d{2}-\d{2}-\d{4}$", line):
            continue
        lines.append(line)

    records = []
    buf = ""
    for line in lines:
        buf = (buf + " " + line).strip() if buf else line
        m = PATTERN.match(buf)
        if m:
            records.append({
                "verzekeraar": "CZ",
                "werkzame_stof": m.group("stof").strip(),
                "toedieningsweg": m.group("route"),
                "sterkte": m.group("sterkte").strip(),
                "zi_nummer": m.group("zi"),
                "leverancier": m.group("lev").strip(),
                "start": m.group("start"),
                "eind": m.group("eind"),
            })
            buf = ""
        elif buf.count(" ") > 40:
            # Waarschijnlijk een regel die we niet konden matchen; laten vallen
            buf = ""
    return records


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    recs = parse(src)
    pathlib.Path(dst).write_text(json.dumps(recs, ensure_ascii=False), encoding="utf-8")
    print(f"CZ: {len(recs)} records weggeschreven naar {dst}")
