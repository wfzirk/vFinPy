# rules/rule_manager.py

from logging_manager import get_logger
from .rule_set import RuleSet

log = get_logger(__name__)

print("rule_manager", __name__)


class RuleManager:

    def __init__(self):
        log.info(f"{__name__} loaded")

    def load(self):
        """
        Return a RuleSet object backed by the SQL database.
        """
        log.info("Loading rules from database")
        return RuleSet()

    def save(self, rule_set=None):
        """
        Legacy compatibility method.

        Rules are written directly to the database by
        RuleSet.add_rule(), update_rule(), delete_rule(), etc.

        Nothing to save.
        """
        log.info("save() called - rules already stored in database")
        return True