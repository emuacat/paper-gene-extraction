-- Create Gene table
CREATE TABLE IF NOT EXISTS Gene (
    hgnc_id    INTEGER PRIMARY KEY,   -- HGNC ID for the gene
    symbol     TEXT    NOT NULL,      -- Gene symbol (unique identifier like APOL1)
    name       TEXT    NOT NULL,      -- Full HGNC gene name
    coord_hg38 TEXT,                  -- Genomic coordinates (hg38 assembly)
    coord_hg19 TEXT                   -- Genomic coordinates (hg19 assembly)
);

-- Create Alias table (aliases for genes)
CREATE TABLE IF NOT EXISTS Alias (
    id       INTEGER PRIMARY KEY,     -- Auto-increment alias ID
    hgnc_id  INTEGER NOT NULL,        -- References Gene(hgnc_id)
    alias    TEXT    NOT NULL,        -- Alias name for the gene
    FOREIGN KEY (hgnc_id) REFERENCES Gene(hgnc_id)
);

-- Create Disease table (diseases associated with genes)
CREATE TABLE IF NOT EXISTS Disease (
    id            INTEGER PRIMARY KEY,  -- Auto-increment disease ID
    hgnc_id       INTEGER NOT NULL,     -- References Gene(hgnc_id)
    disease_name  TEXT    NOT NULL,     -- Name of an associated disease or syndrome
    FOREIGN KEY (hgnc_id) REFERENCES Gene(hgnc_id)
);
