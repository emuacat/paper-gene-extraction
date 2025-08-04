from dataclasses import dataclass

@dataclass
class GeneInfo:
    hgnc_id: str
    gene_symbol: str
    gene_name: str
    gene_aliases: str
    coord_hg38: str
    coord_hg19: str
    disease: str
