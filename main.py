import argparse
from article_retriever import get_article_text
from gene_extractor import extract_genes
from gene_metadata import fetch_gene_metadata, associate_diseases, nlp_disease
from models import GeneInfo
from writer import write_csv

def main():
    parser = argparse.ArgumentParser(description="Extract gene-disease metadata from a PubMed/PMC article.")
    parser.add_argument("-i", "--input", required=True,
                        help="PMID or PMCID of the article (e.g. 38790019 or PMC11127317)")
    parser.add_argument("-o", "--output", required=True, help="Path to output CSV file")
    args = parser.parse_args()

    print("Fetching article text...")
    text = get_article_text(args.input)

    print("Extracting gene mentions...")
    genes = extract_genes(text)
    if not genes:
        print("No gene symbols found in the article.")
        return

    print("Running disease named-entity recognition on article text...")
    doc = nlp_disease(text)  # Parse text with SciSpaCy disease NER model

    print("Linking diseases to genes...")
    associate_diseases(genes, doc)

    # Prepare results, including only genes that have at least one associated disease
    results = []
    for gene in genes:
        # If the gene has no diseases linked, skip it
        disease_set = gene.get("diseases", set())
        if not disease_set:
            continue
        # Fetch gene metadata (name, aliases, coordinates)
        gene_data = fetch_gene_metadata(gene["symbol"], gene.get("hgnc_id"))
        if not gene_data:
            continue  # skip if gene not found in HGNC
        # Create GeneInfo object with all required fields
        gene_info = GeneInfo(
            hgnc_id     = gene_data["hgnc_id"],
            gene_symbol = gene_data["symbol"],
            gene_name   = gene_data["name"],
            gene_aliases= gene_data["aliases"],
            coord_hg38  = gene_data["coord_hg38"],
            coord_hg19  = gene_data["coord_hg19"],
            disease     = "; ".join(sorted(disease_set))
        )
        results.append(gene_info)

    if not results:
        print("No gene-disease associations found in the article.")
        return

    # Write results to CSV
    write_csv(results, args.output)
    print(f"✅ Success: {len(results)} gene(s) with disease associations written to {args.output}")

if __name__ == "__main__":
    main()
