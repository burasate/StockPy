import time
time.sleep(120)

import update
try:
    update.updateConfig()
    update.updatePreset()
    update.updateAllFile()
except:
    pass

import stockHistorical
stockHistorical.LoadSetHist()
stockHistorical.LoadAllHist()

import stockAnalysis
stockAnalysis.getImageBuySignalAll()

import lineNotify
lineNotify.signalReportToUser()