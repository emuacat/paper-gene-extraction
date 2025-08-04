# Gene Metadata from Rare Disease Exome Reanalysis

## Summary

This repository contains a script and data derived from a 2024 rare disease study in *Orphanet Journal of Rare Diseases*. The study, [**Diagnostic yield of exome and genome sequencing after non-diagnostic multi-gene panels in patients with single-system diseases**](https://pmc.ncbi.nlm.nih.gov/articles/PMC11127317/), reanalyzed exome (ES) and genome (GS) sequencing data for patients who previously had negative results from multi-gene panel tests. As a result, additional pathogenic variants were identified in a few cases, including variants in the genes **RRAGD**, **COL4A3**, **NPHS2**, and **HNF1A**. This repository’s script extracts metadata for these genes and other relevant genes mentioned in the context (such as *APOL1* and *HERC2*), compiling key information like official names, aliases, genomic coordinates, and associated diseases into a CSV file. This data aims to facilitate further analysis or integration into databases of genes implicated in rare diseases.

## Script Explanation

The main script (e.g., `gene_metadata_extractor.py`) automates the retrieval of gene information and outputs it in a structured format. It performs the following steps:

1. **Gene List Preparation:** A list of target gene symbols is defined based on the study findings and context (for this project, the genes of interest are *APOL1*, *RRAGD*, *COL4A3*, *NPHS2*, *HNF1A*, and *HERC2* as identified from the article and related discussions).
2. **Data Retrieval:** For each gene symbol, the script fetches comprehensive metadata from authoritative databases:
   - **HGNC**: to retrieve the gene’s official full name, HGNC ID, and known aliases/synonyms.
   - **Genomic Coordinates**: the chromosomal location of the gene is obtained for both the GRCh38/hg38 and GRCh37/hg19 human genome assemblies (ensuring backward compatibility with older data).
   - **Disease Associations**: known disease or syndrome associations for each gene are gathered. These may come from sources such as OMIM or literature references (for example, *RRAGD* is linked to familial kidney tubulopathy and hypomagnesemia:contentReference[oaicite:1]{index=1}, *COL4A3* mutations cause Alport syndrome, etc.). Where available, multiple diseases are listed.
3. **Output Generation:** The script compiles the collected data into a tabular format and writes it to a CSV file (`output_gene_metadata.csv`). Each row corresponds to one gene and its metadata.

The script uses Python’s `requests` library to call web APIs (for HGNC and other sources) and `json/pandas` to handle and format the data. Comments in the code explain each step for clarity and easy maintenance.

**Usage:**

Run the script (no arguments needed, as the gene list is built-in):

    $ python gene_metadata_extractor.py

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

- **Scope of Genes:** The current list of genes is manually curated from a single publication’s findings. It may not include all genes of potential interest in similar contexts. For a different article or a broader study, the script would need an updated gene list or an automated way to identify gene mentions in text.
- **Data Sources:** The metadata is dependent on external databases (e.g., HGNC, OMIM). If those sources update or if the APIs change, the script might need adjustments. Also, disease association data might not be exhaustive; the script captures major known associations, but some nuanced or newly discovered links could be missing.
- **Automation of Gene Extraction:** The process of identifying which genes from the article to include was not fully automated. In this project, we predetermined the genes based on the study’s results. Future improvements could involve text mining of the article to auto-detect gene symbols.
- **No Live Database Integration:** The output is a static CSV and an example schema. There is no live database or search functionality included in this repository. Users must import the CSV into their own data systems or use the provided script as a starting point for further development (e.g., building a web app or database).
- **Testing and Validation:** The script was tested on the specific genes from the study. Its robustness for a larger or different set of genes (especially if including those with very large numbers of aliases or complex data) hasn’t been extensively evaluated. Minor adjustments might be needed for edge cases.

## Installation Requirements

To run the script and reproduce the data extraction, you will need:

- **Python 3.8+** – The code was developed and tested with Python 3 (it should run on Python 3.8 or newer).
- **Required Python Libraries:**  
  - `requests` – for making HTTP requests to external APIs (to fetch gene info).  
  - `pandas` – for managing data and writing the CSV output.  
  - *(Optional)* `json` is part of Python’s standard library (used for parsing API responses).  

You can install the required libraries using pip if you don’t have them:

    pip install requests pandas

Ensure your environment has internet access when running the script, as it needs to contact remote databases.

## File Structure

The repository is organized as follows:

- **`README.md`** – This documentation file, providing an overview of the project.
- **`gene_metadata_extractor.py`** – The main Python script that retrieves gene data and generates the CSV. (The name of the script might differ if you choose to rename it; ensure to update usage instructions accordingly.)
- **`output_gene_metadata.csv`** – The CSV file produced by the script, containing the compiled gene metadata. This file is included in the repository as an example of the output.
- **`dbschema.png`** – An image illustrating a possible database schema for the gene metadata (as discussed in the “Database Schema” section).
- **`LICENSE`** – The license for this project.

Users interested in the data or script can clone the repository and run the script to regenerate the CSV, or modify the script to adapt to similar projects or new gene lists.

## License

This project is licensed under the MIT License. See the [`LICENSE`](LICENSE) file for details.

