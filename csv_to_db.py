from pathlib import Path

import pandas as pd
import sqlite3
import argparse
import sys
import os


def extract_hgnc_number(hgnc_id):
    """Extract numeric ID from HGNC ID string."""
    return int(hgnc_id.replace('HGNC:', ''))


def split_values(text):
    """Split multiple values separated by semicolons."""
    if pd.isna(text):
        return []
    return [x.strip() for x in text.split(';')]


def process_gene_data(csv_path, db_path):
    """Process gene data from CSV and store in SQLite database."""
    # Verify input file exists
    if not os.path.exists(csv_path):
        print(f"Error: Input file '{csv_path}' not found.")
        sys.exit(1)

    try:
        # Read the CSV file
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)

    try:
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create tables if they don't exist
        cursor.executescript(Path("database_ddl.sql").read_text())

        # Process each row
        for _, row in df.iterrows():
            hgnc_id = extract_hgnc_number(row['HGNC ID'])

            # Insert into Gene table
            cursor.execute('''
                           INSERT OR REPLACE INTO Gene (hgnc_id, symbol, name, coord_hg38, coord_hg19)
                           VALUES (?, ?, ?, ?, ?)
                           ''', (
                               hgnc_id,
                               row['Gene Symbol'],
                               row['HGNC Gene Name'],
                               row['hg38 Coordinates'],
                               row['hg19 Coordinates']
                           ))

            # Delete existing aliases and diseases for this gene
            cursor.execute('DELETE FROM Alias WHERE hgnc_id = ?', (hgnc_id,))
            cursor.execute('DELETE FROM Disease WHERE hgnc_id = ?', (hgnc_id,))

            # Process aliases
            aliases = split_values(row['Gene Aliases'])
            for alias in aliases:
                cursor.execute('''
                               INSERT INTO Alias (hgnc_id, alias)
                               VALUES (?, ?)
                               ''', (hgnc_id, alias))

            # Process diseases
            diseases = split_values(row['Disease'])
            for disease in diseases:
                cursor.execute('''
                               INSERT INTO Disease (hgnc_id, disease_name)
                               VALUES (?, ?)
                               ''', (hgnc_id, disease))

        # Commit changes
        conn.commit()
        print(f"✅ Successfully processed data and saved to {db_path}")

    except Exception as e:
        print(f"Error processing data: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()


def main():
    # Set up command line argument parser
    parser = argparse.ArgumentParser(description="Process gene metadata CSV file into SQLite database.")
    parser.add_argument("-i", "--input", required=True,
                        help="Path to input CSV file")
    parser.add_argument("-o", "--output", required=True,
                        help="Path to output SQLite database file")

    args = parser.parse_args()

    # Process the data
    process_gene_data(args.input, args.output)


if __name__ == "__main__":
    main()