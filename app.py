from collections import defaultdict
import os
from flask import Config, Flask, flash, jsonify, redirect, render_template, request, session, url_for
from datetime import date, datetime
import pyodbc
import settings
#email
from flask_mail import Mail
from flask_cors import CORS
from flask_toastr import Toastr

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

app = Flask(__name__)
app_name = os.getenv("APP_NAME")
app.config.from_object(Config)

CORS(app)

mail = Mail(app)
toastr = Toastr(app)
app.secret_key = 'secret_key_mms'

today = date.today()
year = today.strftime("%Y")

sidebar = True

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
    logout()
    return render_template('index.html', year=year)

#Corrective
@app.route('/corrective_notification', methods=['POST', 'GET'])
def corrective_notification():
    print("oi")
    print(request)
    if request.method == 'POST':
        print("entrei")
        prod_line = request.form.get('production_line')
        var_descricao = request.form.get('var_descricao')
        equipament_var = request.form.get('equipament_var')
        var_numero_operador = request.form.get('var_numero_operador')
        paragem_producao = request.form.get('paragem_producao')
        try:
            conn = pyodbc.connect(conexao_mms)
            cursor = conn.cursor()

            storeproc_add_fiori_notification = """
                Exec dbo.add_fiori_notification 
                @descricao=?, @equipamento=?, @n_operador=?, @paragem=?, @prod_line=?, @nome_app=?
            """
            cursor.execute(
                storeproc_add_fiori_notification,
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

@app.route('/corrective_notification_capture', methods=['POST', 'GET'])
def corrective_notification_capture():
    if request.method == 'POST':
        try:
            data = request.json  
            prod_line = data.get('production_line')
            var_descricao = data.get('var_descricao')
            equipament_var = data.get('equipament_var')
            var_numero_operador = data.get('var_numero_operador')
            paragem_producao = data.get('paragem_producao')

            print("Request:", data)

            conn = pyodbc.connect(conexao_mms)
            cursor = conn.cursor()

            storeproc_add_fiori_notification = """
                Exec dbo.add_fiori_notification 
                @descricao=?, @equipamento=?, @n_operador=?, @paragem=?, @prod_line=?, @nome_app=?
            """
            cursor.execute(
                storeproc_add_fiori_notification,
                var_descricao, equipament_var, var_numero_operador, paragem_producao, prod_line, app_name
            )
            conn.commit()
            print("Notificação enviada com sucesso.")
            flash('Notificação enviada com sucesso', category='success')
            return {"message": "Notificação enviada com sucesso"}, 200
        except Exception as e:
            print(e)
            return {"error": f"Ocorreu um erro: {str(e)}"}, 400
        finally:
            cursor.close()
            conn.close()

    return {"error": "Método não permitido."}, 405

@app.route('/login_corrective', methods=['POST'])
def login_corrective():
    data = request.get_json()
    card = data.get('card')
    username = data.get('username')
    password = data.get('password')

    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        if card:
            cursor.execute("SELECT id, nome, username, n_tecnico, area FROM tecnicos WHERE card_number=?", (card,))
        elif username and password:
            cursor.execute("SELECT id, nome, username, n_tecnico, area FROM tecnicos WHERE username=? AND password=?", (username, password,))
        else:
            return jsonify({'success': False, 'error': 'Nenhum dado fornecido'}), 400

        user = cursor.fetchone()

        if user:
            session['username'] = user.username
            session['nome'] = user.nome
            session['numero_mt'] = user.n_tecnico
            session['id_mt'] = user.id
            session['area'] = user.area
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Credenciais inválidas'}), 401

    except Exception as e:
        print(e)
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/corrective', methods=['GET'])
def corrective():
    sidebar = False
    return render_template('corrective/tables.html', maintenance="Manutenção", use_corrective_layout=sidebar)

@app.route('/notifications', methods=['GET'])
def notifications():
    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        start_date = request.args.get('start_date', type=str)
        end_date = request.args.get('end_date', type=str)
        filter_prod_line = request.args.get('filter_prod_line', '', type=str)
        
        sidebar = request.args.get('sidebar', 'True').lower() == 'true'
        
        cursor.execute("""
            EXEC GetFioriNotifications 
                @PageNumber = ?, 
                @PageSize = ?,  
                @StartDate = ?, 
                @EndDate = ?, 
                @FilterProdLine = ?
            """,
            page, page_size, start_date, end_date, filter_prod_line
        )
        notifications = cursor.fetchall()
        count_query = f"""
            SELECT COUNT(*) 
            FROM [{app_name}].[dbo].[corretiva] 
            WHERE 
                (ISNULL(?, '') = '' OR [prod_line] LIKE '%' + ? + '%') AND
                (ISNULL(?, '') = '' OR [data_pedido] >= ?) AND
                (ISNULL(?, '') = '' OR [data_pedido] <= ?) and id_estado=1
        """
        cursor.execute(count_query, filter_prod_line, filter_prod_line, start_date, start_date, end_date, end_date)
        total_records = cursor.fetchone()[0]
        total_pages = (total_records + page_size - 1) // page_size
        start_page = max(1, page - 3)
        end_page = min(total_pages, page + 3)

        return render_template('corrective/notifications.html', 
                               maintenance="Manutenção", 
                               year=year, 
                               notifications=notifications, 
                               page=page, 
                               total_pages=total_pages,
                               start_page=start_page,
                               end_page=end_page,
                               use_corrective_layout=sidebar)

    except Exception as e:
        print(e)
        flash(f'Ocorreu um erro: {str(e)}', category='error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('notifications'))

@app.route('/corrective_order_by_mt', methods=['POST', 'GET'])
def corrective_order_by_mt():
    if request.method == 'POST':
        prod_line = request.form.get('production_line')
        var_descricao = request.form.get('var_descricao')
        equipament_var = request.form.get('equipament_var')
        var_numero_tecnico = request.form.get('var_numero_tecnico')
        paragem_producao = request.form.get('paragem_producao')

        try:
            conn = pyodbc.connect(conexao_mms)
            cursor = conn.cursor()

            create_order_by_mt = """
                Exec dbo.create_order_by_mt 
                @descricao=?, @equipamento=?, @paragem=?, @prod_line=?, @id_tecnico=?
            """
            cursor.execute(
                create_order_by_mt,
                var_descricao, equipament_var, paragem_producao, prod_line, var_numero_tecnico
            )
            conn.commit()

            flash('Notificação enviada com sucesso', category='success')
            return redirect(url_for('inwork'))
        except Exception as e:
          print(e)
          flash(f'Ocorreu um erro: {str(e)}', category='error')
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('inwork'))

@app.route('/reject_corrective_notification', methods=['POST'])
def reject_notification():
    notification_id = request.form.get('id')
    technician_id = request.form.get('technician_id')
    comment = request.form.get('comment')
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()
        
        update_corretiva_query = """
            UPDATE corretiva
            SET id_estado = ?, data_inicio_man = ?, data_fim_man = ?
            WHERE id = ?
        """
        cursor.execute(update_corretiva_query, (4, current_time, current_time, notification_id))

        update_tecnico_query = """
            INSERT INTO corretiva_tecnicos (id_tecnico, id_corretiva, maintenance_comment, data_fim)
            VALUES (?, ?, ?, ?)
        """
        cursor.execute(update_tecnico_query, (technician_id, notification_id, comment, current_time))

        cursor.commit()
        
        flash('A ordem de manutenção foi cancelada.', category='info')
        return jsonify(status='success')
    except Exception as e:
        print(f"Erro: {e}")
        conn.rollback()
        flash('Erro ao cancelar ordem!', category='error')
        return jsonify(status='error', message=str(e))
    finally:
        cursor.close()
        conn.close()

@app.route('/change_to_inwork', methods=['POST'])
def change_to_inwork():
    id_corretiva = request.form.get('id')
    id_tecnico = request.form.get('tecnico_id')
    
    if not id_corretiva or not id_tecnico:
        return jsonify({'error': 'Parâmetros insuficientes'}), 400

    data_atual = datetime.now()

    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE corretiva
            SET id_estado = ?, data_inicio_man = ?
            WHERE id = ?
        ''', (2, data_atual, id_corretiva))
        

        cursor.execute('''
            INSERT INTO corretiva_tecnicos (id_tecnico, id_corretiva)
            VALUES (?, ?)
        ''', (id_tecnico, id_corretiva))

        conn.commit()

        cursor.close()
        conn.close()
        
        flash('A manutenção encontra-se agora EM CURSO!', category='success')
        logout()
        return jsonify({'status': 'success', 'message': 'A manutenção encontra-se agora EM CURSO!'})

    except Exception as e:
        if 'conn' in locals():
            cursor.close()
            conn.close()
        print(e)
        flash('Erro ao iniciar manutenção!', category='error')
        return jsonify({'status': 'error', 'message': 'Erro ao iniciar manutenção!'}), 500

@app.route('/inwork', methods=['GET'])
def inwork():
    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        start_date = request.args.get('start_date', type=str)
        end_date = request.args.get('end_date', type=str)
        filter_prod_line = request.args.get('filter_prod_line', '', type=str)
        filter_number = request.args.get('filter_number', '', type=str)
        sidebar = request.args.get('sidebar', 'True').lower() == 'true'
        
        cursor.execute("""
            EXEC GetCorretivaInWorks
                @PageNumber = ?, 
                @PageSize = ?, 
                @StartDate = ?, 
                @EndDate = ?, 
                @FilterProdLine = ?,
                @FilterNumber = ?
            """,
            page, page_size, start_date, end_date, filter_prod_line, filter_number
        )
        ongoing = cursor.fetchall()
        if ongoing:
            total_records = ongoing[0].total_count
        else:
            total_records = 0
            
        total_pages = (total_records + page_size - 1) // page_size 
        start_page = max(1, page - 3)
        end_page = min(total_pages, page + 3)
        
        tecnico_id = session.get('id_mt')
        cursor.execute("""
            EXEC GetTecnicoInWorks 
                @IdTecnico = ?
        """, (tecnico_id,))

        tecnico_in_works = [item[0] for item in cursor.fetchall()]

        return render_template('corrective/inwork.html', 
                               maintenance="Manutenção", 
                               year=year, 
                               ongoing=ongoing, 
                               tecnico_in_works=tecnico_in_works,
                               page=page, 
                               total_pages=total_pages,
                               start_page=start_page,
                               end_page=end_page,
                               use_corrective_layout=sidebar)

    except Exception as e:
        print(e)
        flash(f'Ocorreu um erro: {str(e)}', category='error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('inwork'))

@app.route('/finish_maintenance', methods=['POST'])
def finish_maintenance():
    id = request.form.get('id')
    id_corretiva = request.form.get('id_corretiva')
    maintenance_comment = request.form.get('maintenance_comment')
    id_tipo_avaria = request.form.get('id_tipo_avaria')

    if not id or not maintenance_comment:
        return jsonify({'error': 'Parâmetros insuficientes'}), 400

    data_atual = datetime.now()

    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE corretiva_tecnicos
            SET maintenance_comment = ?, data_fim = ?, id_tipo_avaria = ?
            WHERE id_tecnico = ? AND id_corretiva = ? AND data_fim IS NULL
        ''', (maintenance_comment, data_atual, id_tipo_avaria, id, id_corretiva))

        cursor.execute('''
            UPDATE corretiva
            SET data_fim_man = ?, id_estado = ?
            WHERE id = ?
        ''', (data_atual, 3, id_corretiva))

        conn.commit()

        cursor.close()
        conn.close()
        
        flash('Manutenção concluída!', category='success')
        return jsonify({'status': 'success', 'message': 'Manutenção concluída!'})

    except Exception as e:
        if 'conn' in locals():
            cursor.close()
            conn.close()
        print(e)
        flash('Erro ao finalizar manutenção!', category='error')
        return jsonify({'status': 'error', 'message': 'Erro ao finalizar manutenção!'}), 500

@app.route('/finished', methods=['GET'])
def finished():
    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        filter_equipment = request.args.get('filter', '', type=str)
        start_date = request.args.get('start_date', type=str)
        end_date = request.args.get('end_date', type=str)
        filter_prod_line = request.args.get('filter_prod_line', '', type=str)
        
        cursor.execute("""
            EXEC GetCorretivaFinished
                @PageNumber = ?, 
                @PageSize = ?, 
                @FilterEquipment = ?, 
                @StartDate = ?, 
                @EndDate = ?, 
                @FilterProdLine = ?
            """,
            page, page_size, filter_equipment, start_date, end_date, filter_prod_line
        )
        finished = cursor.fetchall()
        if finished:
            total_records = finished[0].total_count
            total_pages = (total_records + page_size - 1) // page_size
        else:
            total_records = 0
            total_pages = 1
        start_page = max(1, page - 3)
        end_page = min(total_pages, page + 3)

        return render_template('corrective/finished.html', 
                               maintenance="Manutenção", 
                               year=year, 
                               finished=finished, 
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

    return redirect(url_for('finished'))

@app.route('/corrective_analytics')
def corrective_analytics():
    return render_template('corrective/analytics.html', maintenance="Manutenção")

@app.route('/corrective_comments', methods=['GET'])
def corrective_comments():
    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        start_date = request.args.get('start_date', type=str)
        end_date = request.args.get('end_date', type=str)
        filter_prod_line = request.args.get('filter_prod_line', '', type=str)
        print(f"Params: page={page}, page_size={page_size}, start_date={start_date}, end_date={end_date}, filter_prod_line={filter_prod_line}")

        cursor.execute("""
            EXEC GetCorretivaCommentsFiltered
                @PageNumber = ?, 
                @PageSize = ?, 
                @StartDate = ?, 
                @EndDate = ?, 
                @FilterProdLine = ?
            """,
            page, page_size, start_date, end_date, filter_prod_line
        )
        comments = cursor.fetchall()

        if comments:
            total_records = comments[0].total_count
            total_pages = (total_records + page_size - 1) // page_size
        else:
            total_records = 0
            total_pages = 1

        start_page = max(1, page - 3)
        end_page = min(total_pages, page + 3)
        
        print(total_records, total_pages)

        return render_template('corrective/comments.html', 
                               maintenance="Manutenção", 
                               year=year, 
                               comments=comments, 
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

    return redirect(url_for('corrective_comments'))

@app.route('/pending_comments', methods=['GET'])
def pending_comments():
    try:
        if 'id_mt' not in session:
            flash('Usuário não autenticado!', category='error')
            return redirect(url_for('login'))
        
        tecnico_id = session['id_mt']
        
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        filter_equipment = request.args.get('filter', '', type=str)
        start_date = request.args.get('start_date', type=str)
        end_date = request.args.get('end_date', type=str)
        filter_prod_line = request.args.get('filter_prod_line', '', type=str)

        cursor.execute("""
            EXEC GetPendingComments ?, ?, ?, ?, ?, ?, ?
        """, tecnico_id, filter_equipment, start_date, end_date, filter_prod_line, page, page_size)

        pending_comments = cursor.fetchall()

        cursor.nextset()
        total_count = cursor.fetchall()[0].total_count
        
        total_pages = (total_count + page_size - 1) // page_size
        start_page = max(1, page - 3)
        end_page = min(total_pages, page + 3)

        return render_template('corrective/pending_comments.html', 
                               maintenance="Manutenção",
                               pending=pending_comments, 
                               page=page, 
                               total_pages=total_pages,
                               start_page=start_page,
                               end_page=end_page,
                               total_records=total_count)

    except Exception as e:
        print(e)
        flash(f'Ocorreu um erro: {str(e)}', category='error')
        return redirect(url_for('pending_comments'))
    finally:
        cursor.close()
        conn.close()

#Autonomous
@app.route('/autonomous', methods=['GET'])
def autonomous():
    try:
        conn = pyodbc.connect(conexao_capture)
        cursor = conn.cursor()

        return render_template('autonomous/notifications.html', 
                               maintenance="Autonomous Maintenance", 
                               year=year)

    except Exception as e:
        print(e)
        flash(f'Ocorreu um erro: {str(e)}', category='error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('autonomous'))

#Preventive
@app.route('/preventive', methods=['GET'])
def preventive():
    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        filter_order = request.args.get('filter_order', '', type=str)
        filter_equipment = request.args.get('filter', '', type=str)
        filter_cost_center = request.args.get('filter_cost', '', type=str)
        start_date = request.args.get('start_date', '', type=str)
        end_date = request.args.get('end_date', '', type=str)

        preventive_page_size = request.args.get('preventive_page_size', 10, type=int)
        preventive_page = request.args.get('preventive_page', 1, type=int)

        orders_page_size = request.args.get('orders_page_size', 10, type=int)
        orders_page = request.args.get('orders_page', 1, type=int)

        filter_order = None if filter_order == "" else filter_order
        filter_equipment = None if filter_equipment == "" else filter_equipment
        filter_cost_center = None if filter_cost_center == "" else filter_cost_center
        start_date = None if start_date == "" else start_date
        end_date = None if end_date == "" else end_date

        cursor.execute("""
            EXEC GetPreventiveRecords 
                @FilterEquipment = ?, 
                @FilterOrder = ?,
                @FilterCostCenter = ?, 
                @StartDate = ?, 
                @EndDate = ?, 
                @PageSize = ?, 
                @Page = ?
        """, filter_equipment, filter_order, filter_cost_center, start_date, end_date, preventive_page_size, preventive_page)

        preventive_total = cursor.fetchone()[0]
        cursor.nextset()
        preventive_data = cursor.fetchall()

        cursor.execute("""
            EXEC GetPreventiveOrders
                @FilterEquipment = ?, 
                @FilterOrder = ?,
                @FilterCostCenter = ?, 
                @StartDate = ?, 
                @EndDate = ?, 
                @PageSize = ?, 
                @Page = ?
        """, filter_equipment, filter_order, filter_cost_center, start_date, end_date, orders_page_size, orders_page)

        orders_total = cursor.fetchone()[0]
        cursor.nextset()
        orders_data = cursor.fetchall()

        return render_template(
            'preventive/notifications.html',
            maintenance="Manutenção Preventiva",
            preventive=preventive_data,
            preventive_total=preventive_total,
            preventive_page_size=preventive_page_size,
            preventive_current_page=preventive_page,
            orders=orders_data,
            orders_total=orders_total,
            orders_page_size=orders_page_size,
            orders_current_page=orders_page
        )

    except Exception as e:
        print(e)
        flash(f'Ocorreu um erro: {str(e)}', category='error')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('preventive'))

@app.route('/start-preventive', methods=['POST'])
def start_preventive():
    try:
        data = request.get_json()
        order_number = data.get('order_number')

        if not order_number:
            return jsonify({'error': 'Número da ordem é obrigatório!'}), 400

        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("EXEC StartPreventiveOrder @OrderNumber = ?", order_number)
        conn.commit()

        return jsonify({'message': 'Preventiva iniciada com sucesso!'}), 200

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/end-preventive', methods=['POST'])
def end_preventive():
    try:
        data = request.get_json()
        id = data.get('id')

        if not id:
            return jsonify({'error': 'Número da ordem é obrigatório!'}), 400

        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("UPDATE preventive_orders SET id_estado = 3, data_fim = GETDATE() WHERE id = ?", id)
        conn.commit()

        return jsonify({'message': 'Preventiva finalizada com sucesso!'}), 200

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

#Daily
def empty_to_none(value):
    return None if value == "" else value

@app.route('/daily', methods=['GET'])
def daily():
    if 'username' not in session:
        flash('É necessário fazer login para aceder a esta página.', category='error')
        return redirect(url_for('index'))

    try:
        username = session.get('username')
        turno = session.get('turno')
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()
        area = session.get('area')
        id_tl = session.get('id_tl')

        today = datetime.today().strftime('%Y-%m-%d')
        print(today)
        cursor.execute("""
            SELECT id
            FROM daily
            WHERE id_tl = ? AND CONVERT(date, data) = ?
        """, id_tl, today)
        daily_record = cursor.fetchone()
        
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        filter_turno = empty_to_none(request.args.get('filter_turno', '', type=str))
        filter_tl = empty_to_none(request.args.get('filter_tl', '', type=str))
        start_date = empty_to_none(request.args.get('start_date', '', type=str))
        end_date = empty_to_none(request.args.get('end_date', '', type=str))        
        
        cursor.execute("""
            EXEC GetDailyRecords
                @FilterTurno = ?, 
                @FilterUsername = ?, 
                @StartDate = ?, 
                @EndDate = ?, 
                @PageSize = ?, 
                @Page = ?,
                @area = ?
            """,
            filter_turno, filter_tl, start_date, end_date, page_size, page, area
        )
        daily_data = cursor.fetchall()
        
        count_query = """
            SELECT COUNT(*) 
            FROM daily d
            LEFT JOIN teamleaders tl ON d.id_tl = tl.id
            WHERE 
                (ISNULL(?, '') = '' OR tl.turno LIKE '%' + ? + '%') AND
                (ISNULL(?, '') = '' OR tl.username LIKE '%' + ? + '%') AND
                (ISNULL(?, '') = '' OR d.data >= ?) AND
                (ISNULL(?, '') = '' OR d.data <= ?) AND
                (tl.area = ?)
                
        """
        cursor.execute(count_query, filter_turno, filter_turno, filter_tl, filter_tl, start_date, start_date, end_date, end_date, area)
        total_records = cursor.fetchone()[0]
        
        total_pages = (total_records + page_size - 1) // page_size
        start_page = max(1, page - 3)
        end_page = min(total_pages, page + 3)

        return render_template('daily/log.html', 
                               maintenance="Daily Maintenance", 
                               daily_data=daily_data,
                               username=username,
                               page=page, 
                               user_turno=turno,
                               total_pages=total_pages,
                               start_page=start_page,
                               end_page=end_page,
                               page_size=page_size,
                               filter_turno=filter_turno,
                               filter_tl=filter_tl,
                               start_date=start_date,
                               end_date=end_date,
                               daily_record=daily_record)

    except Exception as e:
        print(e)
        flash(f'Ocorreu um erro: {str(e)}', category='error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('daily'))

@app.route('/login_daily', methods=['POST'])
def login_daily():
    try:
        username = request.form.get('username')
        password = request.form.get('password')

        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("SELECT id, username, area, turno FROM teamleaders WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()

        if user:
            session['username'] = user.username
            session['id_tl'] = user.id
            session['turno'] = user.turno
            session['area'] = user.area
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Credenciais inválidas'}), 401

    except Exception as e:
        print(e)
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

#Monotoring
@app.route('/monotoring', methods=['GET'])
def monotoring():
    try:
        conn = pyodbc.connect(conexao_capture)
        cursor = conn.cursor()

        return render_template('monotoring/notifications.html', 
                               maintenance="Monotoring Maintenance", 
                               year=year)

    except Exception as e:
        print(e)
        flash(f'Ocorreu um erro: {str(e)}', category='error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('monotoring'))

#Settings
@app.route('/login_settings', methods=['POST'])
def login_settings():
    try:
        username = request.form.get('username')
        password = request.form.get('password')

        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("SELECT id, username FROM admin WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()

        if user:
            session['username'] = user.username
            session['id_admin'] = user.id
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Credenciais inválidas'}), 401

    except Exception as e:
        print(e)
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/settings', methods=['GET'])
def settings():
    if 'username' not in session:
        flash('É necessário fazer login para aceder a esta página.', category='error')
        return redirect(url_for('index'))

    try:
        username = session.get('username')
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()


        return render_template('configs/first_page.html', 
                               maintenance="Settings", 
                               username=username)

    except Exception as e:
        print(e)
        flash(f'Ocorreu um erro: {str(e)}', category='error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('daily'))

@app.route('/admin_tl', methods=['GET'])
def admin_tl():
    if 'username' not in session:
        flash('É necessário fazer login para aceder a esta página.', category='error')
        return redirect(url_for('index'))

    try:
        username = session.get('username')
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        filtro_area = request.args.get('area')
        filtro_turno = request.args.get('turno')
        filtro_num = request.args.get('num')
        page = int(request.args.get('page', 1))
        page_size = 10

        cursor.execute("""
            EXEC [dbo].[GetTeamLeaders] 
                @PageNumber = ?, 
                @PageSize = ?, 
                @FilterArea = ?, 
                @FilterTurno = ?,
                @FilterNum = ?
        """, page, page_size, filtro_area, filtro_turno, filtro_num)
        
        teamleaders = cursor.fetchall()
        if teamleaders:
            total_records = teamleaders[0].total_count
            total_pages = (total_records + page_size - 1) // page_size
        else:
            total_records = 0
            total_pages = 1

        start_page = max(1, page - 3)
        end_page = min(total_pages, page + 3)

        return render_template(
            'configs/tl.html',
            maintenance="Settings",
            username=username,
            teamleaders=teamleaders,
            page=page,
            total_pages=total_pages,
            start_page=start_page,
            end_page=end_page,
            filtro_area=filtro_area,
            filtro_turno=filtro_turno,
            filtro_num=filtro_num
        )

    except Exception as e:
        print(e)
        flash(f'Ocorreu um erro: {str(e)}', category='error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('admin_tl'))

@app.route('/admin_avarias', methods=['GET', 'POST'])
def admin_avarias():
    if 'username' not in session:
        flash('É necessário fazer login para acessar esta página.', category='error')
        return redirect(url_for('index'))

    try:
        username = session.get('username')
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("EXEC AvariasPorArea")

        tipos = cursor.fetchall()

        cursor.nextset()
        linhas = cursor.fetchall()

        areas = defaultdict(lambda: {"tipos": [], "linhas": []})
        for tipo in tipos:
            areas[tipo.area_nome]["tipos"].append({
                'id': tipo.tipo_id,
                'tipo': tipo.tipo
            })

        for linha in linhas:
            areas[linha.area_nome]["linhas"].append(linha.prod_line)

        areas = dict(sorted(areas.items(), key=lambda x: x[0]))
        
        return render_template(
            'configs/avarias.html',
            maintenance="Settings",
            username=username,
            areas=areas
        )

    except Exception as e:
        print(e)
        flash(f'Ocorreu um erro: {str(e)}', category='error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('admin_avarias'))

@app.route('/add_avaria/<area>', methods=['POST'])
def add_avaria(area):
    if 'username' not in session:
        flash('É necessário fazer login para acessar esta página.', category='error')
        return redirect(url_for('index'))

    try:
        tipo = request.form['tipo']
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("EXEC AddTipoAvaria @tipo = ?, @area = ?", tipo, area)

        conn.commit()
        flash(f'Tipo de avaria "{tipo}" adicionado com sucesso à área {area}.', category='success')
    except Exception as e:
        flash(f'Ocorreu um erro: {str(e)}', category='error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('admin_avarias'))

@app.route('/edit_avaria/<area>', methods=['POST'])
def edit_avaria(area):
    if 'username' not in session:
        flash('É necessário fazer login para acessar esta página.', category='error')
        return redirect(url_for('index'))

    try:
        id_tipo = request.form['id']
        tipo = request.form['tipo']
        
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()
        print(id_tipo, tipo, area)
        cursor.execute("EXEC AddTipoAvaria @id=?, @tipo=?, @area=?", id_tipo, tipo, area)
        conn.commit()

        flash('Tipo de avaria atualizado com sucesso!', category='success')
        return redirect(url_for('admin_avarias'))

    except Exception as e:
        flash(f'Ocorreu um erro: {str(e)}', category='error')
        return redirect(url_for('admin_avarias'))

    finally:
        cursor.close()
        conn.close()

@app.route('/update_teamleader', methods=['POST'])
def update_teamleader():
    
    if 'username' not in session:
        flash('É necessário fazer login para aceder a esta página.', category='error')
        return redirect(url_for('index'))

    try:
        id = request.form['id']
        turno = request.form['turno']
        area = request.form['area']
        
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE [dbo].[teamleaders]
            SET turno = ?, area = ?
            WHERE id = ?
        """, turno, area, id)
        
        conn.commit()
        flash('Dados atualizados com sucesso!', category='success')
        
    except Exception as e:
        print(e)
        flash(f'Ocorreu um erro: {str(e)}', category='error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('admin_tl'))

@app.route('/add_teamleader', methods=['POST'])
def add_teamleader():
    if 'username' not in session:
        flash('É necessário fazer login para aceder a esta página.', category='error')
        return redirect(url_for('index'))

    try:
        username = request.form['username']
        n_colaborador = request.form['n_colaborador']
        turno = request.form['turno']
        area = request.form['area']
        email = username + '@borgwarner.com'
        password = request.form['password']

        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO [dbo].[teamleaders] (username, password, n_colaborador, turno, area, email)
            VALUES (?, ?, ?, ?, ?, ?)
        """, username, password, n_colaborador, turno, area, email)

        conn.commit()
        flash('Team Leader adicionado com sucesso!', category='success')

    except Exception as e:
        flash(f'Ocorreu um erro: {str(e)}', category='error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('admin_tl'))

@app.route('/delete_tl/<int:id>', methods=['POST'])
def delete_tl(id):
    if 'username' not in session:
        flash('É necessário fazer login para aceder a esta página.', category='error')
        return redirect(url_for('index'))
    
    conn = pyodbc.connect(conexao_mms)
    cursor = conn.cursor()
    try:
        
        cursor.execute("""
           UPDATE [dbo].[teamleaders] SET ativo = 0 WHERE id = ?
        """, id)

        conn.commit()
        flash('Team Leader removido com sucesso!', category='info')

    except Exception as e:
        print(e)
        flash(f'Ocorreu um erro: {str(e)}', category='error')

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return redirect(url_for('admin_mt'))

@app.route('/admin_mt', methods=['GET'])
def admin_mt():
    if 'username' not in session:
        flash('É necessário fazer login para aceder a esta página.', category='error')
        return redirect(url_for('index'))

    try:
        username = session.get('username')
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        filtro_area = request.args.get('area')
        filtro_num = request.args.get('num')
        page = int(request.args.get('page', 1))
        page_size = 10

        cursor.execute("""
            EXEC [dbo].[GetTecnicos] 
                @PageNumber = ?, 
                @PageSize = ?, 
                @FilterArea = ?, 
                @FilterNtecnico = ?
        """, page, page_size, filtro_area, filtro_num)
        
        mts = cursor.fetchall()
        if mts:
            total_records = mts[0].total_count
            total_pages = (total_records + page_size - 1) // page_size
        else:
            total_records = 0
            total_pages = 1

        start_page = max(1, page - 3)
        end_page = min(total_pages, page + 3)

        return render_template(
            'configs/mt.html',
            maintenance="Settings",
            username=username,
            mts=mts,
            page=page,
            total_pages=total_pages,
            start_page=start_page,
            end_page=end_page,
            filtro_area=filtro_area,
            filtro_num=filtro_num
        )

    except Exception as e:
        print(e)
        flash(f'Ocorreu um erro: {str(e)}', category='error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('settings'))

@app.route('/update_mt', methods=['POST'])
def update_mt():
    if 'username' not in session:
        flash('É necessário fazer login para aceder a esta página.', category='error')
        return redirect(url_for('index'))

    try:
        id = request.form['id']
        area = request.form['area']
        
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE [dbo].[tecnicos]
            SET area = ?
            WHERE id = ?
        """, area, id)
        
        conn.commit()
        flash('Dados atualizados com sucesso!', category='success')
        
    except Exception as e:
        print(e)
        flash(f'Ocorreu um erro: {str(e)}', category='error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('admin_mt'))

@app.route('/add_mt', methods=['POST'])
def add_mt():
    if 'username' not in session:
        flash('É necessário fazer login para aceder a esta página.', category='error')
        return redirect(url_for('index'))

    try:
        username = request.form['username']
        n_colaborador = request.form['n_colaborador']
        area = request.form['area']
        email = username + '@borgwarner.com'
        password = request.form['password']
        nome = request.form['nome']

        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO [dbo].[tecnicos] (username, nome, password, n_tecnico, area, email)
            VALUES (?, ?, ?, ?, ?, ?)
        """, username, nome, password, n_colaborador, area, email)

        conn.commit()
        flash('Técnico adicionado com sucesso!', category='success')

    except Exception as e:
        flash(f'Ocorreu um erro: {str(e)}', category='error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('admin_mt'))

@app.route('/delete_mt/<int:id>', methods=['POST'])
def delete_mt(id):
    if 'username' not in session:
        flash('É necessário fazer login para aceder a esta página.', category='error')
        return redirect(url_for('index'))
    
    conn = pyodbc.connect(conexao_mms)
    cursor = conn.cursor()
    try:
        cursor.execute("""
           UPDATE [dbo].[tecnicos] 
           SET ativo = 0
           WHERE id = ?
        """, id)

        conn.commit()
        flash('Técnico removido com sucesso!', category='info')

    except Exception as e:
        print(e)
        flash(f'Ocorreu um erro: {str(e)}', category='error')

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return redirect(url_for('admin_mt'))

@app.route('/contacts', methods=['GET'])
def contacts():
    page = int(request.args.get('page', 1)) 
    page_size = int(request.args.get('page_size', 20))
    number_bw = request.args.get('number_bw', None) 
    turno = request.args.get('shift', None) 
    area = request.args.get('area', None)
    nome = request.args.get('nome', None)

    try:
        conn = pyodbc.connect(conexao_sms)
        cursor = conn.cursor()
        cursor.execute("EXEC GetContactsPaged @PageNumber=?,  @PageSize=?, @NumberBW=?, @Area=?, @Shift=?, @Nome=?", page, page_size, number_bw, area, turno, nome)
        rows = cursor.fetchall()
        contacts = []
        total_count = 0
        for row in rows:
            contact = {
                "Id": row.Id,
                "Name": row.Name,
                "NumberBW": row.NumberBW,
                "Email": row.Email,
                "PhoneNumber": row.PhoneNumber,
                "Area": row.Area,
                "Shift": row.Shift,
                "Role": row.Role,
            }
            contacts.append(contact)
            total_count = row.TotalCount

        total_pages = (total_count + page_size - 1) // page_size

        return render_template(
            'configs/contacts.html',
            contacts=contacts,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            number_bw=number_bw,
            area=area,
            shift=turno,
            nome=nome
        )
    except Exception as e:
        print(f"Error fetching contacts: {e}")
        return "Error loading contacts", 500

@app.route('/contacts/add', methods=['POST'])
def add_contact():
    data = request.form
    try:
        conn = pyodbc.connect(conexao_sms)

        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO [SMS].[dbo].[Contacts] (Name, NumberBW, Email, PhoneNumber, Area, Shift, Role)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, data['name'], data['numberBW'], data['email'], data['phoneNumber'], data['area'], data['shift'], data['role'])

        conn.commit()
        return redirect(url_for('contacts'))
    except Exception as e:
        print(f"Error adding contact: {e}")
        return "Error adding contact", 500

@app.route('/contacts/remove', methods=['POST'])
def remove_contact():
    data = request.get_json()
    id = data.get('id')
    try:
        conn = pyodbc.connect(conexao_sms)

        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM [SMS].[dbo].[Contacts] where id = ?
        """, id)

        conn.commit()
        flash('Contacto removido com sucesso!', category='success')
        return redirect(url_for('contacts'))
    except Exception as e:
        print(f"Error removing contact: {e}")
        return "Error removing contact", 500

@app.route('/contacts/edit/<int:id>', methods=['POST'])
def edit_contact(id):
    data = request.form
    try:
        conn = pyodbc.connect(conexao_sms)

        cursor = conn.cursor()

        cursor.execute("""
            UPDATE [SMS].[dbo].[Contacts]
            SET Name = ?, NumberBW = ?, Email = ?, PhoneNumber = ?, Area = ?, Shift = ?, Role = ?
            WHERE Id = ?
        """, data['name'], data['numberBW'], data['email'], data['phoneNumber'], data['area'], data['shift'], data['role'], id)

        conn.commit()
        return redirect(url_for('contacts'))
    except Exception as e:
        print(f"Error editing contact: {e}")
        return "Error editing contact", 500

#API
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

@app.route('/api/tecnicos', methods=['GET'])
def get_tecnicos():
    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("SELECT id, nome, n_tecnico FROM tecnicos")

        tecnicos = []
        for row in cursor.fetchall():
            tecnicos.append({
                'id': row.id,
                'nome': row.nome,
                'n_tecnico': row.n_tecnico
            })

        return jsonify(tecnicos)

    except Exception as e:
        print(e)
        return jsonify({'error': f'Ocorreu um erro: {str(e)}'}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/tipo_avarias', methods=['GET'])
def get_tipo_avarias():
    try:
        prod_line = request.args.get('prod_line')
        
        if not prod_line:
            return jsonify({'error': 'Linha de produção não registada.'}), 400
        
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("EXEC GetTipoAvariasByProdLine @prod_line = ?", (prod_line,))
        
        avarias = []
        rows = cursor.fetchall()
        
        if not rows:
            return jsonify({'error': 'Nenhum tipo de avaria encontrado para esta linha de produção.'}), 404

        for row in rows:
            avarias.append({
                'id': row.id,
                'tipo': row.tipo,
            })

        return jsonify(avarias)

    except Exception as e:
        print(e)
        return jsonify({'error': f'Ocorreu um erro: {str(e)}'}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/associate_tecnico', methods=['POST'])
def associate_tecnico():
    id_corretiva = request.form.get('id_corretiva')
    id_tecnico = request.form.get('id_tecnico')

    if not id_corretiva or not id_tecnico:
        return jsonify({'error': 'Parâmetros insuficientes'}), 400

    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO corretiva_tecnicos (id_tecnico, id_corretiva, data_inicio)
            VALUES (?, ?, ?)
        ''', (id_tecnico, id_corretiva, datetime.now()))

        conn.commit()
        flash('Técnico associado com sucesso!', category='success')
        logout()
        return jsonify({'status': 'success', 'message': 'Técnico associado com sucesso!'})
    except Exception as e:
        print(e)
        flash('Erro ao associar técnico!', category='error')
        return jsonify({'status': 'error', 'message': 'Erro ao associar o técnico!'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/check_association', methods=['GET'])
def check_association():
    id_tecnico = request.args.get('id_tecnico')

    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        query = """
        SELECT c.id, c.description, c.equipament, c.data_pedido, c.prod_line
        FROM corretiva_tecnicos ct
        JOIN corretiva c ON c.id = ct.id_corretiva
        WHERE ct.id_tecnico = ? AND ct.data_fim IS NULL
        """
        cursor.execute(query, (id_tecnico,))
        result = cursor.fetchone()

        if result:
            return jsonify({
                "associado": True,
                "manutencao": {
                    "id": result.id,
                    "prod_line": result.prod_line,
                    "description": result.description,
                    "equipament": result.equipament,
                    "data_pedido": result.data_pedido,
                }
            })
        else:
            return jsonify({"associado": False})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/get_tecnicos_associados/<int:id_corretiva>', methods=['GET'])
def get_tecnicos_associados(id_corretiva):
    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT t.id, t.nome , t.n_tecnico
            FROM corretiva_tecnicos ct
            JOIN tecnicos t ON ct.id_tecnico = t.id
            WHERE ct.id_corretiva = ? AND ct.data_fim IS NULL
        ''', (id_corretiva,))

        tecnicos = cursor.fetchall()

        data = [{'id': tecnico.id, 'nome': tecnico.nome, 'n_tecnico': tecnico.n_tecnico} for tecnico in tecnicos]

        return jsonify(data)
    except Exception as e:
        print(e)
        return jsonify({'error': 'Ocorreu um erro ao buscar os técnicos.'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/update_comment', methods=['POST'])
def update_comment():
    id_corretiva = request.form.get('id_corretiva')
    id_tecnico = request.form.get('id_tecnico')
    comment = request.form.get('comment')
    id_tipo_avaria = request.form.get('id_tipo_avaria')
    parou = request.form.get('stopped_prod')

    if not id_corretiva or not id_tecnico or not comment:
        return jsonify({'error': 'Parâmetros insuficientes'}), 400

    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE corretiva_tecnicos
            SET maintenance_comment = ?, id_tipo_avaria = ?, data_fim = GETDATE()
            WHERE id_corretiva = ? AND id_tecnico = ?
        ''', (comment, id_tipo_avaria, id_corretiva, id_tecnico))

        cursor.execute('''
            UPDATE corretiva
            SET stopped_production = ?
            WHERE id = ?
        ''', (parou, id_corretiva))
        
        if cursor.rowcount == 0:
            flash('Registo não encontrado para atualização', category='error')
            return jsonify({'status': 'error', 'message': 'Registo não encontrado para atualização!'}), 404

        conn.commit()
        flash('Comentário feito com sucesso!', category='success')
        return jsonify({'status': 'success', 'message': 'Comentário feito com sucesso!'})
    except Exception as e:
        print(e)
        flash('Erro ao fazer o comentário!', category='error')
        return jsonify({'status': 'error', 'message': 'Erro ao fazer o comentário!'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/get_corrective_stats')
def get_corrective_stats():
    try:
        filter_prod_line = request.args.get('filter_prod_line', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')

        if start_date:
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        else:
            start_date = None
        if end_date:
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        else:
            end_date = None
            
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("EXEC GetCorrectiveStats @filter_prod_line=?, @start_date=?, @end_date=?", filter_prod_line if filter_prod_line else None    , start_date, end_date)
        
        data = []
        for row in cursor.fetchall():
            data.append({
                'estado': row.estado,
                'count': row.count
            })

        return jsonify(data)
        
    except Exception as e:
        print(e)
        return jsonify({'error': f'Ocorreu um erro: {str(e)}'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/get-corretiva-comments')
def get_corretiva_comments():
    id_corretiva = request.args.get('idCorretiva', type=int)

    conn = pyodbc.connect(conexao_mms)
    cursor = conn.cursor()
    cursor.execute(
        "EXEC GetCorretivaComments @IdCorretiva=?", 
        id_corretiva
    )

    comments = [{
        'tecnico_nome': row.tecnico_nome,
        'n_tecnico': row.n_tecnico,
        'maintenance_comment': row.maintenance_comment,
        'duracao_intervencao': row.duracao_intervencao,
        'tipo_avaria': row.tipo_avaria,
        'data_inicio': row.ini,
        'data_fim': row.fim
    } for row in cursor.fetchall()]
    
    return jsonify(comments)

@app.route('/api/check_comments', methods=['POST'])
def check_comments():
    if 'id_mt' not in session:
        return jsonify({'status': 'error', 'message': 'Usuário não autenticado!'}), 403

    id_tecnico = request.json.get('id_tecnico')
    
    if not id_tecnico:
        return jsonify({'status': 'error', 'message': 'ID do técnico não fornecido!'}), 400

    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()
        
        query = """
            SELECT COUNT(*) 
            FROM corretiva_tecnicos
            WHERE id_tecnico = ? 
              AND (maintenance_comment IS NULL OR id_tipo_avaria IS NULL)
              AND data_fim IS NOT NULL
        """
        
        cursor.execute(query, (id_tecnico,))
        result = cursor.fetchone()

        if result and result[0] > 0:
            return jsonify({'status': 'success', 'has_pending_comments': 'SIM'}), 200
        else:
            return jsonify({'status': 'success', 'has_pending_comments': 'NAO'}), 200
        
    except Exception as e:
        print(f"Erro ao verificar comentários: {e}")
        return jsonify({'status': 'error', 'message': 'Erro ao verificar comentários'}), 500
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/save_comment', methods=['POST'])
def save_comment():
    try:
        data = request.get_json()
        comment_id = data['id']
        comment_text = data['comment']
        tipo_avaria_id = data['tipo_avaria']

        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE corretiva_tecnicos
            SET maintenance_comment = ?, id_tipo_avaria = ?
            WHERE id = ?
        """, comment_text, tipo_avaria_id, comment_id)

        conn.commit()

        return jsonify({"status": "success"})
    
    except Exception as e:
        print(f"Erro ao salvar comentário: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/check_all_interventions_completed', methods=['GET'])
def check_all_interventions_completed():
    if 'id_mt' not in session:
        return jsonify({'status': 'error', 'message': 'Usuário não autenticado!'}), 403

    try:
        id_corretiva = request.args.get('id_corretiva')
        id_tecnico = request.args.get('id_tecnico')

        if not id_corretiva or not id_tecnico:
            return jsonify({'status': 'error', 'message': 'ID da correção e ID do técnico são obrigatórios!'}), 400

        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) AS pending_interventions
            FROM corretiva_tecnicos
            WHERE id_corretiva = ? 
              AND data_fim IS NULL
              AND id_tecnico != ?;
        """, id_corretiva, id_tecnico)

        result = cursor.fetchone()
        pending_interventions = result.pending_interventions if result else 0

        if pending_interventions > 0:
            return jsonify({'status': 'warning', 'message': 'Não é possível finalizar. Existem intervenções não finalizadas de outros técnicos.'}), 200
        
        return jsonify({'status': 'success', 'message': 'Apenas a sua intervenção está pendente, pode finalizar.'})

    except Exception as e:
        print(e)
        return jsonify({'status': 'error', 'message': 'Erro ao verificar o status das intervenções!'}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/add_daily_record', methods=['POST'])
def add_daily_record():
    if 'id_tl' not in session:
        return jsonify({'status': 'error', 'message': 'Usuário não autenticado!'}), 403

    try:
        safety_comment = request.form.get('safety_comment')
        quality_comment = request.form.get('quality_comment')
        volume_comment = request.form.get('volume_comment')
        people_comment = request.form.get('people_comment')

        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO daily (id_tl, data, safety_comment, quality_comment, volume_comment, people_comment)
            VALUES (?, GETDATE(), ?, ?, ?, ?)
        """, session['id_tl'], safety_comment, quality_comment, volume_comment, people_comment)

        conn.commit()
        flash('Comentários adicionados!', category='success')
        return jsonify({'status': 'success', 'message': 'Comentários adicionados!'})

    except Exception as e:
        print(e)
        flash('Erro ao adicionar os comentários.', category='error')
        return jsonify({'status': 'error', 'message': 'Erro ao adicionar comentários!'}), 500
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/edit_daily_record', methods=['POST'])
def edit_daily_record():
    if 'username' not in session:
        return jsonify({'status': 'error', 'message': 'Usuário não autenticado.'}), 403
    
    try:
        record_id = request.form.get('id')
        safety_comment = request.form.get('safety_comment')
        quality_comment = request.form.get('quality_comment')
        volume_comment = request.form.get('volume_comment')
        people_comment = request.form.get('people_comment')

        if not record_id or not safety_comment or not quality_comment or not volume_comment or not people_comment:
            return jsonify({'status': 'error', 'message': 'Todos os campos são obrigatórios.'}), 400

        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        today = datetime.today().strftime('%Y-%m-%d')
        cursor.execute("""
            UPDATE daily
            SET safety_comment = ?, quality_comment = ?, volume_comment = ?, people_comment = ?
            WHERE id = ? AND CONVERT(date, data) = ?
        """, (safety_comment, quality_comment, volume_comment, people_comment, record_id, today))

        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({'status': 'error', 'message': 'Comentário não encontrado ou já editado.'}), 404

        return jsonify({'status': 'success', 'message': 'Comentário atualizado com sucesso.'}), 200

    except Exception as e:
        print(f"Erro ao atualizar comentário: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Ocorreu um erro ao atualizar o comentário.'}), 500

    finally:
        cursor.close()
        conn.close()

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

@app.route('/api/get_areas', methods=['GET'])
def areas():
  try:
    conn = pyodbc.connect(conexao_capture)
    cursor = conn.cursor()
    
    query = "Select DISTINCT area from [dbo].[ProdLineAreaPL] order by area ASC"
    cursor.execute(query)

    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            "area": row[0]
        })

    cursor.close()
    conn.close()

    return jsonify(result)

  except Exception as e:
    print(e)
    return jsonify({'error'}), 500


if __name__ == "__main__":
    app.run(debug=True)