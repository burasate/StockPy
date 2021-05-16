import json,time,csv,requests,os,ast,pprint
from datetime import datetime as dt
from bs4 import BeautifulSoup
import pandas as pd
import gSheet,lineNotify

rootPath = os.path.dirname(os.path.abspath(__file__))
dataPath = rootPath+'/data'
histPath = dataPath+'/hist/'
configPath = dataPath + '/config.json'
configJson = json.load(open(configPath))
presetPath = dataPath + '/preset.json'
presetJson = json.load(open(presetPath))

def GetRealtime (Quote,connectCount = 5):
    df = pd.DataFrame()
    url = 'https://marketdata.set.or.th/mkt/stockquotation.do?symbol={}&ssoPageId=1&language=en&country=US'.format(Quote)
    for i in range(connectCount):
        try :
            r = requests.get(url,timeout=30)
        except :
            print ('timed out')
        else : break
    c = r.content
    soup = BeautifulSoup(c, 'html.parser')
    table = soup.find_all('tbody')

    data = {
        'dateTime' : dt.now().strftime('%Y-%m-%d %H:%M:%S'),
        'hour' : int(dt.now().strftime('%H')),
        'minute' : int(dt.now().strftime('%M')),
        'quote' : Quote
    }
    index = 0
    dataList = []
    for row in table[0].find_all('tr'):
        col = row.find_all('td')
        value = col[1].get_text()
        value = value.replace(',','')
        value = value.replace('+','')
        value = value.replace('\n','')
        value = value.replace('\r','')
        value = value.replace(' ','')
        #print(value)
        if value == '' or value == '-':
            value = '0'
        try:
            value = ast.literal_eval(value)
        except:
            pass
        dataList.append((col[0].get_text(),value))
        index += 1

    data['last'] = dataList[1][1]
    data['change'] = dataList[2][1]
    data['percentageChange'] = dataList[3][1]
    data['prior'] = dataList[4][1]
    data['open'] = dataList[5][1]
    data['high'] = dataList[6][1]
    data['low'] = dataList[7][1]
    data['volume'] = dataList[8][1]
    data['value'] = dataList[9][1] * 1000
    return data

def GetAllRealtime (recordData=True,cleanupData=True):
    signalData = gSheet.getAllDataS('SignalRecord')
    df = pd.read_csv(dataPath + '/signal.csv')
    df = df.append(
        pd.DataFrame.from_records(signalData)
    )
    df.drop_duplicates(['Date','Quote','Preset','Close'],keep='last',inplace=True)
    last_date = df['Rec_Date'].tail(1).tolist()[0]
    df = df[df['Rec_Date'] == last_date]
    df = df[df['Signal'] == 'Entry']
    df.reset_index(inplace=True)

    realtimeData = gSheet.getAllDataS('Realtime')
    df_realtime = pd.DataFrame.from_records(realtimeData)

    rec = []
    totalCount = range(df['Quote'].count())
    for i in totalCount:
        os.system('cls||clear')
        row = df.iloc[i]
        print( '{}/{}'.format( i+1,len( totalCount ) ) )
        print(row['Quote'])

        # Send Sell Buy from last
        sendBuy = df_realtime[(df_realtime['quote'] == row['Quote']) &
                              (df_realtime['preset'] == row['Preset'])].groupby(['quote', 'preset'])[
                'sendBuy'].tail(1).tolist()
        sendSell = df_realtime[(df_realtime['quote'] == row['Quote']) &
                              (df_realtime['preset'] == row['Preset'])].groupby(['quote', 'preset'])[
            'sendSell'].tail(1).tolist()
        if sendBuy != []:
            sendBuy = sendBuy[0]
        else:
            sendBuy = 0
        if sendSell != []:
            sendSell = sendSell[0]
        else:
            sendSell = 0

        #Fill Collumn
        data = GetRealtime(row['Quote'])
        if data != None:
            data['preset'] = row['Preset']
            data['breakHigh'] = row['BreakOut_H']
            data['breakLow'] = row['BreakOut_L']
            data['breakMidHigh'] = row['BreakOut_MH']
            data['breakMidLow'] = row['BreakOut_ML']
            data['signal'] = ''
            data['sendBuy'] = sendBuy
            data['sendSell'] = sendSell
            if data['last'] < data['breakMidLow'] and data['last'] > data['breakLow']:
                data['signal'] = 'Entry'
            elif data['last'] < data['breakLow']:
                data['signal'] = 'Exit'
            elif data['low'] < data['breakLow'] and data['last'] > data['breakLow']:
                data['signal'] = 'Entry'
            elif data['last'] > data['breakMidHigh']:
                data['signal'] = 'Entry'
            if data['signal'] == 'Entry' and data['sendBuy'] == 0:
                SendRealtimeSignal(row['Preset'], row['Quote'], 'buy', data['last'], data['breakLow'])
                data['sendBuy'] = 1
            elif data['signal'] == 'Exit' and data['sendSell'] == 0:
                SendRealtimeSignal(row['Preset'], row['Quote'], 'sell', data['last'], data['breakLow'])
                data['sendSell'] = 1
                data['sendBuy'] = 0
        rec.append(data)
        #convert row to list and add row
        rowData = pd.DataFrame.from_records([data]).values.tolist()[0]
        if recordData:
            gSheet.addRow('Realtime',rowData)
        pprint.pprint(data)
    if recordData and cleanupData:
        df_realtime = df_realtime.append( pd.DataFrame.from_records(rec) )
        df_realtime.drop_duplicates(['quote','preset','hour','minute'],keep='last',inplace=True)
        df_realtime['sendBuy'] = df_realtime.groupby(['quote', 'preset'])['sendBuy'].transform('last')
        df_realtime['sendSell'] = df_realtime.groupby(['quote', 'preset'])['sendSell'].transform('last')
        df_realtime = df_realtime.tail(10000)
        df_realtime.to_csv(dataPath+'/realtime.csv',index=False)
        while True:
            gSheet.updateFromCSV(dataPath+'/realtime.csv', 'Realtime')
            time.sleep(5)
            if gSheet.getAllDataS('Realtime') != []:
                break

def getTokenByPreset(preset):
    data = []
    for user in configJson:
        if configJson[user]['preset'] == preset and bool(configJson[user]['realtime']):
            token = configJson[user]['lineToken']
            data.append(token)
    return data

def SendRealtimeSignal(preset,quote,side,price,cut):
    tokenList = getTokenByPreset(preset)
    if tokenList == []:
        return None
    text = ''
    percentage_cutLoss = round( ((price-cut)/price)*100 ,2)
    if side.lower() == 'buy':
        text = 'Buy    {}    {}\nCut Loss    {} (▽{}%)'.format(quote,price,cut,percentage_cutLoss)
    elif side.lower() == 'sell':
        text = 'Sell    {}    {}'.format(quote,price)
    else:
        return None
    print('{}  {}'.format(preset,text))
    for token in tokenList:
        #print(token)
        lineNotify.sendNotifyMassage(token,text)
        pass

print('SET Real-Time Recorder')
time.sleep(60)
marketHour = [9,10,11,12,14,15,16,17]
if os.name == 'nt': #Windows
    while True:
        GetAllRealtime()
        #time.sleep(60*5)

else: #Raspi
    import update
    while True:
        try:
            update.updateAllFile()
            update.updateConfig()
            update.updatePreset()
            break
        except:
            pass
    while True:
        hour = int(dt.now().hour)
        weekDay = int(dt.now().weekday())
        if hour in marketHour and weekDay < 5:
            try:
                GetAllRealtime()
                #time.sleep(60*1)
            except: pass
        else:
            os.system('cls||clear')
            print('SET Market is Close')
            time.sleep(60*30)