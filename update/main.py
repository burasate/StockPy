import time
print('StockPy')
time.sleep(120)

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

import lineNotify
lineNotify.signalReportToUser()