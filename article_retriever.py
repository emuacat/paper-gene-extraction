import requests
import re
import xml.etree.ElementTree as ET

def get_article_text(identifier: str) -> str:
    """
    Retrieve the main BODY text of an open-access article given a PMID or PMCID.

    Parameters
    ----------
    identifier : str
        A PMID (e.g. 'PMID38790019' or '38790019') or a PMCID (e.g. 'PMC11127317').

    Returns
    -------
    str
        Plain text of the article’s <body> section. Front-matter (title, authors, etc.)
        and back-matter (references, acknowledgements, etc.) are excluded. An empty
        string is returned if the XML cannot be parsed or no <body> tag is found.
    """
    pmcid: str | None = None
    pmid: str | None = None
    ident = identifier.strip()

    # ───────────────────────── Identify accession ──────────────────────────
    if ident.upper().startswith("PMC"):
        pmcid = ident
    elif ident.upper().startswith("PMID"):
        pmid = ident[4:]
    elif ident.isdigit():
        pmid = ident
    else:
        raise ValueError("Identifier must be a PMID or PMCID (e.g. 'PMID1234' or 'PMC1234').")

    # ───────────────────── Map PMID → PMCID via Europe PMC ─────────────────
    if pmcid is None:
        search_url = (
            "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
            f"?query=EXT_ID:{pmid}%20AND%20SRC:MED&format=json"
        )
        resp = requests.get(search_url, timeout=10)
        resp.raise_for_status()
        results = resp.json().get("resultList", {}).get("result", [])
        if not results:
            raise RuntimeError(f"No Europe PMC match for PMID {pmid}.")
        pmcid = results[0].get("pmcid")
        if not pmcid:
            raise RuntimeError(f"No PMCID found for PMID {pmid}.")

    # ─────────────────────── Download full-text XML ────────────────────────
    xml_url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"
    resp = requests.get(xml_url, timeout=10)
    resp.raise_for_status()
    xml_content = resp.text

    # ───────────────────── Extract only the <body> content ─────────────────
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError:
        # Malformed XML – return the raw text fallback (stripped of tags)
        return re.sub(r"<[^>]+>", "", xml_content)

    body_elem = next((elem for elem in root.iter() if elem.tag.endswith("body")), None)
    if body_elem is None:
        return ""  # No body tag present (e.g. abstract-only record)

    # Collect all descendant text nodes inside <body>
    body_text = "".join(body_elem.itertext())

    # Normalize whitespace: collapse multiple spaces/newlines
    text = re.sub(r"\s+", " ", body_text).strip()
    return text
