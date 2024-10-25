from flask import Config, Flask, render_template
from datetime import date
import pyodbc
import settings
#email
from flask_mail import Mail

from flask_toastr import Toastr
from fpdf import FPDF

try:
    conexao_capture=settings.conexao_capture()
    conn=pyodbc.connect(conexao_capture)
except Exception as e:
  print("Falha de ligacao à BD do Capture")

app = Flask(__name__)

app.config.from_object(Config)

mail = Mail(app)
toastr = Toastr(app)
app.secret_key = 'secret_key_mms'


@app.route('/')
def index():
  conn=pyodbc.connect(conexao_capture)
  cursor = conn.cursor()

  today = date.today()
  year = today.strftime("%Y")

  return render_template('index.html', year=year)

if __name__ == "__main__":
    app.run(debug=False)