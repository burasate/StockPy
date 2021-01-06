from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
import json
import os
import datetime as dt
from shutil import copyfile

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

def getAnalysisSetFromCSV(csvPath,valueFilter=100000000,priceMin=5,priceMax=150,SMA=10,breakOutH=55,breakOutL=20):
    quote = os.path.splitext(os.path.basename(csvPath))[0]

    # Read Data Frame
    df = pd.read_csv(csvPath)

    if df['Day'].count() < 50:
        #print('skip {} because not enough data'.format(quote))
        return None

    flag = ''
    date = dt.date.today().strftime('%d/%m/%Y')
    price = df['Close'][0]
    volume = df['Volume'][0]
    true_range = df['High'] - df['Low']
    avg_true_range = round(true_range.mean(), 2)
    median = (max(df['High']) + min(df['Low'])) / 2
    midian_range_pecentile = round(((df['Close'][0] - median) / df['Close'][0]) * 100)
    value = df['Volume'][0] * df['Close'][0]
    sma_s = round(df['Close'][0:SMA].mean(), 2)
    sma_l = round(df['Close'].mean(), 2)
    breakout_high = df['High'][1:breakOutH].max()
    breakout_low = df['Low'][1:breakOutL].min()
    breakout_mid = round((breakout_high + breakout_low) / 2, 2)
    breakout_midLow = round((breakout_mid + (breakout_low * 2)) / 3, 2)
    breakout_midHigh = round((breakout_mid + (breakout_high * 2)) / 3, 2)
    change_day = round(((df['Close'][0] - df['Close'][1]) / df['Close'][0]) * 100, 2)
    change_week = round(((df['Close'][0] - df['Close'][4]) / df['Close'][0]) * 100, 2)
    change_month = round(((df['Close'][0] - df['Close'][19]) / df['Close'][0]) * 100, 2)
    stop_loss = round(breakout_low - min(true_range), 2)
    trailling_stop = round(((breakout_high - breakout_low) / breakout_high) * 50)
    volume_high_week_change = df['Volume'][0:9].max() - df['Volume'][10:19].max()
    value_high_week_change = volume_high_week_change * price
    board_lot = price * 100

    # Signal Condition
    condition_filter = (
            value > valueFilter and
            price > priceMin and price < priceMax
    )
    condition_buy = (
            sma_s > sma_l and
            df['Close'][df['Close'].count() - 1] < median and
            price > breakout_midLow  # and
    )
    condition_sell = (
            sma_s < sma_l and
            price < median and
            df['Close'][df['Close'].count() - 1] > median  # and
    )
    if condition_buy and condition_filter:
        flag = 'BUY'
    elif condition_sell and condition_filter:
        flag = 'SELL'
    elif condition_filter and not condition_sell and not condition_buy:
        flag = 'SIDE'

    # Data Set
    dataS = {
        'DATE' : date,
        'QUOTE' : quote,
        'PRICE': price,
        'CHG% D':change_day,
        'CHG% W':change_week,
        'CHG% M':change_month,
        'MID RANGE %':midian_range_pecentile,
        'ATR':avg_true_range,
        'HIGH VOL W CHG':volume_high_week_change,
        'HIGH VAL W CHG':value_high_week_change,
        'BreakOut H':breakout_high,
        'BreakOut MH':breakout_midHigh,
        'BreakOut M':breakout_mid,
        'BreakOut ML':breakout_midLow,
        'BreakOut L':breakout_low,
        'SMA1':sma_s,
        'SMA2':sma_l,
        'VOLUME':volume,
        'VALUE':value,
        'STOPLOSS':stop_loss,
        'TRAILLING%':trailling_stop,
        'BOARD LOT':board_lot,
        'FLAG':flag
    }

    if not condition_filter:
        return None

    return dataS

def getSignalFromPreset(presetName):
    buy_signal_list = []
    sell_signal_list = []
    side_signal_list = []

    # Scan from csv
    for file in histFileList:
        analysisData = getAnalysisSetFromCSV(histPath + file,presetJson[presetName]['value'],
                                             presetJson[presetName]['priceMin'],
                                             presetJson[presetName]['priceMax'],
                                             presetJson[presetName]['SMA'],
                                             presetJson[presetName]['breakOutH'],
                                             presetJson[presetName]['breakOutL'])
        if analysisData != None:
            if analysisData['FLAG']=='BUY':
                buy_signal_list.append(analysisData['QUOTE'])
            elif analysisData['FLAG']=='SELL':
                sell_signal_list.append(analysisData['QUOTE'])
            else:
                side_signal_list.append(analysisData['QUOTE'])
    dataS = {'BUY':buy_signal_list,'SELL':sell_signal_list,'SIDE':side_signal_list}
    return dataS

def plotIndicatorFromCSV(csvPath,preset,save=False):
    # Plot Indicator
    quote = os.path.splitext(os.path.basename(csvPath))[0]

    #Load Preset
    ps_value = presetJson[preset]["value"]
    ps_priceMin = presetJson[preset]["priceMin"]
    ps_priceMax = presetJson[preset]["priceMax"]
    ps_sma = presetJson[preset]["SMA"]
    ps_breakout_high = presetJson[preset]["breakOutH"]
    ps_breakout_low = presetJson[preset]["breakOutL"]

    # Load Signal
    signalS = getAnalysisSetFromCSV(csvPath,ps_value,ps_priceMin,ps_priceMax,ps_sma,ps_breakout_high,ps_breakout_low)

    # Read Data Frame
    df = pd.read_csv(csvPath)

    clh = (df['Close'] + df['High'] + df['Low']) / 3
    h_plt = df['High']
    l_plt = df['Low']
    clh_np = np.linspace(df['Close'][0], df['Close'][df['Day'].count() - 1], df['Day'].count())

    # create indicator
    bkh_plt = []
    bkl_plt = []
    bkm_plt = []
    bkmh_plt = []
    bkml_plt = []
    sma_plt = []
    sma_l_plt = []
    buy_point = []
    sell_point = []
    for i in range(df['Day'].count()):
        #print(df['Day'][i])
        breakout_h = df['High'][i:i+ps_breakout_high].max()
        breakout_l = df['Low'][i:i+ps_breakout_low].min()
        breakout_m = (breakout_h+breakout_l)/2
        breakout_mh = ((breakout_h*2)+breakout_m)/3
        breakout_ml = (breakout_m+(breakout_l*2))/3
        sma = df['Close'][i:i+ps_sma].mean()
        sma_l = df['Close'][i:i+df['Day'][i]].mean()

        bkh_plt.append(breakout_h)
        bkl_plt.append(breakout_l)
        bkm_plt.append(breakout_m)
        bkmh_plt.append(breakout_mh)
        bkml_plt.append(breakout_ml)
        sma_plt.append(sma)
        sma_l_plt.append(sma_l)

        if i !=0 and df['Close'][i] > bkmh_plt[-2] :
            buy_point.append((df['Day'][i],df['Close'][i]))
        if i !=0 and df['Close'][i] < bkml_plt[-2] :
            sell_point.append((df['Day'][i],df['Close'][i]))

    # Plot Figure
    fig = plt.figure(figsize=(21, 9), dpi=100)
    ax = plt.axes()
    ax.set_facecolor((1, 1, 1))
    fig.patch.set_facecolor((1, 1, 1))
    plt.subplots_adjust(left=0.04, bottom=0.05, right=0.98, top=0.90, wspace=0.20, hspace=0.20)
    plt.xlabel('Day')
    plt.ylabel('Price')

    # Text
    plt.title(quoteJson[quote]["Name"].upper() + '\n' +
              quoteJson[quote]["Market"] + ' - ' + quoteJson[quote]["Sector"],
              fontsize=20, color=(.4, .4, .4))
    plt.text(100, min(df['Low']), quote + ' : ' + str(signalS['PRICE']), size=50, ha='right', va='bottom', color=(.7, .7, .7))
    plt.text(100, min(df['Low']), 'by Burasate.U', size=12, ha='right', va='top', color=(.7, .7, .7))
    plt.text(min(df['Day'] - 3), max(df['High']),
             'Data From Yahoo Finance\n' + signalS['DATE'] + '\n\n' +
             'Price : {}\nVolume : {} M\n'.format(signalS['PRICE'], (signalS['VOLUME']) / 1000000) + '\n' +
             'Week Chg : {}%\nMonth Chg : {}%\n'.format(signalS['CHG% W'], signalS['CHG% M']) + '\n' +
             'Break Low : {}\nBreak High : {}\nTrailling {} - {}%\n'.format(signalS['BreakOut L'], signalS['BreakOut H'],
                                                                            signalS['TRAILLING%'] / 2, signalS['TRAILLING%']) + '\n' +
             'Volume Week Chg : {} M\nValue Week Chg : {} M Baht\n'.format(round(signalS['HIGH VOL W CHG'] / 1000000),
                                                                           round(
                                                                               signalS['HIGH VAL W CHG'] / 1000000)) + '\n' +
             'P/E : {}\nP/BV : {}\n'.format(quoteJson[quote]["P/E"], quoteJson[quote]["P/BV"]) +
             'Dividend : {}\nMarket Cap : {}\nPar : {}\n'.format(quoteJson[quote]["Dividend"],
                                                                 quoteJson[quote]["Market Cap"],
                                                                 quoteJson[quote]["Par"]) +
             'Authorized Capital : {}\nPaid-up Capital : {}\n'.format(quoteJson[quote]["Authorized Capital"],
                                                                      quoteJson[quote]["Paid-up Capital"])
             , size=14, ha='left', va='top', color=((.6, .6, .6)))
    plt.text(100, signalS['BreakOut L'], signalS['BreakOut L'], size=12, ha='left', va='center', color=((0.8, 0.4, 0)))
    plt.text(100, signalS['BreakOut H'], signalS['BreakOut H'], size=12, ha='left', va='center', color=((0.4, 0.8, 0)))

    #signal point
    for i in buy_point:
        plt.text(i[0],i[1] , i[1], size=12, ha='center', va='bottom', color=((0.4, 0.8, 0)))
    for i in sell_point:
        plt.text(i[0],i[1] , i[1], size=12, ha='center', va='top', color=((0.8, 0.4, 0)))

    # Line
    plt.plot(df['Day'], clh, color=(0, 0.4, 0.8), linewidth=1)
    plt.plot(df['Day'], h_plt, color=(0.5, 0.5, 0.5), linewidth=.2, linestyle='--')
    plt.plot(df['Day'], l_plt, color=(0.5, 0.5, 0.5), linewidth=.2, linestyle='--')
    plt.plot(df['Day'], clh_np, linewidth=1, color='grey', linestyle=':')

    plt.plot(df['Day'], bkh_plt, linewidth=1, color=(0.4, 0.8, 0), linestyle='--')
    plt.plot(df['Day'], bkl_plt, linewidth=1, color=(0.8, 0.4, 0), linestyle='--')
    plt.plot(df['Day'], bkm_plt, linewidth=1, color=(1, 0.8, 0), linestyle='--')
    plt.plot(df['Day'], bkmh_plt, linewidth=1, color=(0.4, 0.8, 0), linestyle=':')
    plt.plot(df['Day'], bkml_plt, linewidth=1, color=(0.8, 0.4, 0), linestyle=':')
    plt.plot(df['Day'], sma_plt, color=(0.2, 0.7, 1.0), linewidth=.5, linestyle='--')
    plt.plot(df['Day'], sma_l_plt, color=(0.7, 0.2, 0.5), linewidth=.5, linestyle='--')

    # Finally
    if save:
        savePath = dataPath+'/analysis_img/' + '_'.join([preset,quote]) + '.png'
        print(savePath)
        plt.savefig(savePath)
    else:
        plt.show()

    plt.close()

def getImageBuySignalAll(*_):
    #Clear Directory
    imgPath = dataPath+'/analysis_img/'
    oldImgFiles = os.listdir(imgPath)
    for f in oldImgFiles:
        os.remove(imgPath+f)

    for ps in presetJson:
        print('get signal from preset \"{}\"'.format(ps))
        signalS = getSignalFromPreset(ps)

        for q in signalS['BUY']:
            plotIndicatorFromCSV(histPath+q+'.csv',ps,True)


if __name__ == '__main__' :
    #getImageBuySignalAll()
    #import update
    #update.updatePreset()
    presetPath = dataPath + '/preset.json'
    presetJson = json.load(open(presetPath))
    plotIndicatorFromCSV(histPath + 'KCE' + '.csv', 'preset02', False)
    pass




