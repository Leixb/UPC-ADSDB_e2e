#!/usr/bin/env python

import psycopg2
import os
import glob
import json


try:
  from google.colab import drive
  drive.mount('/content/drive', force_remount=True)
  is_local = False
except ModuleNotFoundError:
  is_local = True


folder_landing = "./landing" if (is_local) else "/content/drive/MyDrive/ADSDB/landing"

folder_temporal = os.path.join(folder_landing, "temporal")
folder_persistent = os.path.join(folder_landing, "persistent")

extract_dir = os.path.join(folder_persistent, "extracted")

def get_specs(
        spec_folder = os.path.join(folder_landing, 'sql_spec'),
        spec_table_file = os.path.join(folder_landing, 'spec_tables.json')
    ):
    table_spec = dict()
    for spec_file in glob.glob(os.path.join(spec_folder, '*')):
        table_name = os.path.basename(spec_file)
        
        with open(spec_file, 'r') as f:
            table_spec[table_name] = f.read()

    with open(spec_table_file, 'r') as f:
        table_equi = json.load(f)

    return table_spec, table_equi

def table_exists(cur, table_name):
    cur.execute('''SELECT EXISTS(SELECT 1 FROM information_schema.tables 
              WHERE table_catalog='adsdb' AND 
                    table_schema='formatted' AND 
                    table_name=%s);''', (table_name.lower(),))
    return cur.fetchone()[0]

def create_table(cursor, table_type, icd_rev, timestamp, table_spec, overwritte = False):
    if icd_rev is None:
        icd_rev = 0

    table_name = f"{table_type}_{icd_rev}_{timestamp}"
    table_name_full = f"formatted.{table_name}"
    
    if table_exists(cursor, table_name):
        if not overwritte:
            return None
        print(f"Overwritting table {table_name_full}")
        cursor.execute(f"DROP TABLE {table_name_full} CASCADE;");

    cursor.execute(f'''CREATE TABLE {table_name_full} (
        {table_spec[table_type]}
    );
    ''')
    
    return table_name_full

def load_csv(cursor, table_name, filename):
    with open(filename, 'r') as csvfile:
        cursor.copy_expert(f'''
            COPY {table_name}
            FROM STDIN
            DELIMITER ','
            CSV HEADER;
        ''', csvfile)
        
def ingest_folder(cur, folder_path, table_spec, table_equi):
    with open(os.path.join(folder_path, "metadata.json"), 'r') as f:
        metadata = json.load(f)

    folder_base = os.path.basename(folder_path)
    
    contents = glob.glob(f"{folder_path}/*")
    
    name_sha, _, timestamp = folder_base.rpartition("-")
    name, _, sha = name_sha.rpartition("-")
    version = sha[:4] + "_" + timestamp.partition(".")[0]

    for i in contents:
        filename = os.path.basename(i)
        if filename == "metadata.json":
            continue

        table = table_equi.get(filename)
    
        if table is not None:
            target_table = create_table(cur, table['spec'], table.get('rev'), version, table_spec)
            
            if target_table is None:
                print("SKIP ALREADY_IN_DB", filename)
                continue

            load_csv(cur, target_table, i)

            print("LOAD", filename, "==>", target_table)
        else:
            print("SKIP IGNORED", filename)


def main():
    conn = psycopg2.connect(dbname="adsdb", user="adsdb", password="adsdb")

    table_spec, table_equi = get_specs()

    cur = conn.cursor()
    cur.execute('''CREATE SCHEMA IF NOT EXISTS formatted''')
    for meta in glob.glob(f"{folder_persistent}/extracted/*/metadata.json"):
        ingest_folder(cur, os.path.dirname(meta), table_spec, table_equi)
    conn.commit()

if __name__ == '__main__':
    main()
