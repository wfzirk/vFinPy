# rules/rule_set.py

# Python Includes
import sys
from pathlib import Path
import fnmatch

# 3rd party includes

# Project Includes
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
import apswSql as sql
from logging_manager import get_logger
log = get_logger(__name__)

class RuleSet:

    def __init__(self):
        self.rules = []
        self.refresh()

    def refresh(self):

        self.rules, self.columns, _ = sql.sqlQueryDict("""
            SELECT
                rule_id,
                account,
                pattern,
                alias,
                category,
                subcategory,
                import_file_key
            FROM rules
            ORDER BY account, pattern
        """)


    def classify(self, description, account_name):
        cur, conn = sql.open_db()
        #log.info(f'classify {description}')
        desc = (description or "").upper()
        #account_name = (account_name or "").upper()

        query = "SELECT rule_id, account, pattern, alias, category, subcategory "\
            "FROM rules WHERE enabled = 1 AND account = '"+account_name+"';"
        rows, cols, _ = sql.sqlQueryDict(query)
        
        account_name = (account_name or "").upper()
        
        for rule in rows:
            acct_pattern = (rule["account"] or "*").upper()

            if not fnmatch.fnmatch(account_name, acct_pattern):
                continue

            pattern = (rule["pattern"] or "").upper()

            if fnmatch.fnmatch(desc, pattern):
                return (
                    rule["alias"] or "",
                    rule["category"] or "",
                    rule["subcategory"] or ""
                )

        return ("", "", "")

    def add_rule(
        self,
        account,
        pattern,
        alias,
        category,
        subcategory,
        import_file_key=None
    ):

        try:
            acct_name = sql.get_account_name(account) or account
        except Exception:
            acct_name = account

        sql.sqlExecute("""
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
            acct_name,
            pattern,
            alias,
            category,
            subcategory,
            import_file_key
        ))

    def delete_rule(self, rule_id):
        log.info(f'delete rule {rule_id}')
        sql.sqlExecute("DELETE FROM rules WHERE rule_id=?", (rule_id,))