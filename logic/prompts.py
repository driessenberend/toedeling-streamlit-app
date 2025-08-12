from __future__ import annotations

from typing import List, Dict
from loaders.schema_loader import CodeRule
import textwrap


def build_system_prompt(language: str = "nl") -> str:
    """
    Bouwt de system-prompt die de LLM strak kadert.
    """
    if language == "nl":
        return textwrap.dedent(
            """
            Je bent een nauwkeurige data-analist die regels toepast voor het coderen van
            formatie (PIL), kosten en opbrengsten in de zorg (VVT, GGZ, GHZ).
            Je volgt het codeschema strikt en motiveert je keuze kort en bondig (maximaal 2 zinnen).
            Als informatie ontbreekt of het schema dat vraagt, geef je ÉÉN verduidelijkende vraag.

            Antwoord ALTIJD in JSON met exact deze velden:
            {
              "code": "<exacte code uit lijst>",
              "argumentatie": "<max 2 zinnen>",
              "vraag": null of "<één vraag>",
              "confidence": <getal tussen 0 en 1>
            }
            """
        ).strip()
    else:
        return textwrap.dedent(
            """
            You are a meticulous analyst applying a coding scheme for staffing (PIL),
            costs, and revenues in Dutch healthcare (VVT, GGZ, GHZ).
            Follow the scheme strictly. Provide a concise rationale (max 2 sentences).
            If information is missing or the scheme requires it, include ONE clarifying question.

            ALWAYS answer in JSON with exactly these fields:
            {
              "code": "<exact code from list>",
              "argumentatie": "<max 2 sentences>",
              "vraag": null or "<one question>",
              "confidence": <number between 0 and 1>
            }
            """
        ).strip()


def build_user_prompt(row_context: Dict[str, str], candidates: List[CodeRule], category: str) -> str:
    """
    Gebruikersprompt: compacte rijcontext + shortlist met kandidaat-codes.
    """
    # Compacte context
    ctx_lines = []
    for k, v in row_context.items():
        if v is None or str(v).strip() == "":
            continue
        sv = str(v)
        if len(sv) > 300:
            sv = sv[:300] + "…"
        ctx_lines.append(f"- {k}: {sv}")
    ctx_block = "\n".join(ctx_lines) if ctx_lines else "- (geen contextwaarden gevonden)"

    # Kandidaten samenvatten
    cand_lines = []
    for r in candidates:
        desc = (r.description or r.instructions or "").strip()
        if len(desc) > 280:
            desc = desc[:280] + "…"
        name_part = f"{r.name}" if r.name else ""
        extra = f" | instructies: {r.instructions}" if r.instructions else ""
        if len(extra) > 160:
            extra = extra[:160] + "…"
        cand_lines.append(f"* [{r.code}] {name_part} — {desc}{extra}")
    cands_block = "\n".join(cand_lines)

    prompt = f"""
Categorie: {category}

Context van de rij (kolom: waarde):
{ctx_block}

Mogelijke codes (kandidaten, kies exact één die het beste past):
{cands_block}

Regels:
- Geef JSON met velden: code (exacte code-string uit lijst), argumentatie (max 2 zinnen), vraag (of null), confidence (0..1).
- Stel enkel een verduidelijkingsvraag als de context onvoldoende is ÓF het bij de gekozen code expliciet hoort (via instructies).
- Als je sterk twijfelt tussen 2 codes, kies de beste en benoem de twijfel kort in de argumentatie.
- Geen extra tekst buiten het JSON.
"""
    return prompt.strip()
