import json,time,csv,requests,os,ast,pprint,datetime
from datetime import datetime as dt
import realtime
print('SET Real-Time Recorder')
if not os.name == 'nt': #Raspi
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
        minute = int(dt.now().minute)
        morning = isNowInTimePeriod(datetime.time(9, 55), datetime.time(12, 30), datetime.time(hour, minute))
        afternoon = isNowInTimePeriod(datetime.time(14, 30), datetime.time(16, 45), datetime.time(hour, minute))
        weekDay = int(dt.now().weekday())
        if (morning or afternoon) and weekDay < 5:
            try:
                GetAllRealtime(recordData=True,cleanupData=False)
                #time.sleep(60*1)
            except: pass
        else:
            os.system('cls||clear')
            print('SET Market is Close')
            time.sleep(60*10)