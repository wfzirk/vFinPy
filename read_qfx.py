
# Python Includes
import re
from html import unescape

# 3rd Party Includes

# Project Includes
from logging_manager import get_logger
log = get_logger(__name__)

def read_qfx(path):
    try:
        #log.info(f"Parsing QFX: {path}")
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        def normalize_qfx_date(dt):
            return f"{dt[:4]}-{dt[4:6]}-{dt[6:8]}" if dt else ""

        def find(tag):
            m = re.search(rf"<{tag}>(.*)", text, flags=re.IGNORECASE)
            return m.group(1).strip() if m else ""

        text = re.sub(r"\r", "", text)
      
        account_info = {
            "Account ID": find("ACCTID") or "default_account",
            "Bank ID": find("BANKID"),
            "Branch ID": find("BRANCHID"),
            "ORG": find("ORG"),
            "FID": find("FID"),
            "Account Type": find("ACCTTYPE"),
            "Currency": find("CURDEF"),
            "Start Date": find("DTSTART"),
            "End Date": find("DTEND"),
        }

        blocks = re.findall(r"<STMTTRN>(.*?)</STMTTRN>", text, flags=re.DOTALL | re.IGNORECASE)

        '''def get(tag, block):
            m = re.search(rf"<{tag}>(.*)", block, flags=re.IGNORECASE)
            return m.group(1).strip() if m else ""
        '''
        # more readable and secure than previous version
        def get(tag: str, block: str, default: str = "") -> str:
            match = re.search(
                rf"<{re.escape(tag)}>(.+)",
                block,
                flags=re.IGNORECASE
            )

            return match.group(1).strip() if match else default

        statement = []
        for block in blocks:
            desc = get("NAME", block) or get("MEMO", block)
            statement.append({
                "date": normalize_qfx_date(get("DTPOSTED", block)),
                "amount": get("TRNAMT", block),
                "description": unescape(desc).strip(),
                "fitid": get("FITID", block),
                "type": get("TRNTYPE", block),
                "number": get("CHECKNUM", block),
            })

        return statement, account_info
    except Exception as e:
        log.error(e)
        raise
        
if __name__ == "__main__":        
    import time

    # Get current timestamp
    current_seconds = time.time()
    print(f"Seconds since epoch: {current_seconds}")
    start = time.perf_counter()
    
    statement, account_info = read_qfx(
    "D:/Documents/Financial/FinancialDataFiles/2026/EMsavings20260715.qfx")
    end = time.perf_counter()

    print(account_info)
    cnt = 0
    for stmt in statement:
        print(cnt, stmt["date"], stmt["description"])
    cnt+=1
    print(f"Elapsed time: {end - start} seconds")