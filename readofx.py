# https://gist.github.com/whistler/e7c21c70d1cbb9c4b15d
# https://pypi.org/project/ofxparse/
# https://github.com/Fluxo-Resultados/fluxo-ofx-parser

# Python Includes
import os
from datetime import datetime
from tkinter import messagebox
import fluxo_ofx_parse.ofxparse as ofxparse
import logging

# Project Includes
import apswSql as sql
#from util import messageWindow
#from finMsgBox import dupPopup
from finAlias import getAliasOfx

DATE_FORMAT = '%Y-%m-%d' 

def accountName(accountId):
    data, columns, err = sql.accounts(accountId)
    if data:
        return data[0]["OrganizationName"]
    else:
        return ""
    return ""


def getLastDate(actName):
    # Get the newest date for account to prevent duplicates
    query = "SELECT MAX(Date) FROM transactions WHERE Account = '"+actName+"';"
    data, cols, err = sql.sqlQuery(query, [])
    logging.info("getlastdate %s",data[0][0])
    if "None" in str(data[0]):
        logging.info("Last date = now")
        dt = datetime.now()
    else:    
        logging.info("Last Date %s", data[0])
        dt = datetime.strptime(data[0][0], '%Y-%m-%d')
    a = int(dt.strftime('%Y%m%d'))
    logging.info("getLastDate  %s", a)
    return a


def get_bank_statement_from_ofx(account):
    balance = account.statement.balance

    statement = []
    credit_transactions = ['credit', 'dep', 'int', 'directdep']
    debit_transactions  = ['debit', 'atm', 'pos', 'xfer', 'check', 'fee', 'payment']

    for transaction in account.statement.transactions:
        credit = ""
        debit = ""
        balance = balance + transaction.amount
        if transaction.type in credit_transactions:
            credit = transaction.amount
        elif transaction.type in debit_transactions:
            debit = -transaction.amount
        else:
            raise ValueError("Unknown transaction type:" + transaction.type)
        try:
            line = {
                'Date': transaction.date.strftime(DATE_FORMAT),
                'Payee': transaction.payee,
                'Type': transaction.type,
                'Memo': transaction.memo,
                'UID': transaction.id,
                'Amount': str(transaction.amount),
                'sic': transaction.sic,
                'mcc': transaction.mcc,
                'Debit': str(debit),
                'Credit': str(credit),
                'Balance': str(balance),
                'CheckNum': str(transaction.checknum),
                'FID': account.institution.fid,
                'Organization': account.institution.organization}
        except Exception as error:
            logging.error('Try without FID or ORG ',error)  #Fid/ORG may be present in QFX but not OFX files
            line = {
                'Date': transaction.date.strftime(DATE_FORMAT),
                'Payee': transaction.payee,
                'Type': transaction.type,
                'Memo': transaction.memo,
                'UID': transaction.id,
                'Amount': str(transaction.amount),
                'sic': transaction.sic,
                'mcc': transaction.mcc,
                'Debit': str(debit),
                'Credit': str(credit),
                'Balance': str(balance),
                'CheckNum': str(transaction.checknum),
                'FID': "",
                'Organization': ""}
        statement.append(line)
        
    return statement

def get_investment_transactions_statement_from_ofx(ofx):
    statement = []
    for transaction in ofx.account.statement.transactions:
        line = {
            'type': getattr(transaction, 'type', ''),
            'tradeDate': getattr(transaction, 'tradeDate', ''),
            'settleDate': getattr(transaction, 'settleDate', ''),
            'memo': getattr(transaction, 'memo', ''),
            'income_type': getattr(transaction, 'income_type', ''),
            'units': getattr(transaction, 'units', ''),
            'unit_price': getattr(transaction, 'unit_price', ''),
            'comission': getattr(transaction, 'comission', ''),
            'fees': getattr(transaction, 'fees', ''),
            'total': getattr(transaction, 'total', ''),
            'tferaction': getattr(transaction, 'tferaction', '')
        }
        line.update(get_security_info(getattr(transaction, 'security', ''), ofx))
        statement.append(line)
    return statement


def get_security_info(sec_id, ofx):
    sec_dict = {
        'securityid':'',
        'securityname': '',
        'securityticker': '',
        'securitymemo': ''
    }
    if sec_id == '' or sec_id is None:
        return sec_dict
    for sec in ofx.security_list:
        if sec.uniqueid == sec_id :
            sec_dict['securityid'] = getattr(sec,'uniqueid','')
            sec_dict['securityname'] = getattr(sec,'name','')
            sec_dict['securityticker'] = getattr(sec,'ticker','')
            sec_dict['securitymemo'] = getattr(sec,'memo','')
            return sec_dict


def get_statement_from_ofx(ofx):
    if isinstance(ofx.account.statement, ofxparse.ofxparse.InvestmentStatement):
        return get_investment_transactions_statement_from_ofx(ofx)
    else:
        return get_bank_statement_from_ofx(ofx)
 
def check_duplicate(date, amount, actName, description, uid):
    logging.info('chkdup  %s %s %s %s %s', date, amount, actName, description, uid)
    try:

        desc = description.replace("'","''")        # escape single quote if exists
        data, col, err = sql.sqlQuery("SELECT Id, Date, Alias, Amount, Account, Description, UiD  FROM transactions WHERE Account = '"+actName+"' AND Date = '"+date+"' AND Amount = '"+amount+"' AND Description = '"+desc+"';")
        #sql.saveDatabase()
        #logging.info(data)
        #logging.info(len(data))
        if len(data)==1: data = data[0]
        logging.info(data)    
        if data:
            data1 = ["Existing Data"]+list(data)
            amt = format(float(data1[4]), '.2f')
            data1[4] = amt
            logging.info(data1)    
            newData = ["New Data"]
            newData.append("")
            newData.append(date)
            newData.append("")
            newData.append(amount)
            newData.append(actName)
            newData.append(description)
            newData.append(uid)
            
            #dpopup = dupPopup("", data1, newData)
            #result = dpopup.show()
            
            return False
        else:
            return True     # no existing data

    except Exception as error:
        logging.exception("Failed to insert data into table %s", error)
        messagebox.showerror("ERROR", error)
        return False
    return False
                
def accountData(account):   #, accountList):

    rc = -1
    try:
        '''
        logging.info('account_id %s',account.account_id )       # The account number
        logging.info('number %s',account.number )           # The account number (deprecated -- returns account_id)
        logging.info('routing_number %s',account.routing_number)    # The bank routing number
        logging.info('branch_id %s',account.branch_id)         # Transit ID / branch number
        logging.info('type %s',account.type)              # An AccountType object
        '''
        statement = account.statement          # A Statement object
        '''logging.info('start_date %s',statement.start_date  )        # The start date of the transactions
        logging.info('end_date %s',statement.end_date  )          # The end date of the transactions
        logging.info('balance %s',statement.balance )            # The money in the account as of the statement date
        '''
        account.institution
                       
        tableList = sql.tableData('accounts')
        accId = str(account.account_id)
        str(account.routing_number)
        match = False
        sqlA.encdec()
        for actIdx in tableList:
            if str(actIdx[1]) == accId:
                match = True
                rc = 0
                break
                
        if match == False:
            logging.warning("Account not found %s", accId)
            messaebox.showerror("ERROR", "Account not found" )
            rc = "Account not found"
                
    except Exception as error:
        logging.exception("Failed to insert data into table %s", error)
        messagebox.showerror("ERROR", error)
        rc = error
          
    finally:
        #sql.saveDatabase()
        return rc  #, actIdx

def addStmt(statement, actName, progbar=""):

    #statement = get_bank_statement_from_ofx(account)
    logging.info("bankstatement length %d",len(statement))
    try:
        getLastDate(actName)
        if len(statement) > 0:
            100/len(statement)
            for stmt in statement:
                logging.info('statement %s', stmt)
                aDate = stmt["Date"]
                dt = datetime.strptime(aDate, '%Y-%m-%d')
                int(dt.strftime('%Y%m%d'))

                aAlias = ""
                aPayee = stmt["Payee"]
                aAmount = stmt["Amount"]
                aType = stmt["Type"]
                stmt["Balance"]
                aCheckNum = stmt["CheckNum"]
                aCategory = ""
                aSubCat = ""
                stmt["Memo"]
                aNotes = ""
                aTags = ""
                aAccount = actName
                aUID = stmt["UID"]
                
                #dup = check_duplicate(aDate, aAmount, aAccount, aPayee, aUID)
                #if dup == False: continue

                aAlias, aCategory, aSubCat = getAliasOfx(stmt, actName)    
                record = [aDate, aAlias, aCheckNum, aType, aAmount, aCategory, aSubCat, aNotes, aTags, aAccount, aPayee, aUID]

                stmt = "INSERT OR IGNORE INTO transactions (Date, Alias, Number, Type, Amount, Category, Subcategory, Notes, Tags, Account, Description,  UID) VALUES (?,?,?,?,?,?,?,?,?,?,?,?);"                
                rc = sql.sqlExecute(stmt, record)
                logging.info(rc)

            messagebox.showinfo("INFO", "Done Adding Items")
            
    except Exception as ex:
            logging.exception('error %s',ex)
            message =  type(ex).__name__, str(ex), 'In', os.path.basename(__file__), 'On Line', ex.__traceback__.tb_lineno
            messagebox.showerror("ERROR", message)
                
    #sql.saveDatabase()   

    
def ofx2Array(ofx_file, progbar=""):
    try:
        logging.info('ofx2Arry %s',ofx_file)

        ofx = ofxparse.OfxParser.parse(open(ofx_file, encoding="latin-1"))
        #accountList = ofx.account
        account = ofx.account
        rc = accountData(account)
        if rc == 0:
            sql.tableData('Accounts')
            actName = accountName(account.account_id)
            # search for account in table
            '''
            for x in tableList:
                logging.info('%s  --- %s *** %s ',x[0],x[1], x[ACTNAME])
                #if str(x[1]) == actEncrypt:
                if str(x[1]) == account.account_id:
                    actName = x[ACTNAME]
                    break
            '''        
            #maxDate = sql.getLastDate(actName)
            #logging.info(' %s', maxDate)
            
            statement = get_bank_statement_from_ofx(account)
            addStmt(statement, actName, progbar)
            logging.info("bankstatement length %d",len(statement))

        else:
            logging.info('Error %s',rc)
        #===============================

    except Exception as error:
        logging.exception("Error %s", error)
        messagebox.showerror("ERROR", error)
        rc = error
          
    finally:
        sql.saveDatabase()
        return rc
