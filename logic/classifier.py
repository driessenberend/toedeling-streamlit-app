from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Optional, Any, Tuple
from rapidfuzz import process, fuzz

from loaders.schema_loader import CodeRule
from llm_providers.base import LLMClient
from utils.json_utils import extract_first_json_block


@dataclass
class ClassificationResult:
    code: Optional[str]
    argumentatie: Optional[str]
    vraag: Optional[str]
    confidence: float


def rank_candidates(text: str, rules: List[CodeRule], top_k: int = 15) -> List[CodeRule]:
    """
    Rankt codes met fuzzy matching op basis van rijcontext; retourneert top_k CodeRule's.
    """
    corpus = {i: f"{r.code} {r.name} {r.description} {r.instructions}".strip()
              for i, r in enumerate(rules)}
    # WRatio is robuust voor volgorde/varianten
    scored = process.extract(text or "", corpus, scorer=fuzz.WRatio, limit=top_k)
    ids = [idx for _, _, idx in scored]
    return [rules[i] for i in ids]


def build_row_text(context: Dict[str, Any]) -> str:
    """
    Zet rijcontext om naar een platte tekst voor fuzzy match.
    """
    parts = []
    for k, v in context.items():
        if v is None:
            continue
        sv = str(v).strip()
        if not sv:
            continue
        parts.append(f"{k}: {sv}")
    return " | ".join(parts)


def pick_code_with_llm(
    llm: LLMClient,
    *,
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.0
) -> ClassificationResult:
    """
    Roept de LLM aan en parse't het JSON-antwoord.
    """
    raw = llm.classify(model=model, system_prompt=system_prompt, user_prompt=user_prompt, temperature=temperature)
    data = extract_first_json_block(raw) or {}
    code = data.get("code")
    arg = data.get("argumentatie")
    vraag = data.get("vraag")
    conf = data.get("confidence", 0.0)
    try:
        conf = float(conf)
    except Exception:
        conf = 0.0

    # Trim argumentatie tot max ~2 zinnen
    if isinstance(arg, str):
        sentences = [s.strip() for s in arg.replace("\n", " ").split(".") if s.strip()]
        arg = ". ".join(sentences[:2])
        if arg and not arg.endswith("."):
            arg += "."

    if isinstance(vraag, str):
        vraag = vraag.strip() or None

    return ClassificationResult(code=code, argumentatie=arg, vraag=vraag, confidence=conf)


def simple_rules_fallback(context: Dict[str, Any], rules: List[CodeRule]) -> ClassificationResult:
    """
    Eenvoudige fallback zonder LLM:
    - telt token-overlap tussen context en naam/beschrijving/instructies
    - kiest de beste; bij geen overlap -> geen code + vraag om toelichting
    """
    text = (build_row_text(context) or "").lower()
    best: Optional[Tuple[CodeRule, int]] = None

    for r in rules:
        score = 0
        for token in (r.name or "").lower().split():
            if token and token in text:
                score += 1
        for token in (r.description or "").lower().split():
            if token and token in text:
                score += 1
        for token in (r.instructions or "").lower().split():
            if token and token in text:
                score += 1
        if best is None or score > best[1]:
            best = (r, score)

    if best and best[1] > 0:
        r = best[0]
        return ClassificationResult(
            code=r.code,
            argumentatie=f"Gekozen op basis van overeenkomende termen met '{r.name}'.",
            vraag=None,
            confidence=0.3,
        )

    return ClassificationResult(
        code=None,
        argumentatie="Onvoldoende context om een code te kiezen.",
        vraag="Kunt u toelichten welke code het beste past volgens uw interne rubricering?",
        confidence=0.0,
    )
