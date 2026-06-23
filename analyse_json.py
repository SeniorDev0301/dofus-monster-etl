import json
from collections import defaultdict, Counter
from typing import Any, Dict, Set, Tuple
from pathlib import Path
import sys

def analyze_json_structure(file_path):
    """Analyse la structure du fichier JSON Dofus pour Supabase"""
    
    print("🔍 Chargement du fichier JSON...\n")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            print("  ├─ Parsing du JSON...")
            data = json.load(f)
        
        print("  └─ Analyse de la structure...\n")
        
        # Extraire les références avec données réelles
        refs = data.get('references', {})
        ref_ids_data = refs.get('RefIds', [])
        
        print(f"✅ Total d'objets détectés: {len(ref_ids_data):,}\n")
        
        # Analyser la structure
        field_types = defaultdict(Counter)
        field_presence = defaultdict(int)
        field_samples = defaultdict(list)
        field_max_lengths = defaultdict(int)
        nested_fields = {}
        array_fields = {}
        array_nested_fields = {}
        
        total_objects = 0
        
        print("📊 Analyse des objets...\n")
        
        for i, obj in enumerate(ref_ids_data):
            if (i + 1) % 500 == 0:
                print(f"  ├─ {i + 1:,} objets analysés...")
            
            if isinstance(obj, dict):
                # Analyser les champs root
                analyze_object(obj, field_types, field_presence,
                             field_samples, field_max_lengths,
                             nested_fields, array_fields, array_nested_fields,
                             prefix='', is_root=True)
                total_objects += 1
        
        print(f"\n✅ Analyse terminée: {total_objects:,} objets traités\n")
        
        return {
            'fields': dict(field_types),
            'presence': dict(field_presence),
            'samples': dict(field_samples),
            'max_lengths': dict(field_max_lengths),
            'nested': nested_fields,
            'arrays': array_fields,
            'array_nested': array_nested_fields,
            'total': total_objects
        }
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_object(obj, field_types, field_presence, field_samples, 
                   field_max_lengths, nested_fields, array_fields, 
                   array_nested_fields, prefix='', is_root=False, depth=0):
    """Analyse récursive d'un objet JSON"""
    
    if depth > 5:  # Limiter la profondeur
        return
    
    if not isinstance(obj, dict):
        return
    
    for key, value in obj.items():
        full_key = f"{prefix}{key}" if prefix else key
        field_presence[full_key] += 1
        
        if value is None:
            field_types[full_key]['null'] += 1
        elif isinstance(value, bool):
            field_types[full_key]['boolean'] += 1
        elif isinstance(value, int):
            field_types[full_key]['integer'] += 1
        elif isinstance(value, float):
            field_types[full_key]['float'] += 1
        elif isinstance(value, str):
            field_types[full_key]['string'] += 1
            field_max_lengths[full_key] = max(field_max_lengths[full_key], len(value))
            if len(field_samples[full_key]) < 2:
                field_samples[full_key].append(value[:80])
            if len(value) > 500:
                field_types[full_key]['text_long'] += 1
        elif isinstance(value, list):
            array_fields[full_key] = 'array'
            field_types[full_key]['array'] += 1
            
            if value:
                if isinstance(value[0], dict):
                    array_nested_fields[full_key] = defaultdict(Counter)
                    # Analyser les 100 premiers items
                    for item in value[:100]:
                        if isinstance(item, dict):
                            for k, v in item.items():
                                t = get_type_name(v)
                                array_nested_fields[full_key][k][t] += 1
                elif isinstance(value[0], (int, float)):
                    field_types[full_key]['array_numeric'] += 1
                elif isinstance(value[0], str):
                    field_types[full_key]['array_string'] += 1
        elif isinstance(value, dict):
            nested_fields[full_key] = {}
            field_types[full_key]['object'] += 1
            # Analyser les champs imbriqués mais limiter la profondeur
            if depth < 3:
                analyze_object(value, field_types, field_presence, field_samples,
                             field_max_lengths, nested_fields, array_fields,
                             array_nested_fields, prefix=f"{full_key}.", is_root=False, depth=depth+1)

def get_type_name(value):
    """Retourne le nom du type de la valeur"""
    if value is None:
        return 'null'
    elif isinstance(value, bool):
        return 'boolean'
    elif isinstance(value, int):
        return 'integer'
    elif isinstance(value, float):
        return 'float'
    elif isinstance(value, str):
        return 'string'
    elif isinstance(value, list):
        return 'array'
    elif isinstance(value, dict):
        return 'object'
    return 'unknown'

def get_sql_type(types, max_length):
    """Détermine le type SQL Supabase approprié"""
    
    type_names = set(types.keys())
    total_count = sum(types.values())
    
    if 'string' in type_names and type_names == {'string'}:
        if max_length > 1000:
            return 'text'
        elif max_length > 255:
            return 'text'
        else:
            return f'varchar({min(max_length + 50, 255)})'
    elif 'integer' in type_names and type_names == {'integer'}:
        return 'integer'
    elif {'integer', 'float'} >= type_names or 'float' in type_names:
        return 'numeric'
    elif 'boolean' in type_names and type_names == {'boolean'}:
        return 'boolean'
    elif 'array' in type_names:
        return 'jsonb'
    elif 'object' in type_names:
        return 'jsonb'
    elif type_names == {'string', 'null'}:
        return 'text'
    else:
        return 'jsonb'

def print_report(stats):
    """Affiche un rapport formaté"""
    
    total_lines = stats['total']
    field_types = stats['fields']
    field_presence = stats['presence']
    nested_fields = stats['nested']
    array_fields = stats['arrays']
    array_nested_fields = stats['array_nested']
    
    print("\n" + "=" * 120)
    print("📋 RAPPORT D'ANALYSE SUPABASE")
    print("=" * 120)
    
    # Résumé
    print(f"\n📊 STATISTIQUES GÉNÉRALES")
    print(f"   ├─ Total d'objets: {total_lines:,}")
    root_fields_count = len({k for k in field_types.keys() if '.' not in k})
    nested_fields_count = len({k for k in field_types.keys() if '.' in k})
    print(f"   ├─ Champs root: {root_fields_count}")
    print(f"   ├─ Champs imbriqués: {nested_fields_count}")
    print(f"   ├─ Tableaux détectés: {len(array_fields)}")
    print(f"   └─ Objets imbriqués: {len(nested_fields)}")
    
    # Champs principaux
    print(f"\n\n🌳 STRUCTURE HIÉRARCHIQUE")
    print("─" * 120)
    print(f"{'Champ':<40} {'Type SQL':<20} {'Présence':<15} {'Max Length':<15} {'Échantillon':<30}")
    print("─" * 120)
    
    root_fields = {k: v for k, v in field_types.items() if '.' not in k and k not in array_fields}
    for field in sorted(root_fields.keys()):
        types = field_types[field]
        presence_rate = (field_presence.get(field, 0) / total_lines) * 100
        sql_type = get_sql_type(types, stats['max_lengths'].get(field, 0))
        max_len = stats['max_lengths'].get(field, 0)
        sample = stats['samples'].get(field, [''])[0][:27] if stats['samples'].get(field) else 'N/A'
        
        presence_marker = "✓ 100%" if presence_rate > 99.5 else f"⚠️ {presence_rate:.1f}%"
        max_len_str = f"{max_len}" if max_len > 0 else "—"
        print(f"{field:<40} {sql_type:<20} {presence_marker:<15} {max_len_str:<15} {sample:<30}")
    
    # Objets imbriqués (avec un niveau de profondeur)
    if nested_fields:
        print(f"\n\n🔶 OBJETS IMBRIQUÉS (niveau 1)")
        print("─" * 120)
        for obj_field in sorted(nested_fields.keys()):
            nested_props = [k for k in field_types.keys() if k.startswith(f"{obj_field}.") and k.count('.') == 1]
            print(f"\n   📦 {obj_field} → {len(nested_props)} propriétés")
            for nested_prop in sorted(nested_props)[:8]:
                prop_name = nested_prop.replace(f"{obj_field}.", "")
                types = field_types[nested_prop]
                sql_type = get_sql_type(types, 0)
                presence_rate = (field_presence.get(nested_prop, 0) / total_lines) * 100
                marker = "✓" if presence_rate > 99 else f"⚠️ {presence_rate:.1f}%"
                print(f"       ├─ {prop_name:<35} → {sql_type:<20} {marker}")
            if len(nested_props) > 8:
                print(f"       └─ ... et {len(nested_props) - 8} autres")
    
    # Tableaux de données
    if array_fields:
        print(f"\n\n📚 TABLEAUX DÉTECTÉS ({len(array_fields)} tableaux)")
        print("─" * 120)
        for array_field in sorted(array_fields.keys()):
            if array_field in array_nested_fields:
                nested_data = array_nested_fields[array_field]
                print(f"\n   🔷 {array_field} → {len(nested_data)} colonnes/propriétés")
                for nested_field in sorted(nested_data.keys())[:10]:
                    types = dict(nested_data[nested_field])
                    sql_type = get_sql_type(types, 0)
                    print(f"      ├─ {nested_field:<35} → {sql_type}")
                if len(nested_data) > 10:
                    print(f"      └─ ... et {len(nested_data) - 10} autres")

def print_sql_recommendations(stats):
    """Génère les recommandations SQL"""
    
    field_types = stats['fields']
    field_presence = stats['presence']
    total_lines = stats['total']
    nested_fields = stats['nested']
    array_fields = stats['arrays']
    array_nested_fields = stats['array_nested']
    
    print(f"\n\n" + "=" * 120)
    print("🗄️  SCHÉMA SQL SUPABASE RECOMMANDÉ")
    print("=" * 120)
    
    field_types = stats['fields']
    field_presence = stats['presence']
    total_lines = stats['total']
    array_fields = stats['arrays']
    array_nested_fields = stats['array_nested']
    
    sql_lines = []
    sql_lines.append("-- ================================")
    sql_lines.append("-- Schéma SQL Supabase Dofus")
    sql_lines.append("-- ================================\n")
    
    print("\n📝 SQL - TABLE PRINCIPALE:\n")
    print("CREATE TABLE monsters (")
    sql_lines.append("CREATE TABLE monsters (")
    print("  id BIGSERIAL PRIMARY KEY,")
    sql_lines.append("  id BIGSERIAL PRIMARY KEY,")
    
    # Collecter les champs root (pas imbriqués ni tableaux)
    root_fields = sorted({k for k in field_types.keys() if '.' not in k and k not in array_fields})
    
    for i, field in enumerate(root_fields):
        types = field_types[field]
        presence_rate = (field_presence.get(field, 0) / total_lines) * 100
        sql_type = get_sql_type(types, stats['max_lengths'].get(field, 0))
        
        nullable = presence_rate < 100
        constraint = "," if i < len(root_fields) - 1 else ","
        null_str = f" {constraint}" if nullable else " NOT NULL,"
        
        # Formater le commentaire
        presence_comment = f"  -- {presence_rate:.1f}% present" if presence_rate < 100 else ""
        line = f"  {field} {sql_type}{null_str}{presence_comment}"
        print(line)
        sql_lines.append(line)
    
    print("  created_at TIMESTAMP DEFAULT NOW(),")
    sql_lines.append("  created_at TIMESTAMP DEFAULT NOW(),")
    print("  updated_at TIMESTAMP DEFAULT NOW()")
    sql_lines.append("  updated_at TIMESTAMP DEFAULT NOW()")
    print(");\n")
    sql_lines.append(");\n")
    
    # Tables pour les tableaux
    if array_nested_fields:
        for i, array_field in enumerate(sorted(array_nested_fields.keys())):
            # Générer un nom de table approprié (sans caractères spéciaux)
            safe_name = array_field.replace('.', '_').replace('Array', '').strip('_').lower()
            table_name = f"monster_{safe_name}"
            
            print(f"\n-- Table pour le tableau: {array_field}")
            sql_lines.append(f"\n-- Table pour le tableau: {array_field}")
            print(f"CREATE TABLE {table_name} (")
            sql_lines.append(f"CREATE TABLE {table_name} (")
            print(f"  id BIGSERIAL PRIMARY KEY,")
            sql_lines.append(f"  id BIGSERIAL PRIMARY KEY,")
            print(f"  monster_id BIGINT NOT NULL REFERENCES monsters(id) ON DELETE CASCADE,")
            sql_lines.append(f"  monster_id BIGINT NOT NULL REFERENCES monsters(id) ON DELETE CASCADE,")
            
            nested_data = array_nested_fields[array_field]
            fields_list = sorted(nested_data.keys())
            for j, nested_field in enumerate(fields_list):
                types = dict(nested_data[nested_field])
                sql_type = get_sql_type(types, 0)
                is_last = (j == len(fields_list) - 1)
                line = f"  {nested_field} {sql_type}{',' if not is_last else ','}"
                print(line)
                sql_lines.append(line)
            
            print(f"  created_at TIMESTAMP DEFAULT NOW()")
            sql_lines.append(f"  created_at TIMESTAMP DEFAULT NOW()")
            print(f");\n")
            sql_lines.append(f");\n")
    
    # Index recommandés
    if array_nested_fields:
        print("\n-- INDEX RECOMMANDÉS")
        sql_lines.append("\n-- INDEX RECOMMANDÉS")
        for array_field in sorted(array_nested_fields.keys()):
            safe_name = array_field.replace('.', '_').replace('Array', '').strip('_').lower()
            table_name = f"monster_{safe_name}"
            line = f"CREATE INDEX idx_{table_name}_monster_id ON {table_name}(monster_id);"
            print(line)
            sql_lines.append(line)
        print()
    
    # Exporter dans un fichier
    sql_file = Path("supabase_schema.sql")
    with open(sql_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(sql_lines))
    
    print(f"\n✅ Schéma SQL exporté dans: {sql_file}\n")

def print_import_guide(stats):
    """Affiche un guide d'import"""
    
    print(f"\n\n" + "=" * 120)
    print("📥 GUIDE D'IMPORT SUPABASE")
    print("=" * 120)
    
    print(f"""
1️⃣ CRÉATION DES TABLES
   • Exécuter le SQL généré ci-dessus dans Supabase
   • Attention: Respecter l'ordre (tables parentes d'abord)

2️⃣ EXPORTATION DES DONNÉES
   • Générer des fichiers CSV/JSONL à partir du JSON
   • Voir script d'export_data.py pour convertir les structures imbriquées

3️⃣ IMPORT DANS SUPABASE
   • Via Supabase UI: Console SQL ou Data Upload
   • Via PostgREST API: INSERT en batch
   • Via Python: supabase-py avec batch operations

4️⃣ OPTIMISATIONS POST-IMPORT
   • Ajouter des index sur les colonnes fréquemment filtrées
   • Configurer les RLS (Row Level Security) si nécessaire
   • Mettre en place les triggers pour les champs updated_at

📌 NOTES IMPORTANTES:
   • Les champs avec "Array" et "Array" imbriqués → tables séparées
   • Les objets complexes → stocker en JSONB si pas de requête spécifique
   • Les IDs (rid) → PRIMARY KEY ou FOREIGN KEY selon contexte
""")

# Utilisation
if __name__ == "__main__":
    print("\n" + "=" * 120)
    print("🚀 ANALYSEUR JSON DOFUS POUR SUPABASE")
    print("=" * 120 + "\n")
    
    stats = analyze_json_structure('monsters.json')
    
    if stats:
        print_report(stats)
        print_sql_recommendations(stats)
        print_import_guide(stats)
        print("\n" + "=" * 120 + "\n")
