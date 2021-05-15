import os
import realtime
marketHour = [9,10,11,12,14,15,16,17]
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
        weekDay = int(dt.now().weekday())
        if hour in marketHour and weekDay < 5:
            try:
                GetAllRealtime(recordData=True,cleanupData=False)
                #time.sleep(60*1)
            except: pass
        else:
            os.system('cls||clear')
            print('SET Market is Close')
            time.sleep(60*30)