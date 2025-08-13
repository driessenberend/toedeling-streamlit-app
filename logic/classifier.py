from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Optional, Any, Tuple

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
    Fuzzy matching UITGESCHAKELD: geef het volledige codeschema door.
    We houden de functie-naam aan voor compatibiliteit met writers/excel_writer.py.
    """
    return list(rules)


def build_row_text(context: Dict[str, Any]) -> str:
    """
    Niet gebruikt wanneer fuzzy uit staat; houden we aan voor compatibiliteit.
    """
    return ""


def pick_code_with_llm(
    llm: LLMClient,
    *,
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.0
) -> ClassificationResult:
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
    Eenvoudige offline fallback blijft beschikbaar voor demo/no-API situaties.
    (Geen fuzzy; alleen zeer simpele token-overlap.)
    """
    text = " ".join(str(v).lower() for v in context.values() if v is not None)
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
