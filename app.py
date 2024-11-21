import os
from flask import Config, Flask, flash, jsonify, redirect, render_template, request, session, url_for
from datetime import date, datetime
import pyodbc
import settings
#email
from flask_mail import Mail

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

app = Flask(__name__)
app_name = os.getenv("APP_NAME")
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
    logout()
    return render_template('index.html', year=year)

#Corrective
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
            EXEC GetFioriNotifications 
                @PageNumber = ?, 
                @PageSize = ?, 
                @FilterEquipment = ?, 
                @StartDate = ?, 
                @EndDate = ?, 
                @FilterProdLine = ?
            """,
            page, page_size, filter_equipment, start_date, end_date, filter_prod_line
        )
        notifications = cursor.fetchall()
        count_query = f"""
            SELECT COUNT(*) 
            FROM [{app_name}].[dbo].[corretiva] 
            WHERE 
                (ISNULL(?, '') = '' OR [equipament] LIKE '%' + ? + '%') AND
                (ISNULL(?, '') = '' OR [prod_line] LIKE '%' + ? + '%') AND
                (ISNULL(?, '') = '' OR [data_pedido] >= ?) AND
                (ISNULL(?, '') = '' OR [data_pedido] <= ?) and id_estado=1
        """
        cursor.execute(count_query, filter_equipment, filter_equipment, filter_prod_line, filter_prod_line, start_date, start_date, end_date, end_date)
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
            return redirect(url_for('corrective'))
        except Exception as e:
          print(e)
          flash(f'Ocorreu um erro: {str(e)}', category='error')
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('corrective'))

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
            SET id_estado = ?, data_fim_man = ?, data_fim_man = ?
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
        filter_equipment = request.args.get('filter', '', type=str)
        start_date = request.args.get('start_date', type=str)
        end_date = request.args.get('end_date', type=str)
        filter_prod_line = request.args.get('filter_prod_line', '', type=str)
        
        cursor.execute("""
            EXEC GetCorretivaInWorks
                @PageNumber = ?, 
                @PageSize = ?, 
                @FilterEquipment = ?, 
                @StartDate = ?, 
                @EndDate = ?, 
                @FilterProdLine = ?
            """,
            page, page_size, filter_equipment, start_date, end_date, filter_prod_line
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
                               end_page=end_page)

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

        filter_equipment = request.args.get('filter', '', type=str)
        filter_cost_center = request.args.get('filter_cost', '', type=str)
        start_date = request.args.get('start_date', '', type=str)
        end_date = request.args.get('end_date', '', type=str)
        page_size = request.args.get('page_size', 10, type=int)
        page = request.args.get('page', 1, type=int)

        filter_equipment = None if filter_equipment == "" else filter_equipment
        filter_cost_center = None if filter_cost_center == "" else filter_cost_center
        start_date = None if start_date == "" else start_date
        end_date = None if end_date == "" else end_date

        cursor.execute("""
            EXEC GetPreventiveRecords 
                @FilterEquipment = ?, 
                @FilterCostCenter = ?, 
                @StartDate = ?, 
                @EndDate = ?, 
                @PageSize = ?, 
                @Page = ?
        """, filter_equipment, filter_cost_center, start_date, end_date, page_size, page)
        
        preventive_data = cursor.fetchall()

        count_query = """
            SELECT COUNT(*) 
            FROM preventive 
            WHERE 
                (ISNULL(?, '') = '' OR equipament LIKE '%' + ? + '%') AND
                (ISNULL(?, '') = '' OR cost_center LIKE '%' + ? + '%') AND
                (ISNULL(?, '') = '' OR start_date >= ?) AND
                (ISNULL(?, '') = '' OR end_date <= ?)
        """
        cursor.execute(count_query, filter_equipment, filter_equipment, 
                       filter_cost_center, filter_cost_center, 
                       start_date, start_date, 
                       end_date, end_date)
        total_records = cursor.fetchone()[0]

        return render_template('preventive/notifications.html', 
                               maintenance="Preventive Maintenance", 
                               preventive=preventive_data, 
                               total_records=total_records, 
                               page_size=page_size,
                               current_page=page)

    except Exception as e:
        print(e)
        flash(f'Ocorreu um erro: {str(e)}', category='error')
    finally:
        cursor.close()
        conn.close
    return redirect(url_for('preventive'))

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
                @Page = ?
            """,
            filter_turno, filter_tl, start_date, end_date, page_size, page
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
                (ISNULL(?, '') = '' OR d.data <= ?)
        """
        cursor.execute(count_query, filter_turno, filter_turno, filter_tl, filter_tl, start_date, start_date, end_date, end_date)
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
                               end_date=end_date)

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

        cursor.execute("SELECT id, username, turno FROM teamleaders WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()

        if user:
            session['username'] = user.username
            session['id_tl'] = user.id
            session['turno'] = user.turno
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


        return render_template('configs/settings.html', 
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

    return redirect(url_for('settings'))

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
           DELETE FROM [dbo].[teamleaders] WHERE id = ?
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
           DELETE FROM [dbo].[tecnicos] WHERE id = ?
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
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("SELECT id, tipo FROM tipo_avaria")

        avarias = []
        for row in cursor.fetchall():
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