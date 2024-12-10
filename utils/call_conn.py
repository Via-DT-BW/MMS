import settings
import pyodbc

try:
    conexao_capture=settings.conexao_capture()
    conn=pyodbc.connect(conexao_capture)
except Exception as e:
    print(e)
    print("Falha de ligacao à BD do Capture")
  
try:
    conexao_mms=settings.conexao_mms()
    conn_mms=pyodbc.connect(conexao_mms)
except Exception as e:
    print(e)
    print("Falha de ligacao à BD do MMS")
    
try:
    conexao_sms=settings.conexao_sms()
    conn_sms=pyodbc.connect(conexao_sms)
except Exception as e:
    print(e)
    print("Falha de ligacao à BD dos SMS")