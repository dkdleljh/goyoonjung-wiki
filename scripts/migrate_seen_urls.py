#!/usr/bin/env python3
"""Migrate legacy text files to SQLite."""
import os
import sys
from pathlib import Path

# Add script dir to path to import db_manager
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import db_manager

BASE = Path(__file__).resolve().parent.parent
SEEN_TXT = BASE / 'sources' / 'seen-urls.txt'

def main():
    print("Migrating seen-urls.txt to SQLite...")
    db_manager.init_db()
    
    if not SEEN_TXT.exists():
        print("No legacy text file found.")
        return
        
    count = db_manager.migrate_from_txt(SEEN_TXT)
    print(f"Migrated {count} URLs to database.")
    
    # Rename legacy file to backup
    # os.rename(SEEN_TXT, str(SEEN_TXT) + ".bak")
    # print("Renamed legacy file to .bak")

if __name__ == "__main__":
    main()
