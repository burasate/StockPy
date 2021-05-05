import json,time,csv,requests,os
from datetime import datetime as dt
from bs4 import BeautifulSoup
import pandas as pd

rootPath = os.path.dirname(os.path.abspath(__file__))
dataPath = rootPath+'/data'

with open(dataPath+'/quote.json', 'r') as f:
    quote_list = json.load(f)

def LoadHist (Quote,connectCount = 5):
    df = pd.DataFrame()
    url = 'https://www.settrade.com/C04_02_stock_historical_p1.jsp?txtSymbol={}&ssoPageId=10&&selectPage=2&max=101&offset=0'.format(Quote)
    #url = 'https://finance.yahoo.com/quote/' + Quote + '.BK/history'
    for i in range(connectCount):
        try :
            r = requests.get(url,timeout=30)
        except : print ('timed out')
        else : break
    c = r.content
    soup = BeautifulSoup(c, 'html.parser')
    price_data = soup.find_all('tbody')
    index = 0
    #print(price_data[0].find_all('tr'))
    for row in price_data[0].find_all('tr'):
        col = row.find_all('td')

        df = df.append(pd.DataFrame({
            'Day' : [100 - index],
            'Date' : [col[0].get_text()],
            'Open' : [col[1].get_text()],
            'High' : [col[2].get_text()],
            'Low' : [col[3].get_text()],
            'Close' : [col[5].get_text()],
            'adjClose' : [col[5].get_text()],
            'Volume' : [float(str(col[8].get_text()).replace(',', ''))*1000]
        }))
        index += 1
    df.reset_index(inplace=True,drop=True)
    print(df[['Date','Close','Volume']].iloc[0])
    df.to_csv(dataPath+'/hist/'+Quote+'.csv',index=False)

"""
def LoadHist (Quote) :
    Historical_List = [['Day','Date','Open','High','Low','Close','adjClose','Volume']]
    #url = 'https://finance.yahoo.com/quote/' + Quote + '.BK/history?interval=1d&filter=history&frequency=1d'
    url = 'https://finance.yahoo.com/quote/' + Quote + '.BK/history'

    for i in range(5):
        try :
            r = requests.get(url,timeout=15)
        except : print ('timed out')
        else : break

    c = r.content
    soup = BeautifulSoup(c, 'html.parser')

    price_data = soup.find_all('tbody')
    index = 0
    for table in price_data:
        for row in table:
            col = row.find_all('td')
            #print(col)
            try:
                Day = 100 - index
                Date = col[0].text
                Open = col[1].text
                High = col[2].text
                Low = col[3].text
                Close = col[4].text
                adjClose = col[5].text
                Volume = str(col[6].text).replace(',','')
                if Volume != '-':
                    #print([Day,Date, Open, High, Low, Close, adjClose, Volume])
                    Historical_List.append([Day,Date, float(Open), float(High), float(Low), float(Close), float(adjClose), float(Volume)])
                    index += 1
                if index < 3:
                    print([Day,Date, Open, High, Low, Close, adjClose, Volume])
                    #print(len(Volume))
                    pass
            except : pass

    if len(Historical_List) > 1 :
        try:
            with open(dataPath+'/hist/'+Quote+'.csv', 'x',newline='') as outfile:
                writer = csv.writer(outfile, delimiter=',')
                writer.writerows(Historical_List)
        except:
            with open(dataPath+'/hist/'+Quote+'.csv', 'w', newline='') as outfile:
                writer = csv.writer(outfile, delimiter=',')
                writer.writerows(Historical_List)
"""

def LoadSetHist() :
    today = dt.today().strftime('%Y-%m-%d')
    r = requests.get('https://marketdata.set.or.th/mkt/marketsummary.do?language=en&country=US')
    c = r.content
    soup = BeautifulSoup(c, 'html.parser')
    data = soup.find_all('div',{'class','col-xs-4 text-right'})

    csv_data = []  # prepre list of data
    csv_file = 'setIndexPerformanceHist.csv'  # File Name
    # open csv checking if has csv file
    try:
        csv_f = open(rootPath+os.sep+'data'+os.sep+csv_file, 'r')
        csv_reader = csv.reader(csv_f, delimiter=',')
        for i in csv_reader:
            if i[0] != today:
                csv_data.append(i)
        csv_f.close()
    # have no csv file
    except:
        # HEADER SETUP
        header_list = ['Date','3Month','6Month','YTD']
        csv_data.append(header_list)

    col_append = []
    col_append.append(today)
    col = 0
    for i in data:
        try:
            x = i.find_all('font')
            #print(x[0].text)
            col_append.append(str(x[0].text).replace('%',''))
        except:pass
        col = col+1

    csv_data.append(col_append)
    #print(csv_data)
    print('SET Index Performance  {}\n3M : {}%\n6M : {}%\nYTD : {}%'.format(col_append[0],col_append[1],col_append[2],col_append[3]))
    #print(header_list)
    #print(col_append)

    try:
        with open(rootPath+os.sep+'data'+os.sep+csv_file, 'x', newline='') as outfile:
            writer = csv.writer(outfile, delimiter=',')
            writer.writerows(csv_data)
            outfile.close()
    except:
        with open(rootPath+os.sep+'data'+os.sep+csv_file, 'w', newline='') as outfile:
            writer = csv.writer(outfile, delimiter=',')
            writer.writerows(csv_data)
            outfile.close()

def LoadAllHist():
    # Clear Directory
    imgPath = dataPath + '/hist/'
    oldHistory = os.listdir(imgPath)
    for f in oldHistory:
        os.remove(imgPath + f)

    start_time = dt.now()
    alphabets = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    count = 1
    succes_c = 0
    fail_c = 0
    for Char in alphabets:
        for i in quote_list:
            if i[0] == Char :
                os.system('cls||clear')
                print('{}/{}   {}'.format(count,len(quote_list),i))
                try:
                    LoadHist(i)
                    print('succesful')
                    succes_c += 1
                except:
                    print('failed')
                    fail_c += 1
                count += 1
    finish_time = dt.now()
    os.system('cls||clear')

    log_text = 'Data Loading Start {}\n' \
               'Data Loading Finish {}\n' \
               'Quote Count {}\n' \
               'Succesful {}\n' \
               'Fail {}\n'.format(start_time,finish_time,count,succes_c,fail_c)
    print (log_text)
    #LineNotify.sendNotifyMassage(log_text)

    try:
        with open(dataPath+'/load_stock_hist_log.txt', 'x') as outfile:
            json.dump(log_text, outfile)
    except:
        with open(dataPath+'/load_stock_hist_log.txt', 'w') as outfile:
            json.dump(log_text, outfile)

if __name__ == '__main__' :
    #LoadAllHist()
    #LoadSetHist()
    LoadHist('UNIQ')
    pass