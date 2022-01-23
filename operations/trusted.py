#!/usr/bin/env python
# coding: utf-8

import psycopg2
import os

def table_name(name, ts_sha):
    ts, sha = ts_sha
    return "formatted." + "_".join((name, sha, str(ts)))

def main():
    conn = psycopg2.connect(dbname="adsdb", user="adsdb")
    cur = conn.cursor()


    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'formatted'")
    tables = cur.fetchall()

    table_versions = dict()
    for table in tables:
        name_sha, _ , timestamp = table[0].rpartition("_")
        name, _, sha256 = name_sha.rpartition("_")
        
        print(name, sha256, timestamp)
        
        table_versions[name] = table_versions.get(name, []) + [(int(timestamp), sha256)]

    cur.execute("CREATE SCHEMA IF NOT EXISTS trusted;")

    for k, v in table_versions.items():
        # Order by timestamp (newest first)
        v = sorted(v)
        
        new_table = f"trusted.{k}"

        print("Populating table:", new_table, "...")

        cur.execute(f"DROP TABLE {new_table} CASCADE;")

        # Load all the newest data into new table
        cur.execute(f'''
        CREATE TABLE IF NOT EXISTS {new_table} AS 
            TABLE {table_name(k, v[0])};
        ''')
    conn.commit()

if __name__ == '__main__':
    main()
