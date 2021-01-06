import json,requests,os

rootPath = os.path.dirname(os.path.abspath(__file__))
dataPath = rootPath+'/data'
histPath = dataPath+'/hist/'
configPath = dataPath + '/config.json'
configJson = json.load(open(configPath))
presetPath = dataPath + '/preset.json'
presetJson = json.load(open(presetPath))
quotePath = dataPath + '/quote.json'
quoteJson = json.load(open(quotePath))
histFileList = os.listdir(histPath)
imgPath = dataPath+'/analysis_img/'
ImgFiles = os.listdir(imgPath)

url = 'https://notify-api.line.me/api/notify'

def sendNotifyMassage (token,text):
    print('Sending Massage')
    headers = {'Authorization': 'Bearer ' + token}
    r = requests.post(url, headers=headers , data = {'message':'\n'+text})
    print (r.text)

def sendNotifyImageMsg (token,imagePath,text):
    print('Sending Image {}'.format(imagePath))
    headers = {'Authorization': 'Bearer ' + token}
    r = requests.post(url, headers=headers ,data = {'message':'\n'+text}, files = {'imageFile':open(imagePath,'rb')})
    print (r.text)

def signalReportToUser(*_):
    import datetime as dt
    date = dt.date.today().strftime('%d/%m/%Y')
    import stockAnalysis
    for user in configJson:
        if bool(configJson[user]['active']):
            token = configJson[user]['lineToken']
            preset = configJson[user]['preset']
            description = configJson[user]['description']

            # Load Preset
            ps_value = presetJson[preset]["value"]
            ps_priceMin = presetJson[preset]["priceMin"]
            ps_priceMax = presetJson[preset]["priceMax"]
            ps_sma = presetJson[preset]["SMA"]
            ps_breakout_high = presetJson[preset]["breakOutH"]
            ps_breakout_low = presetJson[preset]["breakOutL"]

            print('sending to {} ({}) preset \"{}\"'.format(user,description,preset))

            #Send Summary
            signalS = stockAnalysis.getSignalFromPreset(preset)

            #Buy Most Active Filter
            buyActive = []
            buyInActive = []
            for quote in signalS['BUY']:
                csvPath = histPath + quote + '.csv'
                dataS = stockAnalysis.getAnalysisSetFromCSV(csvPath, ps_value, ps_priceMin, ps_priceMax, ps_sma, ps_breakout_high,
                                                    ps_breakout_low)
                if dataS['HIGH VOL W CHG'] > 0:
                    buyActive.append(quote)
                else:
                    buyInActive.append(quote)

            #Message Text
            text_buy_active = '△+ \n{}\n'.format(' '.join(buyActive))
            text_buy = '△- \n{}\n'.format(' '.join(buyInActive))
            text_side = '◁ ▷ \n{}\n'.format(' '.join(signalS['SIDE']))
            text_sell = '▽ \n{}\n'.format(' '.join(signalS['SELL']))

            msg_signal = date + '\n' \
                                '' + text_buy_active + text_buy + text_side + text_sell
            sendNotifyMassage(token,msg_signal)
            
            #Send Img
            for f in ImgFiles:
                if f.__contains__(preset):
                    quote = f.split('_')[-1][:-len('.png')]
                    print('sending {} to {} ({})'.format(quote, user, description))
                    csvPath = histPath+quote+'.csv'

                    # Load Quote Data
                    dataS = stockAnalysis.getAnalysisSetFromCSV(csvPath, ps_value, ps_priceMin, ps_priceMax, ps_sma, ps_breakout_high,
                                                    ps_breakout_low)

                    price = dataS['PRICE']
                    chage = dataS['CHG% M']
                    breakout_high = dataS['BreakOut H']
                    stop = dataS['STOPLOSS']
                    trailling = dataS['TRAILLING%']
                    volume_w_chg = round(dataS['HIGH VOL W CHG'] / 1000000, 1)
                    value_w_chg = round(price * volume_w_chg, 1)

                    q_msg = '▹ {} {}   \nMonth Chg {}% \nBreak Out High {}\nStoploss {}  Trailling {}%\n' \
                            'Week Chg Vol {}m / Val {}m'.format(quote, price, chage, breakout_high, stop, trailling,
                                                                volume_w_chg, value_w_chg)
                    #print (q_msg)
                    #try send image with timeout checking
                    timeOut = 3
                    for i in range(3):
                        try:
                            sendNotifyImageMsg(token,imgPath+f,q_msg)
                            break
                        except:
                            if i >= timeOut:
                                break
                            else:
                                pass

if __name__=='__main__':
    #sendNotifyMassage('Fq2uIz8AnqmCS2J9eA6ttmVhY1dfDdPp7lzAlsrDc44','test')
    #sendNotifyImageMsg('Fq2uIz8AnqmCS2J9eA6ttmVhY1dfDdPp7lzAlsrDc44','C:/Users/DEX3D_I7/Pictures/UglyDolls2_1.mp4_snapshot_01.17.998.jpg',"asfdfas")

    import update
    update.updatePreset()
    presetPath = dataPath + '/preset.json'
    presetJson = json.load(open(presetPath))

    signalReportToUser()
    pass