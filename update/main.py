import time,os
print('StockPy')

if not os.name == 'nt':
    time.sleep(30)
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
stockAnalysis.getSignalAllPreset()
stockAnalysis.uploadSignalData()

import lineNotify
#lineNotify.signalReportToUser()