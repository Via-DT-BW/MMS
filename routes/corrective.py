import os
import random
from flask import Blueprint, jsonify, request, session, redirect, url_for, flash, render_template
import pyodbc
from datetime import date, datetime
import time
import pyodbc
from utils.call_conn import conexao_mms


today = date.today()
year = today.strftime("%Y")
sidebar = True
app_name = os.getenv("APP_NAME")
#app_name = "MMS"

corrective = Blueprint("corrective", __name__, static_folder="static", static_url_path='/Main/static', template_folder="templates")

@corrective.route('/corrective_notification', methods=['POST', 'GET'])
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
            return redirect(url_for('corrective.corrective_main'))
        except Exception as e:
          print(e)
          flash(f'Ocorreu um erro: {str(e)}', category='error')
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('corrective.corrective_main'))

@corrective.route('/corrective_notification_capture', methods=['POST', 'GET'])
def corrective_notification_capture():
    if request.method == 'POST':
        try:
            data = request.json  
            prod_line = data.get('production_line')
            var_descricao = data.get('var_descricao')
            equipament_var = data.get('equipament_var')
            var_numero_operador = data.get('var_numero_operador')
            paragem_producao = data.get('paragem_producao')

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

@corrective.route('/login_corrective', methods=['POST'])
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

@corrective.route('/corrective', methods=['GET'])
def corrective_main():
    sidebar = False
    return render_template('corrective/tables.html', maintenance="Manutenção", use_corrective_layout=sidebar)

@corrective.route('/notifications', methods=['GET'])
def notifications():
    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        mt_id = session.get('id_mt')
        
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        start_date = request.args.get('start_date', type=str)
        end_date = request.args.get('end_date', type=str)
        filter_prod_line = request.args.get('filter_prod_line', '', type=str)
        
        sidebar = request.args.get('sidebar', 'True').lower() == 'true'
        
        total_records = 0

        cursor.execute("""
            DECLARE @TotalRecords INT;
            EXEC GetFioriNotifications 
                @PageNumber = ?, 
                @PageSize = ?,  
                @StartDate = ?, 
                @EndDate = ?, 
                @FilterProdLine = ?, 
                @TecnicoId = ?, 
                @TotalRecords = @TotalRecords OUTPUT;
            SELECT @TotalRecords;
            """,
            page, page_size, start_date, end_date, filter_prod_line, mt_id
        )
        notifications = cursor.fetchall()

        total_records = cursor.nextset() and cursor.fetchone()[0]

        total_pages = max(1, (total_records + page_size - 1) // page_size)
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

    return redirect(url_for('corrective.notifications'))

@corrective.route('/corrective_order_by_mt', methods=['POST', 'GET'])
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

@corrective.route('/reject_corrective_notification', methods=['POST'])
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

@corrective.route('/change_to_inwork', methods=['POST'])
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
        return jsonify({'status': 'success', 'message': 'A manutenção encontra-se agora EM CURSO!'})

    except Exception as e:
        if 'conn' in locals():
            cursor.close()
            conn.close()
        print(e)
        flash('Erro ao iniciar manutenção!', category='error')
        return jsonify({'status': 'error', 'message': 'Erro ao iniciar manutenção!'}), 500

@corrective.route('/inwork', methods=['GET'])
def inwork():
    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        mt_id = session.get('id_mt')
        
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
                @FilterNumber = ?,
                @TecnicoId = ?
            """,
            page, page_size, start_date, end_date, filter_prod_line, filter_number, mt_id
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

@corrective.route('/finish_maintenance', methods=['POST'])
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

        cursor.execute('''
            SELECT sap_order_number FROM [dbo].[corretiva]
            WHERE id = ?
        ''', (id_corretiva,))
        sap_order_number = cursor.fetchone()
        
        if sap_order_number and sap_order_number[0] is not None:
            cursor.execute('''
                UPDATE [dbo].[rpa_corretiva]
                SET done = 0, in_queue = 0
                WHERE id_corretiva = ?
            ''', (id_corretiva,))
            print("Corretiva pronta para ser finalizada em SAP.")
        else:
            print(f"Não existe sap_order_number para a corretiva {id_corretiva}.")
        
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

@corrective.route('/finished', methods=['GET'])
def finished():
    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()
        
        mt_id = session.get('id_mt')

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

@corrective.route('/corrective_analytics')
def corrective_analytics():
    return render_template('corrective/analytics.html', maintenance="Manutenção")

@corrective.route('/pending_comments', methods=['GET'])
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

@corrective.route('/pedido_spares/<int:id>', methods=['POST'])
def pedido_spares(id):
    time.sleep(10)
        
    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()
        
        query = "INSERT INTO rpa_corretiva (id_tecnico, id_corretiva) values (?, ?)"
        cursor.execute(query, (session['id_mt'], id))
        cursor.commit()
        
        sap_order_number = aguardar_sap_order(cursor, id)

        if sap_order_number:
            return jsonify({"message": f"Ordem {sap_order_number} criada com sucesso!"}), 200
        else:
            return jsonify({"error": "Tempo limite atingido, por favor verifique o número da ordem mais tarde."}), 408

    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

@corrective.route('/mt_profile', methods=['GET'])
def mt_profile_page():
    try:
        mt_id = session.get('id_mt')
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        query = "SELECT * FROM tecnicos WHERE id = ? and ativo = 1"
        cursor.execute(query, (mt_id,))
        row = cursor.fetchone()

        if row:
            tecnico = {
                "id": row.id,
                "nome": row.nome,
                "n_tecnico": row.n_tecnico,
                "card_number": row.card_number,
                "username": row.username,
                "password": row.password,
                "area": row.area,
                "email": row.email,
                "sap_user": row.sap_user,
                "sap_pass": row.sap_pass,
            }
            
            return render_template('corrective/mt_profile.html',maintenance="Perfil", tecnico=tecnico)
        else:
            return render_template('corrective/mt_profile.html',maintenance="Perfil", error="Técnico não encontrado")
    except Exception as e:
        print(e)
        return render_template('corrective/mt_profile.html',maintenance="Perfil", error="Erro ao carregar o perfil")

@corrective.route('/update_profile_mt', methods=['POST'])
def update_profile_mt():
    try:
        mt_id = session.get('id_mt')

        nome = request.form.get('nome')
        n_tecnico = request.form.get('n_tecnico')
        card_number = request.form.get('card_number')
        username = request.form.get('username')
        email = request.form.get('email')
        sap_user = request.form.get('sap_user')
        sap_pass = request.form.get('sap_pass')

        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        query = """
            UPDATE tecnicos
            SET nome = ?, n_tecnico = ?, card_number = ?, username = ?, email = ?, 
                sap_user = ?, sap_pass = ?
            WHERE id = ?
        """
        cursor.execute(query, (nome, n_tecnico, card_number, username, email, sap_user, sap_pass, mt_id))
        conn.commit()
        flash('Perfil atualizado com sucesso!', category='success')

        return redirect(url_for('mt_profile_page'))

    except Exception as e:
        print(e)
        return jsonify({"error": "Erro ao salvar alterações"}), 500

def aguardar_sap_order(cursor, id, max_attempts=20, sleep_interval=15):
    
    attempts = 0
    while attempts < max_attempts:
        cursor.execute(
            "SELECT sap_order_number FROM corretiva WHERE id = ?",
            (id,)
        )
        row = cursor.fetchone()

        if row and row.sap_order_number:
            return row.sap_order_number
        
        attempts += 1
        time.sleep(sleep_interval)
    
    return None
