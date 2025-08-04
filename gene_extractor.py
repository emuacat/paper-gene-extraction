import re
from typing import List, Dict

def extract_genes(text: str) -> List[Dict]:
    """
    Find gene symbols in the text (with optional HGNC IDs).
    Returns a list of dictionaries for each unique gene:
      {"symbol": GENE_SYMBOL, "hgnc_id": HGNC_ID or None, "mentions": [(start_idx, end_idx), ...]}.
    """
    # Regex for explicit gene mention with HGNC ID in parentheses (e.g., TP53 (HGNC:11998))
    explicit_pattern = re.compile(r"\b([A-Z0-9-]+)\s*\([^)]*HGNC:(\d+)\)")
    # Regex for gene mention in context (e.g., "mutation in TP53" or "variants in TP53")
    context_pattern = re.compile(
        r"(?:(?:variant|variants|mutation|mutations|VUS|VUSs)\s+in\s+(?:the\s+|a\s+)?)"
        r"([A-Z0-9-]+)\b",
        flags=re.IGNORECASE
    )

    genes: Dict[str, Dict] = {}
    # Find all explicit gene mentions with HGNC IDs
    for match in explicit_pattern.finditer(text):
        symbol = match.group(1).upper()
        hgnc_id = int(match.group(2))
        sym_start = match.start(1)
        sym_end = match.end(1)
        if symbol not in genes:
            genes[symbol] = {"symbol": symbol, "hgnc_id": hgnc_id, "mentions": []}
        else:
            if genes[symbol]["hgnc_id"] is None:
                genes[symbol]["hgnc_id"] = hgnc_id
        genes[symbol]["mentions"].append((sym_start, sym_end))
    # Find gene mentions in mutation/variant context (no HGNC ID given in text)
    for match in context_pattern.finditer(text):
        symbol = match.group(1).upper()
        sym_start = match.start(1)
        sym_end = match.end(1)
        if symbol not in genes:
            genes[symbol] = {"symbol": symbol, "hgnc_id": None, "mentions": []}
        genes[symbol]["mentions"].append((sym_start, sym_end))

    # Convert genes dict to a list for output
    gene_list: List[Dict] = []
    for symbol, data in genes.items():
        gene_list.append({
            "symbol": symbol,
            "hgnc_id": data["hgnc_id"],
            "mentions": data["mentions"]
        })
    return gene_list
