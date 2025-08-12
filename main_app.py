from __future__ import annotations

import io
import os
import streamlit as st

from config import AppSettings, DEFAULT_HEADER_ROWS
from writers.excel_writer import process_workbook

st.set_page_config(page_title="Berenschot Benchmark Codering (PoC)", layout="wide")

st.title("🔎 Benchmark Codering met AI — Proof of Concept")

st.markdown(
    "Upload hieronder **het codeschema** en **het klantbestand** (beide Excel). "
    "De app vult per relevante Oplegger-tabblad de kolommen **Codering AI**, **Argumentatie AI** en **Opmerkingen/aannames vanuit Berenschot**."
)

with st.sidebar:
    st.header("⚙️ Instellingen")
    provider = st.selectbox("LLM-provider", ["openai"], index=0, help="De architectuur is modulair: extra providers zijn eenvoudig toe te voegen.")
    model = st.text_input("Modelnaam", value="gpt-4o-mini")
    temperature = st.slider("Creativiteit (temperature)", 0.0, 1.0, 0.1, 0.1)
    top_k = st.slider("Aantal kandidaat-codes naar het model", 5, 40, 15, 1)
    dry_run = st.checkbox("Offline modus (geen LLM — eenvoudige heuristiek)", value=False)
    max_preview = st.number_input("Max. rijen in preview (per tab)", min_value=5, max_value=200, value=30, step=5)
    language = st.selectbox("Taal van de prompts", ["nl", "en"], index=0)
    st.caption("OpenAI-sleutel wordt automatisch gelezen uit **st.secrets['OPENAI_API_KEY']** of de omgevingsvariabele **OPENAI_API_KEY**.")

    st.subheader("Header-rij per tabblad (optioneel)")
    hr_pil = st.number_input("Oplegger PIL — header-rij", min_value=1, max_value=50, value=DEFAULT_HEADER_ROWS["oplegger pil"])
    hr_kos = st.number_input("Oplegger kosten — header-rij", min_value=1, max_value=50, value=DEFAULT_HEADER_ROWS["oplegger kosten"])
    hr_opb = st.number_input("Oplegger opbrengsten — header-rij", min_value=1, max_value=50, value=DEFAULT_HEADER_ROWS["oplegger opbrengsten"])

settings = AppSettings(
    provider_name=provider,
    model=model,
    temperature=temperature,
    top_k_codes=top_k,
    dry_run=dry_run,
    max_rows_preview=max_preview,
    system_language=language,
    header_rows_override={
        "oplegger pil": hr_pil,
        "oplegger kosten": hr_kos,
        "oplegger opbrengsten": hr_opb,
    },
)

schema_file = st.file_uploader("📘 Codeschema (Excel)", type=["xlsx", "xlsm"])
customer_file = st.file_uploader("🏢 Klantbestand (Excel)", type=["xlsx", "xlsm"])

colA, colB = st.columns(2)
with colA:
    preview_btn = st.button("🔍 Analyse & Preview")
with colB:
    run_btn = st.button("⚡ Verwerk & Download")

if preview_btn or run_btn:
    if not schema_file or not customer_file:
        st.error("Upload zowel het **codeschema** als het **klantbestand**.")
        st.stop()

    # Streamlit Cloud: secrets meenemen als env variabele voor de provider
    if "OPENAI_API_KEY" in st.secrets:
        os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

    # Verwerking
    with st.spinner("Bezig met verwerken…"):
        out_bytes = process_workbook(
            customer_file=customer_file,
            schema_file=schema_file,
            header_rows={
                "oplegger pil": settings.header_row_for("oplegger pil"),
                "oplegger kosten": settings.header_row_for("oplegger kosten"),
                "oplegger opbrengsten": settings.header_row_for("oplegger opbrengsten"),
            },
            provider_name=settings.provider_name,
            model=settings.model,
            temperature=settings.temperature,
            top_k_codes=settings.top_k_codes,
            dry_run=settings.dry_run,
            language=settings.system_language,
        )

    st.success("Verwerking gereed.")
    st.download_button(
        "📥 Download aangepast klantbestand",
        data=out_bytes,
        file_name="klantbestand_coderingsvoorstel.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

st.divider()
with st.expander("ℹ️ Uitleg & aannames"):
    st.markdown(
        """
**Belangrijke punten**

- **Modulair ontwerp**: de LLM-provider zit achter een interface (`llm_providers/base.py`). De OpenAI-implementatie staat in `llm_providers/openai_provider.py`. Een andere provider kan worden ingehangen door slechts één bestand toe te voegen of te wijzigen.
- **Schema-detectie**: het codeschema wordt uit 3 tabbladen gelezen (formatie/kosten/opbrengsten). Kolommen als *Code*, *Naam/Omschrijving*, *Toelichting/Criteria/Instructies* en optioneel *Overhead* en *Verduidelijkingsvraag* worden flexibel gedetecteerd op basis van kolomnamen.
- **Context**: per rij gebruikt de app alle beschikbare kolommen in het Oplegger-blad als context, exclusief de doelkolommen (Codering AI / Argumentatie AI / Opmerkingen…). Het model ziet daarnaast een *korte lijst* van top-\*k* kandidaat-codes op basis van fuzzy matching, wat de prompt compact houdt.
- **Uitvoer**: de 3 doelkolommen worden **aangemaakt** als ze ontbreken en anders **overschreven**. Andere data blijft ongewijzigd.
- **Verduidelijkende vraag**: wordt alleen toegevoegd als de modelrespons die bevat, bijvoorbeeld bij onvoldoende context of wanneer de gekozen code expliciet een aanvullende vraag volgens het schema vereist.
- **Offline modus**: zonder LLM (checkbox) wordt een eenvoudige, heuristische keuze gemaakt op basis van trefwoorden. Handig voor snelle demo's of als er (tijdelijk) geen API-sleutel beschikbaar is.
        """
    )
