import time,os
print('StockPy')
time.sleep(30)

if not os.name == 'nt':
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
lineNotify.signalReportToUser()