# 📊 Synthèse de l'analyse - Base de données Dofus Monsters

## 📈 Volume de données

| Élément | Quantité |
|---------|----------|
| **Monstres** | 4,915 |
| **Grades** | 26,372 (6 par monstre en moyenne) |
| **Drops** | 12,817 |
| **Spells** | 13,765 |
| **Animations** | 3,930 |
| **Total de lignes** | ~57,000 |

## 🗂️ Structure des fichiers générés

### Fichiers CSV

```
supabase_export/
├── monsters.csv                  # 4,915 lignes - Table principale
├── monster_grades.csv            # 26,372 lignes - Grades de monstres
├── monster_drops.csv             # 12,817 lignes - Loots
├── monster_spells.csv            # 13,765 lignes - Spells
├── monster_anims.csv             # 3,930 lignes - Animations
└── import.sql                    # Script d'import
```

## 📋 Colonnes principales

### `monsters.csv`
- `rid` (integer) - Reference ID unique du monstre
- `type_class` (string) - Classe Unity: "MonsterData"
- `type_ns` (string) - Namespace complet
- `type_asm` (string) - Assembly
- `data_raw` (text/JSON) - Données complètes en JSON

### `monster_grades.csv`
| Colonne | Type | Description |
|---------|------|-------------|
| grade | integer | 1-6 (niveau de rareté) |
| monsterId | integer | ID du monstre |
| level | integer | Niveau du monstre |
| lifePoints | integer | Points de vie |
| actionPoints | integer | Points d'action (PA) |
| movementPoints | integer | Points de mouvement (PM) |
| wisdom | integer | Sagesse |
| strength | integer | Force |
| intelligence | integer | Intelligence |
| chance | integer | Chance |
| agility | integer | Agilité |
| *Resistance | integer | Résistances élémentaires |
| gradeXp | integer | XP du grade |
| bonusCharacteristics | JSON | Bonus supplémentaires |
| monster_rid | integer | Référence au monstre parent |

### `monster_drops.csv`
| Colonne | Type | Description |
|---------|------|-------------|
| dropId | integer | ID du drop unique |
| objectId | integer | ID de l'objet droppé |
| percentDropForGradeX | numeric | % de drop par grade |
| criterions | text | Critères complexes (conditions de drop) |
| count | integer | Quantité droppée |

### `monster_spells.csv`
| Colonne | Type |
|---------|------|
| spellId | integer |
| spellGrade | text |
| monster_rid | integer |

### `monster_anims.csv`
| Colonne | Type |
|---------|------|
| animId | integer |
| animName | text |
| animWeight | integer |
| entityId | integer |

## 🚀 Étapes d'import Supabase

### 1. Créer les tables SQL

Copier-coller le SQL du rapport d'analyse dans la console Supabase SQL:

```sql
CREATE TABLE monsters (
  id BIGSERIAL PRIMARY KEY,
  rid integer NOT NULL UNIQUE,
  type_class varchar(50),
  type_ns text,
  type_asm text,
  data_raw jsonb,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- ... (autres tables)
```

### 2. Importer les données

**Option A: Via Supabase UI (GUI)**
1. Allez sur https://app.supabase.com
2. Projet → SQL Editor
3. Collez et exécutez le SQL
4. Cliquez sur votre table → "Insert" → "Upload CSV"
5. Sélectionnez le fichier CSV

**Option B: Via CLI PostgreSQL**

```bash
# Adapter les paramètres de connexion
psql -h db.supabase.co -U postgres -d postgres \
  -c "\COPY monsters(rid, type_class, type_ns, type_asm, data_raw) FROM 'supabase_export/monsters.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',')"

\COPY monster_grades(...) FROM 'supabase_export/monster_grades.csv' WITH (FORMAT csv, HEADER true);
\COPY monster_drops(...) FROM 'supabase_export/monster_drops.csv' WITH (FORMAT csv, HEADER true);
# ... etc
```

**Option C: Via Python + supabase-py**

```python
from supabase import create_client
import pandas as pd

supabase = create_client(URL, KEY)

# Importer les monstres
df_monsters = pd.read_csv('supabase_export/monsters.csv')
for _, row in df_monsters.iterrows():
    supabase.table('monsters').insert(row.to_dict()).execute()

# Importer les grades
df_grades = pd.read_csv('supabase_export/monster_grades.csv')
batch_size = 100
for i in range(0, len(df_grades), batch_size):
    batch = df_grades[i:i+batch_size].to_dict('records')
    supabase.table('monster_data_grades').insert(batch).execute()

# ... Répéter pour les autres tables
```

## 🔍 Requêtes SQL utiles

### Trouver tous les monstres de niveau 20

```sql
SELECT m.*, g.*
FROM monsters m
JOIN monster_data_grades g ON g.monster_rid = m.rid
WHERE g.level = 20
ORDER BY g.grade;
```

### Loot table d'un monstre spécifique

```sql
SELECT d.objectId, d.dropId, d.percentDropForGrade1
FROM monster_data_drops d
JOIN monsters m ON m.rid = d.monster_rid
WHERE m.rid = 2396748898127592475
ORDER BY d.percentDropForGrade1 DESC;
```

### Monstres avec résistance positive à un élément

```sql
SELECT m.rid, g.level, g.waterResistance
FROM monsters m
JOIN monster_data_grades g ON g.monster_rid = m.rid
WHERE g.grade = 1 AND g.waterResistance > 20
ORDER BY g.waterResistance DESC;
```

### Top 10 monstres avec le plus de drops

```sql
SELECT m.rid, COUNT(d.dropId) as drop_count
FROM monsters m
LEFT JOIN monster_data_drops d ON d.monster_rid = m.rid
GROUP BY m.rid
ORDER BY drop_count DESC
LIMIT 10;
```

## ⚠️ Points d'attention

### Encodage
- ✅ Tous les fichiers sont en UTF-8
- ✅ Caractères spéciaux échappés correctement

### Valeurs NULL
- ⚠️ Les drops vides sont représentés par des tableaux vides `[]`
- ⚠️ Utilisez `IS NULL` pour les champs réellement vides

### Performance
- 📊 ~57k lignes au total (très manageable)
- ⚡ Créez les index **après** l'import complet
- 💾 Les données JSON en `data_raw` peuvent être lourdes

### Intégrité des données
- 🔑 `rid` est unique pour chaque monstre (utiliser en clé étrangère)
- 🔑 `monster_rid` relie tous les grades/drops/etc au monstre parent
- ✅ Les cascades DELETE sont configurées

## 📦 Optimisations recommandées

### Post-import

```sql
-- Ajouter des index de performance
CREATE INDEX idx_monsters_rid ON monsters(rid);
CREATE INDEX idx_grades_level ON monster_data_grades(level);
CREATE INDEX idx_grades_grade ON monster_data_grades(grade);
CREATE INDEX idx_drops_objectid ON monster_data_drops(objectId);

-- Créer des vues utiles
CREATE VIEW monsters_by_level AS
SELECT 
  m.rid,
  g.level,
  COUNT(*) as count
FROM monsters m
JOIN monster_data_grades g ON g.monster_rid = m.rid
GROUP BY m.rid, g.level
ORDER BY g.level;

-- Statistiques pour le query planner
ANALYZE monsters;
ANALYZE monster_data_grades;
ANALYZE monster_data_drops;
```

## 🔐 Sécurité

### Activer RLS (Row Level Security)

```sql
ALTER TABLE monsters ENABLE ROW LEVEL SECURITY;
ALTER TABLE monster_data_grades ENABLE ROW LEVEL SECURITY;

-- Policy d'exemple: lecture publique
CREATE POLICY "Tous les monstres visibles"
  ON monsters
  FOR SELECT
  USING (true);

CREATE POLICY "Tous les grades visibles"
  ON monster_data_grades
  FOR SELECT
  USING (true);
```

## 📞 Dépannage

### Erreur: "Violates unique constraint"
→ Les IDs `rid` existent déjà. Truncate les tables avant de réimporter.

```sql
TRUNCATE TABLE monsters CASCADE;
```

### Import lent
→ Désactiver temporairement les index:

```sql
DROP INDEX idx_monsters_rid;
-- ... import ...
CREATE INDEX idx_monsters_rid ON monsters(rid);
```

### Fichier CSV corrompu
→ Valider avec:

```bash
python3 -c "import pandas as pd; df = pd.read_csv('supabase_export/monsters.csv'); print(f'OK: {len(df)} lignes')"
```

## 📚 Ressources

- [Supabase Documentation](https://supabase.com/docs)
- [PostgreSQL COPY](https://www.postgresql.org/docs/current/sql-copy.html)
- [JSON Functions](https://www.postgresql.org/docs/current/functions-json.html)
- [Supabase CLI](https://supabase.com/docs/reference/cli)

---

**Généré le**: 2025-10-25  
**Taille totale**: ~50-100 MB en CSV  
**Format**: UTF-8 CSV avec en-têtes  
**Compatibilité**: Supabase (PostgreSQL 12+)
