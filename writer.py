import csv
from typing import List
from models import GeneInfo

def write_csv(rows: List[GeneInfo], path: str) -> None:
    """Write the list of GeneInfo records to a CSV file at the given path."""
    headers = [
        "HGNC ID", "Gene Symbol", "HGNC Gene Name",
        "Gene Aliases", "hg38 Coordinates", "hg19 Coordinates", "Disease"
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for gene in rows:
            writer.writerow([
                gene.hgnc_id,
                gene.gene_symbol,
                gene.gene_name,
                gene.gene_aliases,
                gene.coord_hg38,
                gene.coord_hg19,
                gene.disease
            ])
