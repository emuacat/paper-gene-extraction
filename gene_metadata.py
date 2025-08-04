import re
import requests
import spacy
from typing import List, Dict, Set, Optional, Tuple

# Load the SciSpaCy model for disease NER (BC5CDR: detects disease and chemical terms)
try:
    nlp_disease = spacy.load("en_ner_bc5cdr_md")
except Exception as e:
    raise RuntimeError(
        "SciSpaCy model 'en_ner_bc5cdr_md' is not installed.\n"
        "Install with:\n"
        "  pip install scispacy\n"
        "  pip install https://s3-us-west-2.amazonaws.com/allenai-scispacy/models/en_ner_bc5cdr_md-0.5.0.tar.gz"
    ) from e

# Helper: determine if a disease term is too generic to be meaningful
GENERIC_PARTS = {
    # Generic qualifiers that make a term non-specific
    "single", "system", "single-system", "multi", "multisystem", "multi-system",
    "systemic", "common", "rare", "genetic", "hereditary", "familial", "unknown",
    # Extended generic qualifiers to filter out terms like "autosomal recessive", "tall stature", etc.
    "autosomal", "dominant", "recessive", "tall", "stature", "short"
}

def _is_generic(term: str) -> bool:
    """
    Check if a disease term is too generic or descriptive to be meaningful as a specific disease name.
    Such terms are not linked as specific associations.
    """
    orig = term.strip()
    t = orig.lower()
    # Special-case: If the term appears to be an uppercase acronym followed by "syndrome" (e.g., "SHORT syndrome"),
    # do not consider it generic (likely a named syndrome).
    if orig.endswith(" syndrome"):
        prefix = orig[:-len(" syndrome")].strip(" ,;:-")
        if prefix and prefix.isupper():
            return False
    # Exact generic words (disease, syndrome, disorder by themselves)
    if t in {"disease", "syndrome", "disorder"}:
        return True
    # Terms ending with disease/syndrome/disorder preceded by only generic qualifiers
    for kw in ("disease", "syndrome", "disorder"):
        if t.endswith(kw):
            prefix = t.rsplit(kw, 1)[0].strip(" -;,")
            if prefix:
                parts = re.split(r"[\s-]+", prefix)
                if all(part in GENERIC_PARTS for part in parts):
                    return True
            else:
                return True
    # If the entire term is composed of one or two generic descriptive words
    # (e.g., "single-system", "autosomal recessive", "tall stature", "short stature")
    parts = re.split(r"[\s-]+", t)
    if len(parts) <= 2 and all(part in GENERIC_PARTS for part in parts):
        return True
    return False

# Helper: validate disease name against known databases
def is_valid_disease_name(term: str) -> bool:
    """
    Validate if the given term is a known disease name by checking against multiple databases.
    The term is considered valid if it is found in at least one recognized database or ontology.
    """
    query = term.strip()
    if not query:
        return False
    # Check in NCBI MedGen database
    try:
        resp = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={"db": "medgen", "term": query}, timeout=5
        )
        if resp.status_code == 200 and '<Id>' in resp.text:
            return True
    except Exception:
        pass
    # Check in NCBI MeSH database
    try:
        resp = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={"db": "mesh", "term": f"{query}[MeSH Terms]"}, timeout=5
        )
        if resp.status_code == 200 and '<Id>' in resp.text:
            return True
    except Exception:
        pass
    # Check in EBI OLS (Disease Ontology)
    try:
        resp = requests.get(
            "https://www.ebi.ac.uk/ols/api/search",
            params={"q": query, "ontology": "doid"}, timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get('response', {}).get('numFound', 0) > 0:
                return True
    except Exception:
        pass
    # If none of the sources confirmed the term, consider it invalid
    return False

# HGNC REST API helper functions
def _hgnc_api(path: str) -> dict:
    resp = requests.get(f"https://rest.genenames.org/{path}",
                        headers={"Accept": "application/json"}, timeout=10)
    resp.raise_for_status()
    return resp.json()

def fetch_hgnc_by_symbol(symbol: str) -> dict:
    """Fetch HGNC record by gene symbol."""
    try:
        data = _hgnc_api(f"fetch/symbol/{symbol}")
    except Exception:
        return {}
    docs = data.get("response", {}).get("docs", [])
    return docs[0] if docs else {}

def fetch_hgnc_by_id(hgnc_id: str) -> dict:
    """Fetch HGNC record by HGNC ID (e.g. 'HGNC:618')."""
    if not hgnc_id:
        return {}
    if not str(hgnc_id).startswith("HGNC:"):
        hgnc_id = f"HGNC:{hgnc_id}"
    try:
        data = _hgnc_api(f"fetch/hgnc_id/{hgnc_id}")
    except Exception:
        return {}
    docs = data.get("response", {}).get("docs", [])
    return docs[0] if docs else {}

def fetch_ncbi_aliases(entrez_id: str) -> List[str]:
    """
    Fetch additional gene aliases from NCBI using Entrez Gene ID via esummary.
    Returns a list of alias names (empty if none or on failure).
    """
    url = (f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
           f"?db=gene&id={entrez_id}&retmode=json")
    try:
        data = requests.get(url, timeout=10).json()
    except Exception:
        return []
    result = data.get("result", {}).get(str(entrez_id), {})
    aliases_str = result.get("otheraliases", "")
    if not aliases_str:
        return []
    # Split aliases by comma and strip whitespace
    aliases = [alias.strip() for alias in aliases_str.split(",") if alias.strip()]
    return aliases

# Ensembl REST API for coordinates on GRCh38 (hg38) and GRCh37 (hg19)
def fetch_coordinates_by_ensembl(ensembl_id: str, assembly: str = "hg38") -> str:
    """
    Fetch genomic coordinates for a given Ensembl gene ID and assembly.
    Returns a string "chr<chrom>:<start>-<end>" or empty string if not found.
    """
    base_url = "https://rest.ensembl.org"
    if assembly.lower() == "hg19" or assembly.lower() == "grch37":
        base_url = "https://grch37.rest.ensembl.org"
    url = f"{base_url}/lookup/id/{ensembl_id}?content-type=application/json"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code != 200:
            return ""
        data = resp.json()
    except Exception:
        return ""
    if not data:
        return ""
    seq_region = data.get("seq_region_name")
    start = data.get("start")
    end = data.get("end")
    if seq_region and start and end:
        return f"chr{seq_region}:{start}-{end}"
    return ""

def fetch_coordinates_by_symbol(symbol: str) -> Tuple[str, str]:
    """
    Fetch hg38 and hg19 coordinates by gene symbol (fallback method).
    Returns a tuple (hg38_coords, hg19_coords), or ("", "") if not found.
    """
    coord_hg38 = fetch_coordinates_by_ensembl(symbol, assembly="hg38")
    coord_hg19 = fetch_coordinates_by_ensembl(symbol, assembly="hg19")
    return coord_hg38, coord_hg19

def associate_diseases(genes: List[Dict], doc) -> None:
    """
    Annotate each gene in the list with diseases mentioned in proximity.
    Uses the parsed spaCy document (with disease NER) to find associations.
    """
    sentences = list(doc.sents)
    for ent in doc.ents:
        if ent.label_ != "DISEASE":
            continue
        disease_name = ent.text.strip().strip('.,;:')
        if not disease_name or _is_generic(disease_name):
            continue
        if not is_valid_disease_name(disease_name):
            continue
        # Identify genes mentioned in the same sentence as this disease
        sent_start = ent.sent.start_char
        sent_end = ent.sent.end_char
        genes_in_sentence: List[Dict] = []
        for gene in genes:
            # Check if any mention of the gene lies within this sentence span
            for (m_start, m_end) in gene["mentions"]:
                if m_start >= sent_start and m_end <= sent_end:
                    genes_in_sentence.append(gene)
                    break
        if genes_in_sentence:
            # If one or more genes are in the same sentence, link disease to the closest gene
            closest_gene = None
            min_distance = float('inf')
            disease_center = (ent.start_char + ent.end_char) / 2
            for gene in genes_in_sentence:
                # Use the first mention of the gene in this sentence for distance calculation
                for (m_start, m_end) in gene["mentions"]:
                    if m_start >= sent_start and m_end <= sent_end:
                        gene_center = (m_start + m_end) / 2
                        dist = abs(gene_center - disease_center)
                        if dist < min_distance:
                            min_distance = dist
                            closest_gene = gene
                        break
            if closest_gene is not None:
                closest_gene.setdefault("diseases", set()).add(disease_name)
        else:
            # No gene in the same sentence: check context in adjacent sentences
            sent_index = None
            for i, s in enumerate(sentences):
                if s.start_char == sent_start:
                    sent_index = i
                    break
            if sent_index is None:
                continue
            linked_gene: Optional[Dict] = None
            # Check previous sentence for exactly one gene mention
            if sent_index > 0:
                prev_sent = sentences[sent_index - 1]
                p_start, p_end = prev_sent.start_char, prev_sent.end_char
                prev_genes = {gene["symbol"] for gene in genes
                              for (ms, me) in gene["mentions"] if ms >= p_start and me <= p_end}
                if len(prev_genes) == 1:
                    # Exactly one unique gene in previous sentence
                    sym = prev_genes.pop()
                    linked_gene = next(g for g in genes if g["symbol"] == sym)
            # If not linked yet, check next sentence for exactly one gene mention
            if linked_gene is None and sent_index < len(sentences) - 1:
                next_sent = sentences[sent_index + 1]
                n_start, n_end = next_sent.start_char, next_sent.end_char
                next_genes = {gene["symbol"] for gene in genes
                              for (ms, me) in gene["mentions"] if ms >= n_start and me <= n_end}
                if len(next_genes) == 1:
                    sym = next_genes.pop()
                    linked_gene = next(g for g in genes if g["symbol"] == sym)
            if linked_gene:
                linked_gene.setdefault("diseases", set()).add(disease_name)

def fetch_gene_metadata(symbol: str, hgnc_id: Optional[int]) -> Optional[Dict]:
    """
    Fetch metadata for the given gene from HGNC and NCBI, and genomic coordinates.
    Returns a dictionary with gene information, or None if not found.
    """
    sym = symbol.upper()
    # Fetch HGNC record by symbol, or by HGNC ID if symbol lookup fails
    record = fetch_hgnc_by_symbol(sym)
    if not record:
        record = fetch_hgnc_by_id(hgnc_id if hgnc_id else "")
    if not record or "symbol" not in record:
        return None

    # Core info from HGNC
    hgnc_id_str = record.get("hgnc_id", "")
    name = record.get("name", "")
    # Gather aliases from HGNC fields (alias_symbol, prev_symbol, alias_name)
    aliases_set: Set[str] = set()
    for field in ("alias_symbol", "prev_symbol", "alias_name"):
        val = record.get(field)
        if isinstance(val, list):
            aliases_set.update(val)
        elif isinstance(val, str) and val:
            aliases_set.add(val)
    # Get Entrez ID and fetch additional aliases from NCBI if available
    entrez_id = record.get("entrez_id")
    if entrez_id:
        aliases_set.update(fetch_ncbi_aliases(str(entrez_id)))
    # Remove aliases identical to the symbol (case-insensitive match)
    aliases_set = {alias for alias in aliases_set if alias.strip().upper() != sym}
    aliases = "; ".join(sorted(aliases_set))

    # Fetch genomic coordinates using Ensembl gene ID if possible
    ensembl_id = record.get("ensembl_gene_id")
    coord_hg38 = coord_hg19 = ""
    if ensembl_id:
        coord_hg38 = fetch_coordinates_by_ensembl(ensembl_id, assembly="hg38")
        coord_hg19 = fetch_coordinates_by_ensembl(ensembl_id, assembly="hg19")
    if not coord_hg38 and not coord_hg19:
        # Fall back to symbol lookup if Ensembl ID is not available or fails
        coord_hg38, coord_hg19 = fetch_coordinates_by_symbol(sym)

    return {
        "hgnc_id": hgnc_id_str,
        "symbol": sym,
        "name": name,
        "aliases": aliases,
        "coord_hg38": coord_hg38,
        "coord_hg19": coord_hg19
    }
