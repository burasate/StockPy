import gspread,csv,os
from oauth2client.service_account import ServiceAccountCredentials

rootPath = os.path.dirname(os.path.abspath(__file__))
dataPath = rootPath+'/data'
jsonKeyPath = dataPath + '/stockPyGSheet.json'
sheetName = 'StockPy'

def connect(*_):
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    credential = ServiceAccountCredentials.from_json_keyfile_name(jsonKeyPath, scope)
    gc = gspread.authorize(credential)
    return gc

def updateFromCSV(csvPath, workSheet, clearAll = True):
    sheet = connect().open(sheetName).worksheet(workSheet)
    #load csv
    tableList = []
    index = 0
    with open(csvPath, 'r', newline='') as readfile:
        for row in csv.reader(readfile):
            tableList.append(row)
        readfile.close()
    if clearAll:
    	sheet.clear()
    sheet.update(tableList,value_input_option='USER_ENTERED')

def loadConfigData(idName):
    print('Loading config data from database....')
    sheet = connect().open(sheetName).worksheet('Config')
    configS = sheet.get_all_records()
    for r in configS :
        if r['idName'] == idName:
            print('config is loaded')
            return r
    print ('Can not found ID Name')
    return None

def getWorksheetColumnName(workSheet):
    sheet = connect().open(sheetName).worksheet(workSheet)
    header = sheet.row_values(1)
    return header

def addRow(workSheet,column):
    sheet = connect().open(sheetName).worksheet(workSheet)
    sheet.append_row(column,value_input_option='USER_ENTERED')

def deleteRow(workSheet,colName,value):
    sheet = connect().open(sheetName).worksheet(workSheet)
    dataS = sheet.get_all_records()
    rowIndex = 1
    for data in dataS:
        rowIndex += 1
        if data[colName] == value:
            sheet.delete_rows(rowIndex,rowIndex)
            print('Sheet "{}" Deleted Row {} {}'.format(workSheet,rowIndex,data))

def getAllDataS(workSheet):
    sheet = connect().open(sheetName).worksheet(workSheet)
    dataS = sheet.get_all_records()
    return dataS

def setValue(workSheet,findKey=None,findValue=None,key=None,value=None):
    dataS = getAllDataS(workSheet)
    rowIndex = 1
    for data in dataS:
        rowIndex += 1
        if not key in data:
            return None
        if data[findKey] == findValue and key in data:
            colIndex = 0
            for col in getWorksheetColumnName(workSheet):
                colIndex += 1
                if col == key:
                    sheet = connect().open(sheetName).worksheet(workSheet)
                    sheet.update_cell(row=rowIndex,col=colIndex,value=value)
                    print('update row : {}  column : \'{}\'  value : {}'.format(rowIndex,key,value))
                    break
            break

if __name__ == '__main__':
    import pprint
    pprint.pprint(getAllDataS('Config'))
    pass
