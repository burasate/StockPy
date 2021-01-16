import time
time.sleep(120)

import update
while True:
    try:
        update.updateConfig()
        update.updatePreset()
        update.updateAllFile()
        break
    except:
        pass


import stockHistorical
stockHistorical.LoadSetHist()
stockHistorical.LoadAllHist()


import stockAnalysis
#stockAnalysis.getImageBuySignalAll()
stockAnalysis.getSignalAllPreset()


import lineNotify
lineNotify.signalReportToUser()