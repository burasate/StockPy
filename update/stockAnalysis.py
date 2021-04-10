from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
import json
import os
import datetime as dt
from shutil import copyfile
import gSheet

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
analysisHistPath = dataPath + '/analysis_hist'

def getAnalysis(csvPath,preset,saveImage=False,showImage=False):
    # Plot Indicator
    quote = os.path.splitext(os.path.basename(csvPath))[0]

    #Load Preset
    ps_description = presetJson[preset]["description"]
    ps_value = presetJson[preset]["value"]
    ps_priceMin = presetJson[preset]["priceMin"]
    ps_priceMax = presetJson[preset]["priceMax"]
    ps_sma_s = presetJson[preset]["smaS"]
    ps_sma_l = presetJson[preset]["smaL"]
    ps_breakout_high = presetJson[preset]["breakOutH"]
    ps_breakout_low = presetJson[preset]["breakOutL"]
    ps_sto_fast = presetJson[preset]["stoFast"]
    ps_sto_slow = presetJson[preset]["stoSlow"]

    # Read Data Frame
    df = pd.read_csv(csvPath)

    clh = df['Close']
    h_plt = df['High']
    l_plt = df['Low']
    clh_np = np.linspace(df['Close'][0], df['Close'][df['Day'].count() - 1], df['Day'].count())

    #analysis
    df_reverse = df.sort_index(ascending=False)
    flag = ''
    date = str(dt.date.today())
    df['TrueRange'] = df['High'] - df['Low'] #true range
    avg_true_range = round(df['TrueRange'].mean(), 2)
    df['ATR'] = avg_true_range.round(2)
    df['Value_M'] = ((df['Volume']/1000000)*df['Close']).round(2)
    day_n = 1
    week_n = 5
    month_n = 20
    change_day = df_reverse['Close'].diff(day_n).sort_index(ascending=False)
    change_week = df_reverse['Close'].diff(week_n).sort_index(ascending=False)
    change_month = df_reverse['Close'].diff(month_n).sort_index(ascending=False)
    df['Chang_D%'] = ((change_day/df['Close'][day_n])*100).round(2)
    df['Chang_W%'] = ((change_week/df['Close'][week_n])*100).round(2)
    df['Chang_M%'] = ((change_month/df['Close'][month_n])*100).round(2)

    # slow stochastic
    low_min = df_reverse['Low'].rolling(ps_sto_fast).min()
    high_max = df_reverse['High'].rolling(ps_sto_fast).max()
    k_fast = 100*(df_reverse['Close'] - low_min) / (high_max - low_min)
    k_slow = k_fast.rolling(ps_sto_slow).mean()
    d_slow = k_slow.rolling(ps_sto_slow).mean()
    df['%K'] = k_slow.sort_index(ascending=True).round(2)
    df['%D'] = d_slow.sort_index(ascending=True).round(2)

    # volume
    volume_sma_s = df_reverse['Volume'].rolling(2).mean()
    volume_break_h = df_reverse['Volume'].rolling(2).max()
    volume_sma_l = volume_sma_s.rolling(20).mean()
    df['Volume_SMA_S'] = volume_sma_s.sort_index(ascending=True)
    df['Volume_SMA_L'] = volume_sma_l.sort_index(ascending=True)
    df['Volume_Break_H'] = volume_break_h.sort_index(ascending=True)
    df['Volume_Avg'] = df_reverse['Volume'].mean()

    # break out
    breakout_h = df_reverse['High'].rolling(ps_breakout_high).max()
    breakout_l = df_reverse['Low'].rolling(ps_breakout_low).min()
    breakout_ml = df_reverse['Low'].rolling(int(round(ps_breakout_low/2))).min()
    breakout_mh = df_reverse['High'].rolling(int(round(ps_breakout_high/2))).max()
    df['BreakOut_L'] = breakout_l.sort_index(ascending=True)
    df['BreakOut_H'] = breakout_h.sort_index(ascending=True)
    df['BreakOut_M'] = (df['BreakOut_L']+df['BreakOut_H'])*0.5
    df['BreakOut_M'] = df['BreakOut_M'].round(2)
    #df['BreakOut_MH'] = (df['BreakOut_M']+df['BreakOut_H'])*0.5
    df['BreakOut_MH'] = breakout_mh.sort_index(ascending=True)
    #df['BreakOut_ML'] = (df['BreakOut_L']+df['BreakOut_M'])*0.5
    df['BreakOut_ML'] = breakout_ml.sort_index(ascending=True)

    # sma
    sma_s = df_reverse['Close'].rolling(ps_sma_s).mean()
    sma_l = df_reverse['Close'].rolling(ps_sma_l).mean()
    df['SMA_S'] = sma_s.sort_index(ascending=True).round(2)
    df['SMA_L'] = sma_l.sort_index(ascending=True).round(2)

    # gain / loss ratio
    gl_rolling = 10
    gain = (df_reverse['Close']/df_reverse['Low'].rolling(gl_rolling).min())-1
    loss = 1-(df_reverse['Close']/df_reverse['High'].rolling(gl_rolling).max())
    df['Gain'] = gain.sort_index(ascending=True).round(6)
    df['Loss'] = loss.sort_index(ascending=True).round(6)
    df['GL_Ratio'] = (gain.rolling(gl_rolling).mean()/loss.rolling(gl_rolling).mean()).round(2)
    df['GL_Ratio'] = df['GL_Ratio'].replace([np.inf, -np.inf], 0)
    df['GL_Ratio_Slow'] = df['GL_Ratio'].sort_index(ascending=False).rolling(3).mean().sort_index(ascending=True)
    df['GL_Ratio_Avg'] = df['GL_Ratio'].mean()

    # drawdown
    df['Drawdown%'] = 100 * ((df['BreakOut_H']-df['Low'])/df['BreakOut_H'])
    df['Max_Drawdown%'] =  round(df['Drawdown%'].max(),2)
    df['Avg_Drawdown%'] =  round(df['Drawdown%'].mean(),2)
    df['Min_Drawdown%'] =  round(df['Drawdown%'].min(),2)

    if saveImage or showImage:
        # Plot Figure
        pltColor = {
            'bg' : (.9, .9, .9),
            'text' : (.4, .4, .4),
            'red' : (0.8, 0.4, 0),
            'green' : (0.4, 0.8, 0),
            'blue' : (0, 0.7, 0.9),
            'yellow' : (.9, .6, 0)
        }
        fig, axes = plt.subplots(nrows=6, ncols=1, figsize=(12, 9), dpi=100,
                                 sharex=True, sharey=False,
                                gridspec_kw={'height_ratios': [1.5,.5,.5,.5,.5,.5]})
        fig.patch.set_facecolor((.9, .9, .9))
        plt.rcParams['figure.facecolor'] = (.9, .9, .9)
        fig.patch.set_alpha(1)
        fig.suptitle(quoteJson[quote]["Name"].upper() + '\n' +
                  quoteJson[quote]["Market"] + ' - ' + quoteJson[quote]["Sector"]+
                     '\n'+df['Date'][0],
                  fontsize=15, color=pltColor['text'])
        plt.subplots_adjust(left=0.01, bottom=0.05, right=0.97, top=0.90, wspace=0.20, hspace=0.00)

        #Plot Setup
        plotTrimMin = 0
        plotTrimMax = 105
        axes[0].set_facecolor(pltColor['bg'])
        axes[0].set_xlim(plotTrimMin,plotTrimMax)
        #axes[0].grid(True, 'both', 'both',color = (.87,.87,.87))
        axes[0].minorticks_on()
        axes[0].set_title('Price',color=pltColor['text'],pad=2,size=10,y=0)
        axes[0].yaxis.tick_right()
        #axes[1].grid(True, 'both', 'both', color=(.87, .87, .87))
        axes[1].minorticks_on()
        axes[1].set_facecolor(pltColor['bg'])
        axes[1].set_xlim(plotTrimMin, plotTrimMax)
        axes[1].set_ylim(0, 100)
        axes[1].set_title('Slow Stochastic',color=pltColor['text'],pad=2,size=10,y=0)
        axes[1].yaxis.tick_right()
        #axes[2].grid(True, 'both', 'both', color=(.87, .87, .87))
        axes[2].minorticks_on()
        axes[2].set_facecolor(pltColor['bg'])
        axes[2].set_xlim(plotTrimMin, plotTrimMax)
        axes[2].set_title('Volume', color=pltColor['text'],pad=2,size=10,y=0)
        axes[2].yaxis.tick_right()
        #axes[3].grid(True, 'both', 'both', color=(.87, .87, .87))
        axes[3].minorticks_on()
        axes[3].set_facecolor(pltColor['bg'])
        axes[3].set_xlim(plotTrimMin, plotTrimMax)
        axes[3].set_title('Gain/Loss Ratio', color=pltColor['text'],pad=2,size=10,y=0)
        axes[3].yaxis.tick_right()
        #axes[4].grid(True, 'both', 'both', color=(.87, .87, .87))
        axes[4].minorticks_on()
        axes[4].set_facecolor(pltColor['bg'])
        axes[4].set_xlim(plotTrimMin, plotTrimMax)
        axes[4].set_title('SMA', color=pltColor['text'],pad=2,size=10,y=0)
        axes[4].yaxis.tick_right()
        #axes[5].grid(True, 'both', 'both', color=(.87, .87, .87))
        axes[5].minorticks_on()
        axes[5].set_facecolor(pltColor['bg'])
        axes[5].set_xlim(plotTrimMin, plotTrimMax)
        axes[5].set_title('Drawdown %', color=pltColor['text'], pad=2, size=10, y=0)
        axes[5].yaxis.tick_right()

        # Line Plot
        axes[0].plot(df['Day'], df['BreakOut_H'], linewidth=.7, color=pltColor['green'], linestyle='--')
        axes[0].plot(df['Day'], df['BreakOut_L'], linewidth=.7, color=pltColor['red'], linestyle='--')
        axes[0].plot(df['Day'], df['BreakOut_M'], linewidth=.7, color=pltColor['yellow'], linestyle='--')
        axes[0].plot(df['Day'], df['BreakOut_MH'], linewidth=.7, color=pltColor['green'], linestyle='--',alpha=0.5)
        axes[0].plot(df['Day'], df['BreakOut_ML'], linewidth=.7, color=pltColor['red'], linestyle='--',alpha=0.5)

        #Test Signal
        axes[0].plot(df[df['SMA_S']>df['SMA_L']][df['%K']>df['%D']][df['GL_Ratio']>df['GL_Ratio_Slow']]['Day'],
                     df[df['SMA_S']>df['SMA_L']][df['%K']>df['%D']][df['GL_Ratio']>df['GL_Ratio_Slow']]['Low'],
                     linewidth=0, color=pltColor['green'], linestyle='-', marker='^', markersize=4)
        axes[0].plot(df[df['SMA_S'] < df['SMA_L']][df['GL_Ratio'] < df['GL_Ratio_Slow']]['Day'],
                     df[df['SMA_S'] < df['SMA_L']][df['GL_Ratio'] < df['GL_Ratio_Slow']]['High'],
                     linewidth=0, color=pltColor['red'], linestyle='-', marker='v', markersize=4)

        axes[0].plot([100, 120], [df['BreakOut_H'][0], df['BreakOut_H'][0]], linewidth=.7, color=pltColor['green'], linestyle='--',alpha = 1)
        axes[0].plot([100, 120], [df['BreakOut_L'][0], df['BreakOut_L'][0]], linewidth=.7, color=pltColor['red'], linestyle='--',alpha = 1)
        axes[0].plot([100, 120], [df['BreakOut_M'][0], df['BreakOut_M'][0]], linewidth=.7, color=pltColor['yellow'], linestyle='--',alpha = 1)

        axes[0].plot(df['Day'], clh, color=(.5,.5,.5), linewidth=1, marker='', markersize=1)
        axes[0].plot(df['Day'][0], clh[0], color=(.5,.5,.5), linewidth=1, marker='o', markersize=7)
        axes[0].plot(df['Day'], h_plt, color=(0.25, 0.25, 0.25), linewidth=.4, linestyle=':', marker='', markersize=.5)
        axes[0].plot(df['Day'], l_plt, color=(0.25, 0.25, 0.25), linewidth=.4, linestyle=':', marker='', markersize=.5)
        axes[0].plot(df['Day'], clh_np, linewidth=.5, color=(0.25, 0.25, 0.25), linestyle=':')

        axes[1].plot(df['Day'], df['%K'], linewidth=1, color=(.5, .5, .5), linestyle='-')
        axes[1].plot(df['Day'][0], df['%K'][0], color=(.5, .5, .5), linewidth=1, marker='o', markersize=7)
        axes[1].plot(df['Day'], df['%D'], linewidth=.7, color=(.5,.5,.5), linestyle=':')

        axes[1].plot([0,120], [80,80], linewidth=.7, color=pltColor['green'], linestyle='--')
        axes[1].plot([0,120], [20,20], linewidth=.7, color=pltColor['red'], linestyle='--')
        axes[1].plot([0,120], [50,50], linewidth=.7, color=(.5,.5,.5), linestyle='--')

        #axes[2].bar(df['Day'], df['Volume'], linewidth=.5, color=(.5, .5, .5), linestyle=':',alpha=0.1)
        axes[2].bar(df[df['Close'] >= df['Open']]['Day'], df[df['Close'] >= df['Open']]['Volume'], linewidth=.5,
                    color=pltColor['green'], linestyle=':', alpha=.2)
        axes[2].bar(df[df['Close'] < df['Open']]['Day'], df[df['Close'] < df['Open']]['Volume'], linewidth=.5,
                    color=pltColor['red'], linestyle=':', alpha=.2)
        #axes[2].plot(df['Day'], df['Volume_SMA_S'], linewidth=1, color=(.5, .5, .5), linestyle='-')
        #axes[2].plot(df['Day'], df['Volume_SMA_L'], linewidth=.5, color=(.5, .5, .5), linestyle='-')
        axes[2].plot(df['Day'], df['Volume_Break_H'], linewidth=1, color=(.5, .5, .5), linestyle='-')
        axes[2].plot([0, 120], [df['Volume_Avg'][0],df['Volume_Avg'][0]], linewidth=.7, color=pltColor['red'],
                     linestyle='--')
        axes[2].plot(df['Day'][0], df['Volume_Break_H'][0], color=(.5, .5, .5), linewidth=1, marker='o', markersize=7)

        axes[3].fill_between(df['Day'], df['GL_Ratio'], linewidth=1, color=(.5, .5, .5), linestyle='-',alpha=0.2)
        axes[3].plot(df['Day'], df['GL_Ratio'], linewidth=.7, color=(.5, .5, .5), linestyle='-')
        axes[3].plot(df['Day'], df['GL_Ratio_Slow'], linewidth=.7, color=(.5,.5,.5), linestyle=':')
        axes[3].plot(df['Day'][0], df['GL_Ratio'][0], color=(.5, .5, .5), linewidth=1, marker='o', markersize=7)
        axes[3].plot([0, 120], [1, 1], linewidth=.7, color=pltColor['red'],
                     linestyle='--')

        axes[4].plot(df['Day'], df['SMA_S'], linewidth=1, color=(.5, .5, .5), linestyle='-')
        axes[4].plot(df['Day'], df['SMA_L'], linewidth=.7, color=(.5,.5,.5), linestyle=':')
        axes[4].plot(df['Day'][0], df['SMA_S'][0], color=(.5, .5, .5), linewidth=1, marker='o', markersize=7)
        axes[4].plot([0, 120], [df['Close'].mean(), df['Close'].mean()], linewidth=.7, color=pltColor['red'], linestyle='--')

        axes[5].fill_between(df['Day'],  df['Drawdown%'], linewidth=1, color=(.5, .5, .5), linestyle='-', alpha=0.2)
        axes[5].plot(df['Day'],  df['Drawdown%'], linewidth=.7, color=(.5, .5, .5), linestyle='-')
        axes[5].plot(df['Day'][0], df['Drawdown%'][0], color=(.5, .5, .5), linewidth=1, marker='o', markersize=7)

        axes[5].plot([0, 120], [df['Max_Drawdown%'][0], df['Max_Drawdown%'][0]], linewidth=.7, color=pltColor['red'], linestyle='--')
        axes[5].plot([0, 120], [df['Avg_Drawdown%'][0], df['Avg_Drawdown%'][0]], linewidth=.7, color=pltColor['yellow'], linestyle='--')
        axes[5].plot([0, 120], [df['Min_Drawdown%'][0], df['Min_Drawdown%'][0]], linewidth=.7, color=pltColor['red'], linestyle='--')

        # Text Color By signal
        axes[0].text(100, min(df['Low']), quote + ' : ' + str(df['Close'][0]), size=40, ha='right', va='bottom',
            color=(.5,.5,.5),alpha = .5)

        # Text
        axes[0].text(100, min(df['Low']), 'by Burasate.U', size=12, ha='right', va='top', color=(.5,.5,.5))
        axes[0].text(100, df['BreakOut_L'][0], '  ' + str(df['BreakOut_L'][0]), size=10, ha='left', va='center',
                 color=pltColor['text'])
        axes[0].text(100, df['BreakOut_H'][0], '  ' + str(df['BreakOut_H'][0]), size=10, ha='left', va='center',
                 color=pltColor['text'])
        axes[0].text(100, df['BreakOut_M'][0], '  ' + str(df['BreakOut_M'][0]), size=10, ha='left', va='center',
                     color=pltColor['text'])
        axes[0].text(plotTrimMin+1, df['High'].max(),
                     'Preset Name: {}\n'.format(preset)+
                     'Preset Description : {}\n'.format(ps_description)+
                     'Value greater than  : {}\n'.format(ps_value)+
                     'Price : {} - {}\n'.format(ps_priceMin,ps_priceMax)+
                     'SMA : {}/{} Days\n'.format(ps_sma_s,ps_sma_l)+
                     'Breakout High : {} Days\n'.format(ps_breakout_high)+
                     'Breakout Low : {} Days\n'.format(ps_breakout_low)+
                     'STO Fast : {} Days\n'.format(ps_sto_fast)+
                     'STO Slow : {}\n'.format(ps_sto_slow)
                 , size=10, ha='left', va='top', color=((.6, .6, .6)))

        axes[1].text(100, df['%K'][0], '  ' + str(df['%K'][0].round(2)),
                     size=10, ha='left', va='center', color=pltColor['text'])

        axes[3].text(100, df['GL_Ratio'][0], '  ' + str(df['GL_Ratio'][0].round(2)),
                     size=10, ha='left', va='center', color=pltColor['text'])

        axes[5].text(plotTrimMin + 1, df['Max_Drawdown%'][0],
                     'Max Drawdown : {}%\n'.format(df['Max_Drawdown%'][0]) +
                     'Avg Drawdown : {}%\n'.format(df['Avg_Drawdown%'][0]) +
                     'Min Drawdown : {}%\n'.format(df['Min_Drawdown%'][0])
                     , size=10, ha='left', va='top', color=((.6, .6, .6)))
        axes[5].text(100, df['Drawdown%'][0], '  ' + str(df['Drawdown%'][0].round(2))+'%',
                     size=10, ha='left', va='center',color=pltColor['text'])

        # Finally
        if saveImage:
            imgName = '_'.join([preset,quote])+'.png'
            savePath = dataPath+'/analysis_img/' + imgName
            print(imgName)
            plt.savefig(savePath,facecolor=fig.get_facecolor())
        if showImage:
            plt.show()
        plt.close()
    #df.to_csv(dataPath+os.sep+'test.csv',index=False)
    return df

def getSignalAllPreset(*_):
    rec_date = dt.date.today().isoformat()
    signal_df = pd.DataFrame()
    # Clear Directory
    imgPath = dataPath + '/analysis_img/'
    oldImgFiles = os.listdir(imgPath)
    for f in oldImgFiles:
        os.remove(imgPath + f)

    for file in histFileList:
        quote = file.split('.')[0]
        #print(quote)
        for ps in presetJson:
            try:
                df = getAnalysis(histPath+os.sep+file, ps,saveImage=False,showImage=False)
                df['Preset'] = ps
                df['Quote'] = quote
                df['Rec_Date'] = rec_date

                # Condition List
                entry_condition_list = [df['SMA_S'][0] > df['SMA_L'][0],
                                        df['%K'][0] > df['%D'][0],
                                        df['GL_Ratio'][0] > df['GL_Ratio_Slow'][0]
                                        ]

                exit_condition_list = [df['SMA_S'][0] < df['SMA_L'][0],
                                       df['GL_Ratio'][0] < df['GL_Ratio_Slow'][0]
                                       ]

                # Condition Setting
                filter_condition = (
                        df['Value_M'][0] >= presetJson[ps]["value"] / 1000000 and
                        df['Close'][0] > presetJson[ps]["priceMin"] and
                        df['Close'][0] < presetJson[ps]["priceMax"] and
                        df['Close'][0] > df['Close'].mean()
                )
                entry_condition = (
                        entry_condition_list[0] and
                        entry_condition_list[1] and
                        entry_condition_list[2]
                )
                exit_condition = (
                        exit_condition_list[0] and
                        exit_condition_list[1]
                )

                # Buy Score
                df['Buy_Score'] = 0
                for con in entry_condition_list:
                    if con:
                        df['Buy_Score'] = df['Buy_Score']+1
                for con in exit_condition_list:
                    if con:
                        df['Buy_Score'] = df['Buy_Score']-1

                os.system('cls||clear')
                # Trade Entry
                if filter_condition and entry_condition:
                    print('Preset : {} | Entry : {}'.format(ps,file))
                    df['Signal'] = 'Entry'
                    signal_df = signal_df.append(df.iloc[0])
                    getAnalysis(histPath + os.sep + file, ps, saveImage=True, showImage=False)
                # Trade Exit
                elif filter_condition and exit_condition:
                    print('Preset : {} | Exit : {}'.format(ps, file))
                    df['Signal'] = 'Exit'
                    signal_df = signal_df.append(df.iloc[0])
                elif filter_condition and df['Buy_Score'][0] >= df['Buy_Score'].max()-1:
                    signal_df = signal_df.append(df.iloc[0])

            except:
                pass

    signal_df = signal_df.sort_values(['Signal','Preset','Value_M','GL_Ratio','Buy_Score'], ascending=[True,True,False,False,False])
    csvPath = dataPath + os.sep + 'signal.csv'

    # New Signal DataFrame
    new_signal_df = pd.read_csv(csvPath)
    new_signal_df = new_signal_df[new_signal_df['Rec_Date'] != rec_date]
    new_signal_df = new_signal_df.append(signal_df)
    new_signal_df.to_csv(csvPath,index=False)

    # Update G Sheet
    gsheet_df = signal_df.sort_values(['Buy_Score','Preset'],ascending=[False,True])
    gsheet_csvPath = dataPath + os.sep + 'signal_gsheet.csv'
    gsheet_df[['Rec_Date','Preset','Quote','Buy_Score']].to_csv(gsheet_csvPath,index=False)
    gSheet.updateFromCSV(gsheet_csvPath, 'SignalRecord')

def backTesting(quote,preset):
    #import csv from yahoofinance
    filePath = dataPath+'/backtesting_hist/'+quote+'.BK.csv'
    tmpFilePath = dataPath+'/backtesting_hist/'+quote+'.tmp'
    df_hist = pd.read_csv(filePath)
    df_bt = pd.DataFrame()

    for i in range(df_hist['Date'].count()):
        df_select = df_hist.iloc[i-100:i].reset_index(drop=True)
        row_count = df_select['Close'].count()
        if row_count >= 100:
            df_select['Day'] = np.linspace(1,100,100).tolist()
            df_reverse = df_select.sort_index(ascending=False).reset_index(drop=True)
            #print (df_reverse['Date'][0])

            #create tmp file
            df_reverse.to_csv(tmpFilePath,index=False)
            #print( df_reverse  )
            df = getAnalysis(tmpFilePath, preset, saveImage=False, showImage=False)
            df['Preset'] = preset
            df['Quote'] = quote

            # Duplicate From Signal
            # Condition Setting
            filter_condition = (
                    df['Value_M'][0] >= presetJson[preset]["value"] / 1000000 and
                    df['Close'][0] > presetJson[preset]["priceMin"] and
                    df['Close'][0] < presetJson[preset]["priceMax"]
            )
            entry_condition = (
                    df['SMA_S'][0] > df['SMA_L'][0] and
                    df['%K'][0] > df['%D'][0] and
                    df['GL_Ratio'][0] > df['GL_Ratio_Slow'][0] and
                    df['Close'][0] > df['Close'].mean()
            )
            exit_condition = (
                    df['SMA_S'][0] < df['SMA_L'][0] and
                    df['GL_Ratio'][0] < df['GL_Ratio_Slow'][0]
            )
            #if filter_condition and entry_condition:
            if entry_condition:
                df['Signal'] = 'Entry'
                df_bt = df_bt.append(df.iloc[0])
            elif filter_condition and exit_condition:
                df['Signal'] = 'Exit'
                df_bt = df_bt.append(df.iloc[0])
            #elif filter_condition:
            else:
                df_bt = df_bt.append(df.iloc[0])

    #Reset Index
    df_bt.reset_index(drop=True)

    #df_bt = pd.read_csv(dataPath + os.sep + 'test.csv')
    #Buy & Hold
    new_signal = []
    new_day = []
    day = 0
    buy_hold = []
    buy_hold_chg = 0
    hold = []
    hold_chg = 0
    signal = np.nan
    for i in range(df_bt['Date'].count()):
        day = day + 1
        new_day.append(day)
        if day > 1:
            hold_chg = hold_chg + (df_bt.iloc[i]['Close']-df_bt.iloc[i-1]['Close'])
            #print(df_bt.iloc[i]['Date'])
            #print(df_bt.iloc[i]['Day'])
            #print(hold_chg)
            #print(df_bt.iloc[i]['Close'])
        hold.append(hold_chg)
        if df_bt.iloc[i]['Signal'] == 'Entry':
            signal = 'Entry'
        elif df_bt.iloc[i]['Signal'] == 'Exit':
            signal = 'Exit'

        new_signal.append(signal)
        if new_signal[-1] == 'Entry':
            #buy_hold_chg = buy_hold_chg + df_bt.iloc[i]['Chang_D%']
            buy_hold_chg = buy_hold_chg + (df_bt.iloc[i]['Close']-df_bt.iloc[i-1]['Close'])
        buy_hold.append(buy_hold_chg)

    df_bt['Signal'] = new_signal
    #print(new_signal)
    #print (df_bt['Signal'].tolist())
    df_bt['Day'] = new_day
    df_bt['Stg_Hold'] = hold
    df_bt['Stg_Hold'] = (df_bt['Stg_Hold']/df_bt['Close'].tolist()[0])*100
    # df['Chang_D%'] = ((change_day / df['Close'][day_n]) * 100).round(2)
    df_bt['Stg_BuyHold'] = buy_hold
    df_bt['Stg_BuyHold'] = (df_bt['Stg_BuyHold']/df_bt['Close'].tolist()[0])*100
    df_bt['Stg_BuyHold'] = df_bt['Stg_BuyHold'].round(2)
    df_bt['Stg_Hold'] = df_bt['Stg_Hold'].round(2)

    print(df_bt['Date'].tolist()[0])
    print(df_bt['Date'].tolist()[-1])

    # Plot Figure
    pltColor = {
        'bg': (.9, .9, .9),
        'text': (.4, .4, .4),
        'red': (0.8, 0.4, 0),
        'green': (0.4, 0.8, 0),
        'blue': (0, 0.7, 0.9),
        'yellow': (1, 0.8, 0)
    }
    fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(12, 9), dpi=100,
                             sharex=True, sharey=False,
                             gridspec_kw={'height_ratios': [1,1]})
    fig.patch.set_facecolor((.9, .9, .9))
    plt.rcParams['figure.facecolor'] = (.9, .9, .9)
    fig.patch.set_alpha(1)
    fig.suptitle('{}\nPreset \"{}\" Performance'.format(quote,preset),
                 fontsize=15, color=pltColor['text'])
    plt.subplots_adjust(left=0.01, bottom=0.05, right=0.97, top=0.90, wspace=0.20, hspace=0.00)

    # Plot Setup
    axes[0].set_facecolor(pltColor['bg'])
    axes[0].grid(True, 'both', 'both', color=(.87, .87, .87))
    axes[0].minorticks_on()
    axes[0].set_title('Price', color=pltColor['text'], pad=2, size=10, y=0)
    axes[0].yaxis.tick_right()
    axes[1].set_facecolor(pltColor['bg'])
    axes[1].grid(True, 'both', 'both', color=(.87, .87, .87))
    axes[1].minorticks_on()
    axes[1].set_title('Performance %', color=pltColor['text'], pad=2, size=10, y=0)
    axes[1].yaxis.tick_right()

    axes[0].plot(df_bt['Day'], df_bt['Close'], linewidth=1, color=(.5, .5, .5), linestyle='-')

    axes[1].plot(df_bt['Day'], df_bt['Stg_Hold'], linewidth=.7, color=(.5, .5, .5), linestyle='-')
    axes[1].plot(df_bt['Day'], df_bt['Stg_BuyHold'], linewidth=1, color=pltColor['blue'], linestyle='-')
    axes[1].plot(df_bt['Day'], [0]*df_bt['Day'].count(), linewidth=.7, color=pltColor['red'], linestyle='--')

    axes[0].text(df_bt['Day'].max(), df['Close'][0], '  ' + str(df['Close'][0]), size=10, ha='left', va='center',
                 color=pltColor['text'])
    axes[1].text(df_bt['Day'].max(), df_bt['Stg_BuyHold'].tolist()[-1],
                 '  ' + str(df_bt['Stg_BuyHold'].tolist()[-1]) + ' %',
                 size=10, ha='left', va='center',color=pltColor['blue'])
    axes[1].text(df_bt['Day'].max(), df_bt['Stg_Hold'].tolist()[-1],
                 '  ' + str(df_bt['Stg_Hold'].tolist()[-1]) + ' %',
                 size=10, ha='left', va='center', color=pltColor['text'])

    imgName = '_'.join([quote,preset]) + '.png'
    savePath = dataPath + '/backtesting_hist/' + imgName
    print(imgName)
    try:
        os.remove(savePath)
    except:pass
    plt.savefig(savePath, facecolor=fig.get_facecolor())
    #plt.show()
    os.remove(tmpFilePath)
    plt.close()


if __name__ == '__main__' :
    getAnalysis(histPath + 'AH' + '.csv', 'S4',saveImage=False,showImage=True)
    #getSignalAllPreset()

    """
    import update
    update.updatePreset()
    presetPath = dataPath + '/preset.json'
    presetJson = json.load(open(presetPath))
    for f in os.listdir(dataPath + '/backtesting_hist/'):
        if f.__contains__('.BK'):
            q = f.split('.')[0]
            for ps in presetJson:
                backTesting(q,ps)
    """
    pass




