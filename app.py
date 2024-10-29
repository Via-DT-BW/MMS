from flask import Config, Flask, flash, jsonify, redirect, render_template, request, session, url_for
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
app_name = "MMS"
app.config.from_object(Config)

mail = Mail(app)
toastr = Toastr(app)
app.secret_key = 'secret_key_mms'

today = date.today()
year = today.strftime("%Y")

@app.route('/logout')
def logout():

   session.pop('username', None)
   session.pop('password', None)
   session.pop('email', None)
   session.pop('workernumber', None)
   session.pop('accesslevel', None)
   session.clear()
   return redirect(url_for('index'))

@app.route('/')
def index():
  conn=pyodbc.connect(conexao_capture)
  cursor = conn.cursor()

  return render_template('index.html', year=year)

@app.route('/corrective', methods=['GET'])
def corrective():
    try:
        conn = pyodbc.connect(conexao_capture)
        cursor = conn.cursor()

        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        filter_description = request.args.get('filter', '', type=str)

        cursor.execute("EXEC GetFioriNotifications @PageNumber = ?, @PageSize = ?, @FilterDescription = ?", 
                       page, page_size, filter_description)
        notifications = cursor.fetchall()

        cursor.execute("""
            SELECT COUNT(*) 
            FROM [Capture].[dbo].[FioriNotification] 
            WHERE [description] LIKE '%' + ? + '%'
        """, (filter_description,))
        
        total_records = cursor.fetchone()[0]

        total_pages = (total_records + page_size - 1) // page_size
        
        start_page = max(1, page - 3)
        end_page = min(total_pages, page + 3)

        return render_template('corrective/notifications.html', 
                               maintenance="Corrective Maintenance", 
                               year=year, 
                               notifications=notifications, 
                               page=page, 
                               total_pages=total_pages,
                               start_page=start_page,
                               end_page=end_page)

    except Exception as e:
        print(e)
        flash(f'Ocorreu um erro: {str(e)}', category='error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('corrective'))

@app.route('/corrective_notification', methods=['POST', 'GET'])
def corrective_notification():
    if request.method == 'POST':
        prod_line = request.form.get('production_line')
        var_descricao = request.form.get('var_descricao')
        equipament_var = request.form.get('equipament_var')
        var_numero_operador = request.form.get('var_numero_operador')
        paragem_producao = request.form.get('paragem_producao')
        print("linha:",prod_line)
        print("desc:",var_descricao)
        print("equip:",equipament_var)
        print("num_operator:",var_numero_operador)
        print("parou?",paragem_producao)
        try:
            conn = pyodbc.connect(conexao_capture)
            cursor = conn.cursor()

            storeproc_station_control_add_fiori_notification = """
                Exec dbo.station_control_add_fiori_notification 
                @descricao=?, @equipamento=?, @n_operador=?, @paragem=?, @prod_line=?, @nome_app=?
            """
            cursor.execute(
                storeproc_station_control_add_fiori_notification,
                var_descricao, equipament_var, var_numero_operador, paragem_producao, prod_line, app_name
            )
            conn.commit()

            flash('Notificação enviada com sucesso', category='success')
            return redirect(url_for('corrective'))
        except Exception as e:
          print(e)
          flash(f'Ocorreu um erro: {str(e)}', category='error')
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('corrective'))

@app.route('/api/corrective', methods=['GET'])
def corrective_maintenance():
  try: 
    machine = request.args.get('machine')

    conn = pyodbc.connect(conexao_capture)
    cursor = conn.cursor()
    
    cursor.execute("Exec dbo.select_distinct_sap_machine_with_prod_line @machine = ?", machine)
    maquinas_sap = [{'id': row[0], 'description': row[1]} for row in cursor.fetchall()]
    
    cursor.execute("Exec dbo.select_description_fiori_by_line @machine = ?", machine)
    select_description_fiori = [{'descricao': row[0]} for row in cursor.fetchall()]
    
    cursor.execute("Exec dbo.presence_ongoing_operators @machine = ?", machine)
    ongoing_operators = [{'id': row[0], 'nome': row[1], 'usernumber': row[2], 'machine': row[3]} for row in cursor.fetchall()]
    
    return jsonify({
        'maquinas_sap': maquinas_sap,
        'select_description_fiori': select_description_fiori,
        'ongoing_operators': ongoing_operators
    })

  except Exception as e:
    print(e)
    return redirect(url_for('index'))

@app.route('/api/prod_lines', methods=['GET'])
def lines():
  try:
    conn = pyodbc.connect(conexao_capture)
    cursor = conn.cursor()
    
    proc= "EXEC GetLines"
    cursor.execute(proc)

    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            "id": row[0],   
            "line": row[1],
            "tabela?": row[2],
        })

    cursor.close()
    conn.close()

    return jsonify(result)

  except Exception as e:
    print(e)
    return jsonify({'error'}), 500

if __name__ == "__main__":
    app.run(debug=True)