import json

def conexao_capture():
    fileObject = open("connections/settings.json", "r")
    jsonContent = fileObject.read()
    aList = json.loads(jsonContent)

    connection_string=aList[0]['connection_string_capture']
    return connection_string

def conexao_mms():
    fileObject = open("connections/settings.json", "r")
    jsonContent = fileObject.read()
    aList = json.loads(jsonContent)
    connection_string=aList[1]['connection_string_mms']
    return connection_string
