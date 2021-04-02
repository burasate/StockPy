#For Update Stock Profile from csv

import csv,os,json
import requests
from bs4 import BeautifulSoup

rootPath = os.path.dirname(os.path.abspath(__file__))
dataPath = rootPath+'/data'

quote_set = {

}

with open('data/quoteList.csv') as csvfile:
    reader = csv.reader(csvfile)
    line = 0
    for row in reader:
        if line == 0 :
            line += 1
            pass
        else :
            print(row[0])
            quote = row[0]

            r = requests.get(
                'https://www.set.or.th/set/companyprofile.do?symbol='+quote+'&ssoPageId=4&language=en&country=US')
            c = r.content
            soup = BeautifulSoup(c, 'html.parser')

            try :
                name_data = soup.find_all('div', {'class', 'col-xs-12 col-md-12 col-lg-8'})
                name = str(name_data[0].text).split(':')
                name = name.pop().replace('\n', '')
                name = name.strip().capitalize()
                print(name)

                profile_data = soup.find_all('div', {'class', 'col-xs-9 col-md-5'})
                p_e = str(profile_data[0].text).strip()
                dvd_y = str(profile_data[1].text).strip()
                pbv = str(profile_data[2].text).strip()
                market_cap = str(profile_data[3].text).strip()
                market = str(profile_data[4].text).strip()
                industry = str(profile_data[5].text).strip()
                sector = str(profile_data[6].text).strip()
                ipo_date = str(profile_data[7].text).strip()
                par_value = str(profile_data[8].text).strip()
                auth_cap = str(profile_data[9].text).strip()
                paid_up_cap = str(profile_data[10].text).strip()

                quote_set[quote] = {
                    'Name' : name,
                    'Industry' : industry,
                    'Sector' : sector,
                    'Market' : market,
                    'P/E' : p_e,
                    'Dividend' : dvd_y,
                    'P/BV' : pbv,
                    'Market Cap' : market_cap,
                    'Par' : par_value,
                    'Authorized Capital' : auth_cap,
                    'Paid-up Capital' : paid_up_cap
                }
                print(quote_set[quote])

                try:
                    with open('data/quote.json', 'x') as outfile:
                        json.dump(quote_set, outfile, indent=4)
                except:
                    with open('data/quote.json', 'w') as outfile:
                        json.dump(quote_set, outfile, indent=4)
            except :
                pass
            #break