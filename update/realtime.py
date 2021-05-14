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

def GetAllRealtime (*_):
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
    #print(df[['Date','Quote','Preset','Close']])

    rec = []
    totalCount = range(df['Quote'].count())
    for i in totalCount:
        os.system('cls||clear')
        row = df.iloc[i]
        print( '{}/{}'.format( i+1,len( totalCount ) ) )
        print(row['Quote'])
        data = GetRealtime(row['Quote'])
        if data != None:
            data['preset'] = row['Preset']
            data['breakHigh'] = row['BreakOut_H']
            data['breakLow'] = row['BreakOut_L']
            data['breakMidHigh'] = row['BreakOut_MH']
            data['breakMidLow'] = row['BreakOut_ML']
            data['signal'] = ''
            if data['last'] < data['breakMidLow'] and data['last'] > data['breakLow']:
                data['signal'] = 'Entry'
            elif data['last'] < data['breakLow']:
                data['signal'] = 'Exit'
            elif data['low'] < data['breakLow'] and data['last'] > data['breakLow']:
                data['signal'] = 'Entry'
            elif data['last'] > data['breakMidHigh']:
                data['signal'] = 'Entry'
        rec.append(data)
        #convert row to list and add row
        rowData = pd.DataFrame.from_records([data]).values.tolist()[0]
        gSheet.addRow('Realtime',rowData)
        pprint.pprint(data)
    realtimeData = gSheet.getAllDataS('Realtime')
    df_realtime = pd.DataFrame.from_records(realtimeData)
    df_realtime = df_realtime.append( pd.DataFrame.from_records(rec) )
    df_realtime = df_realtime.tail(10000)
    df_realtime.to_csv(dataPath+'/realtime.csv',index=False)
    gSheet.updateFromCSV(dataPath+'/realtime.csv', 'Realtime')

marketHour = [9,10,11,12,14,15,16,17]
if os.name == 'nt': #Windows
    while True:
        GetAllRealtime()
        #time.sleep(60*5)

else: #Raspi
    import update
    while True:
        try:
            update.updateConfig()
            update.updatePreset()
            update.updateAllFile()
            break
        except:
            pass
    while True:
        hour = int(dt.now().hour)
        if hour in marketHour:
            try:
                GetAllRealtime()
                #time.sleep(60*1)
            except: pass
        else:
            os.system('cls||clear')
            print('SET Market is Close')
            time.sleep(60*30)

if __name__ == '__main__' :
    #GetRealtime('SSP')
    pass