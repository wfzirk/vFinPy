import json
import apsw
db_file = "database/test2026.db"
rules_file = "rules/rules.json"
conn = apsw.Connection(db_file)
password='fish2fry'
cur = conn.cursor()
cur.execute(f"PRAGMA key = '{password}';")

with open(rules_file, "r", encoding="utf-8") as f:
    data = json.load(f)

for rule in data["rules"]:
    conn.execute("""
        INSERT INTO rules (
            account,
            pattern,
            alias,
            category,
            subcategory,
            import_file_key
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        rule.get("account"),
        rule.get("pattern"),
        rule.get("alias"),
        rule.get("category"),
        rule.get("subcategory"),
        rule.get("import_file_key")
    ))

conn.close()