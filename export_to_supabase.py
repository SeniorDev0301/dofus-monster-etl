#!/usr/bin/env python3
"""
Script pour exporter les données JSON vers des fichiers d'import Supabase.
Génère des fichiers CSV pour chaque table.
"""

import json
import csv
from pathlib import Path
from typing import Dict, List, Any
import sys

def setup_export_directory():
    """Crée le répertoire pour les exports"""
    export_dir = Path("supabase_export")
    export_dir.mkdir(exist_ok=True)
    return export_dir

def extract_monster_data(obj: Dict[str, Any]) -> Dict[str, Any]:
    """Extrait les données root d'un monstre"""
    return {
        'rid': obj.get('rid'),
        'type_class': obj.get('type', {}).get('class'),
        'type_ns': obj.get('type', {}).get('ns'),
        'type_asm': obj.get('type', {}).get('asm'),
        'data_raw': json.dumps(obj.get('data', {}))  # Stocker les données complexes en JSON
    }

def extract_grades(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extrait les grades d'un monstre"""
    grades = []
    for grade_data in data.get('grades', {}).get('Array', []):
        grade = {
            'grade': grade_data.get('grade'),
            'monsterId': grade_data.get('monsterId'),
            'level': grade_data.get('level'),
            'lifePoints': grade_data.get('lifePoints'),
            'actionPoints': grade_data.get('actionPoints'),
            'movementPoints': grade_data.get('movementPoints'),
            'vitality': grade_data.get('vitality'),
            'paDodge': grade_data.get('paDodge'),
            'pmDodge': grade_data.get('pmDodge'),
            'wisdom': grade_data.get('wisdom'),
            'earthResistance': grade_data.get('earthResistance'),
            'airResistance': grade_data.get('airResistance'),
            'fireResistance': grade_data.get('fireResistance'),
            'waterResistance': grade_data.get('waterResistance'),
            'neutralResistance': grade_data.get('neutralResistance'),
            'gradeXp': grade_data.get('gradeXp'),
            'damageReflect': grade_data.get('damageReflect'),
            'hiddenLevel': grade_data.get('hiddenLevel'),
            'strength': grade_data.get('strength'),
            'intelligence': grade_data.get('intelligence'),
            'chance': grade_data.get('chance'),
            'agility': grade_data.get('agility'),
            'startingSpellId': grade_data.get('startingSpellId'),
            'bonusRange': grade_data.get('bonusRange'),
            'bonusCharacteristics': json.dumps(grade_data.get('bonusCharacteristics', {}))
        }
        grades.append(grade)
    return grades

def extract_drops(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extrait les drops d'un monstre"""
    drops = []
    for drop_data in data.get('drops', {}).get('Array', []):
        drop = {
            'dropId': drop_data.get('dropId'),
            'monsterId': drop_data.get('monsterId'),
            'objectId': drop_data.get('objectId'),
            'percentDropForGrade1': drop_data.get('percentDropForGrade1'),
            'percentDropForGrade2': drop_data.get('percentDropForGrade2'),
            'percentDropForGrade3': drop_data.get('percentDropForGrade3'),
            'percentDropForGrade4': drop_data.get('percentDropForGrade4'),
            'percentDropForGrade5': drop_data.get('percentDropForGrade5'),
            'count': drop_data.get('count'),
            'criterions': drop_data.get('criterions'),
            'hasCriterions': drop_data.get('hasCriterions'),
            'hiddenIfInvalidCriterions': drop_data.get('hiddenIfInvalidCriterions'),
            'specificDropCoefficient': json.dumps(drop_data.get('specificDropCoefficient', {}))
        }
        drops.append(drop)
    return drops

def extract_spells(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extrait les spells d'un monstre"""
    spells = []
    spell_list = data.get('spells', {}).get('Array', [])
    spell_grades = data.get('spellGrades', {}).get('Array', [])
    
    for i, spell_id in enumerate(spell_list):
        spell = {
            'spellId': spell_id,
            'spellGrade': spell_grades[i] if i < len(spell_grades) else None
        }
        spells.append(spell)
    return spells

def extract_anims(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extrait les animations d'un monstre"""
    anims = []
    for anim_data in data.get('animFunList', {}).get('Array', []):
        anim = {
            'animId': anim_data.get('animId'),
            'entityId': anim_data.get('entityId'),
            'animName': anim_data.get('animName'),
            'animWeight': anim_data.get('animWeight')
        }
        anims.append(anim)
    return anims

def export_data(input_file: str = 'monsters.json'):
    """Exporte les données vers des fichiers CSV"""
    
    print("📥 Chargement du fichier JSON...\n")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    ref_ids_data = data.get('references', {}).get('RefIds', [])
    print(f"✅ {len(ref_ids_data):,} monstres détectés\n")
    
    # Créer le répertoire d'export
    export_dir = setup_export_directory()
    
    # Listes pour stocker les données
    monsters = []
    grades_list = []
    drops_list = []
    spells_list = []
    anims_list = []
    
    monster_id_map = {}  # Pour mapper rid à l'ID auto-généré
    
    print("📊 Traitement des données...\n")
    
    for i, obj in enumerate(ref_ids_data):
        if (i + 1) % 500 == 0:
            print(f"  ├─ {i + 1:,} monstres traités...")
        
        # Données du monstre
        monster = extract_monster_data(obj)
        monsters.append(monster)
        
        # Stocker le mapping rid -> index (qui devient l'ID)
        monster_id_map[obj.get('rid')] = i + 1
        
        # Données imbriquées
        data_section = obj.get('data', {})
        
        # Grades
        for grade in extract_grades(data_section):
            grade['monster_rid'] = obj.get('rid')
            grades_list.append(grade)
        
        # Drops
        for drop in extract_drops(data_section):
            drop['monster_rid'] = obj.get('rid')
            drops_list.append(drop)
        
        # Spells
        for spell in extract_spells(data_section):
            spell['monster_rid'] = obj.get('rid')
            spells_list.append(spell)
        
        # Anims
        for anim in extract_anims(data_section):
            anim['monster_rid'] = obj.get('rid')
            anims_list.append(anim)
    
    print(f"\n✅ Données consolidées\n")
    
    # Exporter les fichiers CSV
    print("💾 Génération des fichiers CSV...\n")
    
    # Monsters
    if monsters:
        with open(export_dir / 'monsters.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=monsters[0].keys())
            writer.writeheader()
            writer.writerows(monsters)
        print(f"  ✓ monsters.csv ({len(monsters)} lignes)")
    
    # Grades
    if grades_list:
        with open(export_dir / 'monster_grades.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=grades_list[0].keys())
            writer.writeheader()
            writer.writerows(grades_list)
        print(f"  ✓ monster_grades.csv ({len(grades_list)} lignes)")
    
    # Drops
    if drops_list:
        with open(export_dir / 'monster_drops.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=drops_list[0].keys())
            writer.writeheader()
            writer.writerows(drops_list)
        print(f"  ✓ monster_drops.csv ({len(drops_list)} lignes)")
    
    # Spells
    if spells_list:
        with open(export_dir / 'monster_spells.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=spells_list[0].keys())
            writer.writeheader()
            writer.writerows(spells_list)
        print(f"  ✓ monster_spells.csv ({len(spells_list)} lignes)")
    
    # Anims
    if anims_list:
        with open(export_dir / 'monster_anims.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=anims_list[0].keys())
            writer.writeheader()
            writer.writerows(anims_list)
        print(f"  ✓ monster_anims.csv ({len(anims_list)} lignes)")
    
    print(f"\n✅ Export terminé dans le répertoire: {export_dir}/\n")
    
    # Afficher les stats
    print("📊 RÉSUMÉ DE L'EXPORT")
    print("=" * 60)
    print(f"  • Monstres: {len(monsters):,}")
    print(f"  • Grades: {len(grades_list):,}")
    print(f"  • Drops: {len(drops_list):,}")
    print(f"  • Spells: {len(spells_list):,}")
    print(f"  • Anims: {len(anims_list):,}")
    print("=" * 60)
    
    return export_dir

def generate_import_sql(export_dir: Path):
    """Génère un script SQL d'import"""
    
    sql_path = export_dir / 'import.sql'
    
    with open(sql_path, 'w', encoding='utf-8') as f:
        f.write("""-- Import des données Monsters Dofus vers Supabase
-- Exécuter ce script après avoir créé les tables

-- Importer les monstres
\\COPY monsters(rid, type_class, type_ns, type_asm, data_raw) FROM 'monsters.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', ENCODING 'UTF8');

-- Importer les grades
\\COPY monster_grades(grade, monster_id, level, ...) FROM 'monster_grades.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', ENCODING 'UTF8');

-- Importer les drops
\\COPY monster_drops(...) FROM 'monster_drops.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', ENCODING 'UTF8');

-- Importer les spells
\\COPY monster_spells(...) FROM 'monster_spells.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', ENCODING 'UTF8');

-- Importer les anims
\\COPY monster_anims(...) FROM 'monster_anims.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', ENCODING 'UTF8');
""")
    
    print(f"  ✓ import.sql généré")

if __name__ == "__main__":
    export_dir = export_data()
    generate_import_sql(export_dir)
