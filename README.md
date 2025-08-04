# Gene Metadata from Rare Disease Exome Reanalysis

## Summary

This repository contains a script and data derived from a 2024 rare disease study in *Orphanet Journal of Rare Diseases*. The study, [**Diagnostic yield of exome and genome sequencing after non-diagnostic multi-gene panels in patients with single-system diseases**](https://pmc.ncbi.nlm.nih.gov/articles/PMC11127317/), reanalyzed exome (ES) and genome (GS) sequencing data for patients who previously had negative results from multi-gene panel tests. As a result, additional pathogenic variants were identified in a few cases, including variants in the genes **RRAGD**, **COL4A3**, **NPHS2**, and **HNF1A**. This repository’s script extracts metadata for these genes and other relevant genes mentioned in the context (such as **APOL1** and **HERC2**), compiling key information like official names, aliases, genomic coordinates, and associated diseases into a CSV file. This data aims to facilitate further analysis or integration into databases of genes implicated in rare diseases.

## Script Explanation

### `main.py`
Coordinates the full pipeline. It accepts a PubMed ID or PMC ID, fetches the article text, extracts gene and disease mentions, enriches each gene with metadata (HGNC ID, aliases, genomic coordinates), and writes the results to a CSV.

### `article_retriever.py`
Downloads the body text of a publication using the Europe PMC API. Converts a given PMID or PMCID to the corresponding full-text XML, then parses and returns the main article body (excluding references, abstracts, etc.).

### `gene_extractor.py`
Uses regular expressions and context patterns to identify gene mentions. Recognizes both explicitly tagged genes (e.g., `COL4A3 (HGNC:2204)`) and contextual mentions (e.g., "HERC2"). Records gene symbols and mention positions.

### `gene_metadata.py`
Retrieves gene information via HGNC, Ensembl, and NCBI APIs. Gathers:
- HGNC ID and full name
- Aliases (from HGNC + NCBI Entrez)
- Genomic coordinates on hg38 and hg19 (from Ensembl)
- Nearby disease terms in the article using SciSpaCy’s disease NER

Combines all data into a structured record per gene.

**Usage:**

Run the script (no arguments needed, as the gene list is built-in):

    $  python main.py -i PMC11127317 -o output_gene_metadata.cs

This will fetch the gene data and create an output file `output_gene_metadata.csv` in the current directory.

## CSV Output Description

The output CSV (`output_gene_metadata.csv`) contains the following columns for each gene:

- **HGNC ID** – The unique identifier assigned to the gene by the HUGO Gene Nomenclature Committee (e.g., *HGNC:618* for APOL1).
- **Gene Symbol** – The official gene symbol (short abbreviation, e.g., *APOL1*).
- **HGNC Gene Name** – The full name/description of the gene as recorded by HGNC (e.g., *apolipoprotein L1*).
- **Gene Aliases** – Alternative names or symbols that have been used for the gene (synonyms, previous names, or abbreviations).
- **hg38 Coordinates** – The gene’s location on the human genome (chromosome and start-end positions) based on the GRCh38/hg38 reference assembly.
- **hg19 Coordinates** – The gene’s location on the older GRCh37/hg19 assembly, which is provided for reference or compatibility with legacy data.
- **Disease** – Known disease(s) or conditions associated with mutations or variants in this gene. Multiple entries are separated by semicolons. (These associations were derived from clinical databases and the article’s context. For example, *APOL1* risk variants are known to contribute to kidney disease, *RRAGD* variants can cause a syndrome with dilated cardiomyopathy, tubulopathy, and hypomagnesemia, *COL4A3* is implicated in Alport syndrome and certain kidney lesions, etc.)

Users can open the CSV file to examine the detailed information. This structured data can be useful for researchers or clinicians looking into gene-disease relationships highlighted by the study.

## Database Schema

For integrators who wish to import this data into a database, a simple schema is proposed to normalize the information. The diagram below (see `dbschema.png`) illustrates one possible relational model:

![Database Schema](dbschema.png)

In this schema:
- A **Gene** table (keyed by HGNC ID or gene symbol) stores core information about each gene (such as name and genome coordinates).
- An **Alias** table lists gene aliases, with each record linked to a gene entry (one-to-many relationship, since a gene can have multiple aliases).
- A **Disease** table lists disease associations, each linked to a gene (one gene can be associated with multiple diseases; likewise, a disease may involve multiple genes, but here we focus on one-directional listing per gene as extracted).

This structure avoids redundancy by not repeating gene info for each alias or disease. The provided `dbschema.png` visualizes these tables and their relationships.

## Known Limitations

- **NER Coverage:** The named entity recognition model may miss some specific medical terms or acronyms. For example, the acronym MODY (which stands for Maturity Onset Diabetes of the Young
pmc.ncbi.nlm.nih.gov, a type of hereditary diabetes) was mentioned in the article but not recognized as a disease term by the model. As a result, a known association (HNF1A → MODY) did not appear in the output CSV. Future improvements could include custom dictionaries or better NER models to catch such cases.
- **Data Sources:** The metadata is dependent on external databases (e.g., HGNC, OMIM). If those sources update or if the APIs change, the script might need adjustments. Also, disease association data might not be exhaustive; the script captures major known associations, but some nuanced or newly discovered links could be missing.
- **Context and Specificity** The extraction links genes to diseases based on textual co-occurrence, which might not capture complex relationships perfectly. In the output, some disease entries are very general or include database identifiers (e.g., an OMIM number was extracted as if it were a disease name). These quirks reflect the limits of straightforward text parsing. A more advanced approach could use relation extraction models to ensure the gene–disease links are precise and filter out irrelevant terms.
- **Testing and Validation:** The script was tested on the specific genes from the study. Its robustness for a larger or different set of genes (especially if including those with very large numbers of aliases or complex data) hasn’t been extensively evaluated. Minor adjustments might be needed for edge cases.

## Installation Requirements

To run the script and reproduce the data extraction, you will need:

- **Python 3.8 or newer** – the pipeline was developed and tested on Python ≥ 3.8.  
- **Required Python libraries**  
  - `requests` – HTTP calls to external APIs (e.g., MyGene.info).  
  - `pandas` – data wrangling and CSV writing.  
  - *(Optional)* `json` – part of the Python standard library; used for parsing API responses.  
  - `spacy` **and** `scispacy` – biomedical NER (gene & disease recognition).  
    - Example model: `en_ner_bc5cdr_md` (Disease).  
    - Can incoperate more advanced models like hugging face BioBertRelationGenesDiseases in the future 
  - *(Optional)* `mygene` – light wrapper for the MyGene.info API; simplifies HGNC/Entrez look-ups compared with raw `requests` calls.

> **Tip:** All exact version pins are listed in `requirements.txt`; run  
> `pip install -r requirements.txt` to pull everything in one shot.

You can install the required libraries using pip 


Ensure your environment has internet access when running the script, as it needs to contact remote databases.


Users interested in the data or script can clone the repository and run the script to regenerate the CSV, or modify the script to adapt to similar projects or new gene lists.


