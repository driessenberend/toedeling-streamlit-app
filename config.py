"""
Algemene configuratie en constanten.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

# Standaard model (kan in UI worden aangepast)
DEFAULT_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

# Mapping van sheetnaam -> type codes
SHEET_CODEMAP = {
    "oplegger pil": "formatie",
    "oplegger kosten": "kosten",
    "oplegger opbrengsten": "opbrengsten",
}

# Standaard header-rij per sheet (1-indexed in Excel UI; intern gebruiken we 1-indexed)
DEFAULT_HEADER_ROWS = {
    "oplegger pil": 1,
    "oplegger kosten": 4,
    "oplegger opbrengsten": 4,
}

# Doelkolommen die we moeten invullen
TARGET_COLUMNS = {
    "codering_ai": "Codering AI",
    "argumentatie_ai": "Argumentatie AI",
    "opmerkingen": "Opmerkingen/aannames vanuit Berenschot",
}

# Kolomnamen die vaak context geven (heuristiek)
COMMON_CONTEXT_COLS = [
    # PIL
    "Personeelsnummer", "Functienaam", "Kostenplaatsnummer", "Kostenplaatsomschrijving",
    "Afdeling / locatie", "Team", "Datum indienst", "Datum uitdienst",
    "Totaal verloonde salarislasten incl. (x€1000)", "Gemiddelde bezetting (fte)",
    "Codering eerdere deelname", "Codering huidige deelname", "Overhead of primair proces?",
    "NZI-naam",
    # Kosten / Opbrengsten
    "Grootboekrekening", "Omschrijving kosten", "Omschrijving opbrengsten", "Kostenplaatsnummer",
    "Kostenplaatsomschrijving", "Kosten (x €1.000)", "Opbrengst (x €1.000)",
    "Codering concept", "Codering definitief", "Codering-naam",
]

@dataclass
class AppSettings:
    provider_name: str = "openai"
    model: str = DEFAULT_MODEL
    temperature: float = 0.1
    top_k_codes: int = 15
    dry_run: bool = False
    max_rows_preview: int = 30
    system_language: str = "nl"  # nl of en
    header_rows_override: Optional[dict] = None

    def header_row_for(self, sheet_name: str) -> int:
        name = sheet_name.strip().lower()
        override = (self.header_rows_override or {})
        if name in override:
            return override[name]
        for key, val in DEFAULT_HEADER_ROWS.items():
            if key in name:
                return val
        return 1
