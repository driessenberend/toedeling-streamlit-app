from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Optional
import pandas as pd

@dataclass
class CodeRule:
    code: str
    name: str
    description: str
    instructions: str = ""
    overhead_flag: Optional[str] = None
    clarifying_hint: Optional[str] = None

def _first_col_match(cols: List[str], *candidates: str) -> Optional[str]:
    for cand in candidates:
        for c in cols:
            if cand.lower() == str(c).lower():
                return c
        for c in cols:
            if cand.lower() in str(c).lower():
                return c
    return None

def parse_code_sheet(df: pd.DataFrame) -> List[CodeRule]:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    cols = list(df.columns)

    col_code = _first_col_match(cols, "Code", "code")
    col_name = _first_col_match(cols, "Naam", "Omschrijving", "Omschrijving code", "Code-naam", "Naam code")
    col_desc = _first_col_match(cols, "Beschrijving", "Toelichting", "Omschrijving (lang)", "Uitleg", "Argumentatie")
    col_instr = _first_col_match(cols, "Instructies", "Richtlijnen", "Criteria", "Toedeling", "Regels", "Kader")
    col_overh = _first_col_match(cols, "Overhead", "Overhead of primair", "Overhead/Primair", "Primair/Overhead")
    col_hint = _first_col_match(cols, "Vraag", "Verduidelijkingsvraag", "Vraaghint")

    rules: List[CodeRule] = []
    for _, row in df.iterrows():
        code = str(row.get(col_code, "")).strip() if col_code else ""
        name = str(row.get(col_name, "")).strip() if col_name else ""
        description = str(row.get(col_desc, "")).strip() if col_desc else ""
        instructions = str(row.get(col_instr, "")).strip() if col_instr else ""
        overhead_flag = str(row.get(col_overh, "")).strip() if col_overh else None
        clarifying_hint = str(row.get(col_hint, "")).strip() if col_hint else None
        if not code and not name and not description:
            continue
        rules.append(CodeRule(
            code=code, name=name, description=description,
            instructions=instructions, overhead_flag=overhead_flag,
            clarifying_hint=clarifying_hint
        ))
    return rules

def load_codeschema_excel(path_or_file) -> Dict[str, List[CodeRule]]:
    xls = pd.ExcelFile(path_or_file)
    sheets = {s.lower(): s for s in xls.sheet_names}
    out: Dict[str, List[CodeRule]] = {}

    def grab(name_candidates: List[str]) -> Optional[str]:
        for cand in name_candidates:
            for k, v in sheets.items():
                if cand in k:
                    return v
        return None

    m_form = grab(["formatie", "pil", "formatiecodes"])
    m_kost = grab(["kosten", "kostencodes"])
    m_opbr = grab(["opbrengst", "opbrengsten", "opbrengstencodes"])

    if m_form:
        out["formatie"] = parse_code_sheet(pd.read_excel(xls, m_form))
    if m_kost:
        out["kosten"] = parse_code_sheet(pd.read_excel(xls, m_kost))
    if m_opbr:
        out["opbrengsten"] = parse_code_sheet(pd.read_excel(xls, m_opbr))

    return out
