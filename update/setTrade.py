from settrade.openapi import Investor
import json,os

rootPath = os.path.dirname(os.path.abspath(__file__))
dataPath = rootPath+'/data'
histPath = dataPath+'/hist/'
sandboxPath = dataPath + '/sandbox.json'
sandboxJson = json.load(open(sandboxPath))

investor = Investor(
    app_id=sandboxJson['app_id'],                                 # Your app ID
    app_secret=sandboxJson['app_secret'], # Your app Secret
    broker_id=sandboxJson['broker_id'],
    app_code=sandboxJson['app_code'],
    is_auto_queue = False
)

equity = investor.Equity(sandboxJson['equity_account'])
account_info = equity.get_account_info()
portfolio = equity.get_portfolio()

import pprint
pprint.pprint (account_info)
pprint.pprint (portfolio)
#print(account_info)