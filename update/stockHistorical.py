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
    #url = 'https://www.settrade.com/th/equities/quote/super/historical-trading'
    url = 'https://classic.settrade.com/C04_02_stock_historical_p1.jsp?txtSymbol={}&ssoPageId=10&&selectPage=2&max=101&offset=0'.format(Quote)
    #url = 'https://www.settrade.com/C04_02_stock_historical_p1.jsp?txtSymbol={}&ssoPageId=10&&selectPage=2&max=101&offset=0'.format(Quote)
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
    #print(price_data)
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
    csv_data = [i for i in csv_data if len(i) >= 4]
    print('SET Index Performance  {}\n3M : {}%\n6M : {}%\nYTD : {}%'.format(csv_data[-1][0],csv_data[-1][1],csv_data[-1][2],csv_data[-1][3]))
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
    LoadHist('SUPER')
    pass