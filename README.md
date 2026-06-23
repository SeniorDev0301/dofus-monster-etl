# dofus-monster-json-to-sql

> **Convert Dofus monster data from JSON format into a normalized SQL/Supabase-ready database**

A Python toolkit that parses the Dofus game monster dataset (`monsters.json`, 4,915 monsters), analyzes its nested structure, generates SQL schema recommendations, and exports normalized CSV files ready to import into [Supabase](https://supabase.com) (PostgreSQL).

---

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Data Model](#data-model)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Running Guide](#running-guide)
  - [Step 1 — Analyze the JSON structure](#step-1--analyze-the-json-structure)
  - [Step 2 — Export data to CSV](#step-2--export-data-to-csv)
  - [Step 3 — Import into Supabase](#step-3--import-into-supabase)
- [Generated Files](#generated-files)
- [SQL Schema](#sql-schema)
- [Useful Queries](#useful-queries)
- [Troubleshooting](#troubleshooting)

---

## Overview

The Dofus monster dataset is a deeply nested JSON file extracted from the game's data center. Each monster record contains:

- Basic metadata (`id`, `nameId`, `gfxId`, `race`, `look`)
- **Grades** (1–6): level, HP, stats, resistances, and XP per grade
- **Drops**: loot tables with per-grade drop percentages and conditions
- **Spells**: spell IDs and grades used by the monster
- **Animations**: animation function definitions

This project provides two scripts to flatten and normalize that structure into relational tables.

| Script | Purpose |
|---|---|
| `analyse_json.py` | Inspects the JSON, prints a full field report, and generates a `supabase_schema.sql` DDL file |
| `export_to_supabase.py` | Reads the JSON and writes one CSV per relational table |

---

## Project Structure

```
.
├── monsters.json            # Source data — 4,915 Dofus monsters (~70 MB)
├── analyse_json.py          # JSON structure analyzer + SQL schema generator
├── export_to_supabase.py    # CSV exporter for Supabase import
├── README.md                # This file
├── IMPORT_GUIDE.md          # Detailed import walkthrough and SQL query examples
└── supabase_export/         # Generated output directory (created at runtime)
    ├── monsters.csv
    ├── monster_grades.csv
    ├── monster_drops.csv
    ├── monster_spells.csv
    ├── monster_anims.csv
    └── import.sql
```

> `supabase_export/` and `*.sql` files are listed in `.gitignore` and will not be committed.

---

## Data Model

After export, the data is split into five tables:

```
monsters  (4,915 rows)
    │
    ├── monster_grades     (26,372 rows — ~6 grades per monster)
    ├── monster_drops      (12,817 rows — loot table entries)
    ├── monster_spells     (13,765 rows — spells used per monster)
    └── monster_anims      (3,930 rows  — animation definitions)
```

All child tables link back to the parent via `monster_rid` (the monster's unique reference ID).

---

## Prerequisites

- Python 3.8 or higher
- No third-party libraries required for the core scripts (uses only the standard library: `json`, `csv`, `pathlib`, `collections`)

Optional — for the Python-based Supabase import method:

```bash
pip install supabase pandas
```

---

## Getting Started

```bash
# 1. Clone the repository
git clone https://github.com/your-username/dofus-monster-json-to-sql.git
cd dofus-monster-json-to-sql

# 2. Confirm Python version
python3 --version  # requires 3.8+

# 3. Verify the data file is present
ls -lh monsters.json  # should be ~70 MB
```

---

## Running Guide

### Step 1 — Analyze the JSON structure

```bash
python3 analyse_json.py
```

This script reads `monsters.json` and prints:

- **General statistics** — total objects, field count, detected arrays and nested objects
- **Field hierarchy** — every field path with its inferred SQL type and presence rate
- **Nested objects** — properties of embedded objects (e.g. `type`, `data`)
- **Array contents** — columns detected inside each array (grades, drops, spells, anims)
- **Recommended SQL schema** — ready-to-paste `CREATE TABLE` DDL statements

It also writes the generated DDL to `supabase_schema.sql` in the current directory.

**Expected output (excerpt):**

```
✅ Total d'objets détectés: 4,915

🌳 STRUCTURE HIÉRARCHIQUE
────────────────────────────────────────
Champ       Type SQL    Présence
────────────────────────────────────────
data        jsonb       ✓ 100%
rid         integer     ✓ 100%
type        jsonb       ✓ 100%

📚 TABLEAUX DÉTECTÉS (10 tableaux)
   🔷 data.grades.Array → 25 colonnes
   🔷 data.drops.Array  → 13 colonnes
   ...

✅ Schéma SQL exporté dans: supabase_schema.sql
```

---

### Step 2 — Export data to CSV

```bash
python3 export_to_supabase.py
```

This script reads `monsters.json`, splits the nested data into flat tables, and writes CSV files to `supabase_export/`.

**Expected output:**

```
✅ 4,915 monstres détectés

📊 RÉSUMÉ DE L'EXPORT
════════════════════════════════════════
  • Monstres : 4,915
  • Grades   : 26,372
  • Drops    : 12,817
  • Spells   : 13,765
  • Anims    :  3,930
════════════════════════════════════════

✅ Export terminé dans le répertoire: supabase_export/
```

> **Note:** Processing the full ~70 MB JSON file takes about 10–30 seconds depending on your machine.

---

### Step 3 — Import into Supabase

#### Option A — Supabase UI (recommended for first-time setup)

1. Go to [https://app.supabase.com](https://app.supabase.com) and open your project.
2. Navigate to **SQL Editor** and paste the contents of `supabase_schema.sql`.
3. Run the SQL to create all tables.
4. For each table, go to **Table Editor → Insert → Upload CSV** and upload the corresponding file from `supabase_export/`.

#### Option B — PostgreSQL CLI (`psql`)

```bash
# Replace connection details with your Supabase project credentials
psql -h db.<your-project-ref>.supabase.co -U postgres -d postgres

\COPY monsters(rid, type_class, type_ns, type_asm, data_raw) \
  FROM 'supabase_export/monsters.csv' \
  WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');

\COPY monster_grades(grade, monsterId, level, lifePoints, ...) \
  FROM 'supabase_export/monster_grades.csv' \
  WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');

-- Repeat for monster_drops, monster_spells, monster_anims
```

#### Option C — Python (`supabase-py`)

```python
from supabase import create_client
import pandas as pd

SUPABASE_URL = "https://<your-project-ref>.supabase.co"
SUPABASE_KEY = "<your-anon-or-service-role-key>"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Import monsters
df = pd.read_csv("supabase_export/monsters.csv")
for _, row in df.iterrows():
    supabase.table("monsters").insert(row.to_dict()).execute()

# Import grades in batches of 100
df_grades = pd.read_csv("supabase_export/monster_grades.csv")
batch_size = 100
for i in range(0, len(df_grades), batch_size):
    batch = df_grades[i:i + batch_size].to_dict("records")
    supabase.table("monster_data_grades").insert(batch).execute()

# Repeat for drops, spells, anims
```

---

## Generated Files

| File | Rows | Description |
|---|---|---|
| `monsters.csv` | 4,915 | One row per monster. Core fields plus raw JSON data stored in `data_raw`. |
| `monster_grades.csv` | 26,372 | Per-grade stats: level, HP, action/movement points, elemental resistances, XP. |
| `monster_drops.csv` | 12,817 | Loot table: item IDs, per-grade drop percentages, drop conditions. |
| `monster_spells.csv` | 13,765 | Spell IDs and grades assigned to each monster. |
| `monster_anims.csv` | 3,930 | Animation function list: ID, name, weight, and entity reference. |
| `import.sql` | — | Template `\COPY` commands for CLI import. |

---

## SQL Schema

Key table definitions (abbreviated):

```sql
-- Parent table
CREATE TABLE monsters (
  id         BIGSERIAL PRIMARY KEY,
  rid        INTEGER NOT NULL UNIQUE,
  type_class VARCHAR(50),
  type_ns    TEXT,
  type_asm   TEXT,
  data_raw   JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Monster grades (1–6 per monster)
CREATE TABLE monster_data_grades (
  id               BIGSERIAL PRIMARY KEY,
  monster_id       BIGINT NOT NULL REFERENCES monsters(id) ON DELETE CASCADE,
  grade            INTEGER,
  level            INTEGER,
  lifePoints       INTEGER,
  actionPoints     INTEGER,
  movementPoints   INTEGER,
  strength         INTEGER,
  intelligence     INTEGER,
  wisdom           INTEGER,
  chance           INTEGER,
  agility          INTEGER,
  earthResistance  INTEGER,
  fireResistance   INTEGER,
  waterResistance  INTEGER,
  airResistance    INTEGER,
  neutralResistance INTEGER,
  gradeXp          INTEGER,
  created_at       TIMESTAMP DEFAULT NOW()
);

-- Loot table
CREATE TABLE monster_data_drops (
  id                       BIGSERIAL PRIMARY KEY,
  monster_id               BIGINT NOT NULL REFERENCES monsters(id) ON DELETE CASCADE,
  dropId                   INTEGER,
  objectId                 INTEGER,
  percentDropForGrade1     NUMERIC,
  percentDropForGrade2     NUMERIC,
  percentDropForGrade3     NUMERIC,
  percentDropForGrade4     NUMERIC,
  percentDropForGrade5     NUMERIC,
  criterions               TEXT,
  created_at               TIMESTAMP DEFAULT NOW()
);
```

**Recommended indexes (run after import for best performance):**

```sql
CREATE INDEX idx_monsters_rid          ON monsters(rid);
CREATE INDEX idx_grades_level          ON monster_data_grades(level);
CREATE INDEX idx_grades_grade          ON monster_data_grades(grade);
CREATE INDEX idx_drops_objectid        ON monster_data_drops(objectId);
```

---

## Useful Queries

```sql
-- All grade-1 monsters at level 20
SELECT m.rid, g.level, g.lifePoints
FROM monsters m
JOIN monster_data_grades g ON g.monster_id = m.id
WHERE g.grade = 1 AND g.level = 20;

-- Loot table for a specific monster
SELECT d.objectId, d.percentDropForGrade1
FROM monster_data_drops d
JOIN monsters m ON m.id = d.monster_id
WHERE m.rid = 2396748898127592475
ORDER BY d.percentDropForGrade1 DESC;

-- Top 10 monsters with the most drops
SELECT m.rid, COUNT(d.id) AS drop_count
FROM monsters m
LEFT JOIN monster_data_drops d ON d.monster_id = m.id
GROUP BY m.rid
ORDER BY drop_count DESC
LIMIT 10;

-- Monsters with high water resistance at grade 1
SELECT m.rid, g.level, g.waterResistance
FROM monsters m
JOIN monster_data_grades g ON g.monster_id = m.id
WHERE g.grade = 1 AND g.waterResistance > 20
ORDER BY g.waterResistance DESC;
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `json.JSONDecodeError` | Validate the file with `python3 -m json.tool monsters.json` |
| Import CSV encoding error | All files are UTF-8; ensure your Postgres client uses `ENCODING 'UTF8'` |
| Unique constraint violation on re-import | Run `TRUNCATE TABLE monsters CASCADE;` before re-importing |
| Slow Python import | Use batch inserts (100–1000 rows per request) and add indexes after the import |
| `monsters.json` not found | Make sure the file is in the same directory as the scripts |

---

## Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase Python Client](https://github.com/supabase-community/supabase-py)
- [PostgreSQL JSON Functions](https://www.postgresql.org/docs/current/functions-json.html)
- [PostgreSQL COPY](https://www.postgresql.org/docs/current/sql-copy.html)
