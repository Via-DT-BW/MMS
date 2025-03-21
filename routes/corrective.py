import os
import re
import unicodedata
import uuid
from flask import Blueprint, current_app, jsonify, request, session, redirect, url_for, flash, render_template
import pyodbc
from datetime import date, datetime
import time
import pyodbc
from utils.allowed import allowed_file
from utils.call_conn import conexao_mms, conexao_sms, conexao_capture
from werkzeug.utils import secure_filename

today = date.today()
year = today.strftime("%Y")
sidebar = True
app_name = os.getenv("APP_NAME")
#app_name = "MMS"
def sanitize_text(text):
    if text is None:
        return None
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    return text

def insert_files(cursor, ct_id, uploaded_files, upload_folder):
    invalid_files = []
    for file in uploaded_files:
        if file.filename == '':
            continue
        if allowed_file(file.filename):
            ext = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid.uuid4().hex}{ext}"
            unique_filename = secure_filename(unique_filename)
            file_path = os.path.join(upload_folder, unique_filename)
            file.save(file_path)
            relative_path = os.path.join('static', 'uploads', 'images', unique_filename)
            cursor.execute("""
                INSERT INTO tecnicos_images (id_ct, image_path)
                VALUES (?, ?)
            """, (ct_id, relative_path))
        else:
            invalid_files.append(file.filename)
    return invalid_files

corrective = Blueprint("corrective", __name__, static_folder="static", static_url_path='/Main/static', template_folder="templates")
@corrective.route('/logout')
def logout():
   session.pop('username', None)
   session.pop('password', None)
   session.pop('email', None)
   session.pop('workernumber', None)
   session.pop('accesslevel', None)
   #session.clear()
   flash('Logout realizado com sucesso', category='success')

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
            var_descricao = sanitize_text(var_descricao)
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
            
            var_descricao = sanitize_text(var_descricao)

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
            if not card.isdigit():  
                return jsonify({'success': False, 'error': 'O cartão deve conter apenas números.'}), 400
            
            if len(card) < 9:  
                return jsonify({'success': False, 'error': 'O cartão tem de ter pelo menos 9 dígitos.'}), 400

            cursor.execute(f"SELECT id, nome, username, n_tecnico, area FROM tecnicos WHERE card_number LIKE ?", ('%' + card,))
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
        tipo_manutencao = request.form.get('tipo_manutencao')
        planned_date = request.form.get('data_planeada')
        
        if planned_date:
            planned_date = datetime.strptime(planned_date, "%Y-%m-%dT%H:%M").strftime("%Y-%m-%d %H:%M:%S")
        else:
            planned_date = None
        try:
            conn = pyodbc.connect(conexao_mms)
            cursor = conn.cursor()

            create_order_by_mt = """
                Exec dbo.create_order_by_mt 
                @descricao=?, @equipamento=?, @paragem=?, @prod_line=?, @id_tecnico=?, @tipo_man = ?, @select_date = ?
            """
            cursor.execute(
                create_order_by_mt,
                var_descricao, equipament_var, paragem_producao, prod_line, 
                var_numero_tecnico, tipo_manutencao, planned_date
            )
            conn.commit()

            flash('Notificação enviada com sucesso', category='success')
            return redirect(url_for('corrective.inwork'))
        except Exception as e:
          print(e)
          flash(f'Ocorreu um erro: {str(e)}', category='error')
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('corrective.inwork'))

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

        cursor.execute('SELECT equipament FROM corretiva WHERE id = ?', id_corretiva)
        row = cursor.fetchone()
        if row is None:
            return jsonify({'error': 'Pedido não encontrado'}), 404
        equipamento = row[0]

        cursor.execute('''
            SELECT id FROM corretiva
            WHERE equipament = ? AND id_estado = 2 AND id <> ?
        ''', (equipamento, id_corretiva))
        pedido_andamento = cursor.fetchone()

        if pedido_andamento:
            id_pedido_andamento = pedido_andamento[0]
            cursor.execute('''
                UPDATE corretiva
                SET id_estado = 3, data_fim_man = ?
                WHERE id = ?
            ''', (data_atual, id_pedido_andamento))
        
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

    return redirect(url_for('corrective.inwork'))

@corrective.route('/finish_maintenance', methods=['POST'])
def finish_maintenance():
    id = request.form.get('id_tecnico')
    id_corretiva = request.form.get('id_corretiva')
    maintenance_comment = request.form.get('comment')
    id_tipo_avaria = request.form.get('id_tipo_avaria')
    elegivel = request.form.get('elegivel_sistemica')
    definida = request.form.get('definida_acao') 
    
    elegivel_bit = 1 if elegivel == "Sim" else 0
    definida_bit = 1 if definida == "Sim" else 0

    if not id or not maintenance_comment:
        return jsonify({'error': 'Parâmetros insuficientes'}), 400

    data_atual = datetime.now()
    
    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id FROM corretiva_tecnicos
            WHERE id_corretiva = ? AND id_tecnico = ? and data_fim IS NULL
        ''', (id_corretiva, id))
        row = cursor.fetchone()

        if not row:
            return jsonify({'error': 'Registo nao encontrado para finalizar manutencao'}), 404
        else:
            id_ct = row.id

        cursor.execute('''
            UPDATE corretiva_tecnicos
            SET maintenance_comment = ?, 
                data_fim = ?, 
                id_tipo_avaria = ?,
                elegivel_sistemica = ?, 
                definida_acao = ?
            WHERE id = ?
        ''', (maintenance_comment, data_atual, id_tipo_avaria, elegivel_bit, definida_bit, id_ct))

        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'images')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        invalid_files = []
        files = request.files.getlist("images[]")
        invalid_files = insert_files(cursor, id_ct, files, upload_folder)
        
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
        
        if invalid_files and len(invalid_files) > 0:
            message = (f"Manutenção Concluída!"
                       f"No entanto, os seguintes ficheiros têm tipos inválidos e não foram carregados: "
                       f"{', '.join(invalid_files)}")
            flash(message, category='warning')
            logout()
            return jsonify({'status': 'warning', 'message': message})
        else:
            flash('Manutenção finalizada e imagens adicionadas com sucesso!', category='success')
            logout()
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

        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        filter_equipment = request.args.get('filter_equipment', '', type=str)
        start_date = request.args.get('start_date', type=str)
        end_date = request.args.get('end_date', type=str)
        filter_prod_line = request.args.get('filter_prod_line', '', type=str)
        print(filter_equipment)
        
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

    return redirect(url_for('corrective.finished'))

@corrective.route('/pending_comments', methods=['GET'])
def pending_comments():
    try:
        if 'id_mt' not in session:
            flash('Usuário não autenticado!', category='error')
            return redirect(url_for('corrective.login'))
        
        tecnico_id = session['id_mt']
        
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        filter_equipment = request.args.get('filter', '', type=str)
        start_date = request.args.get('start_date', type=str) or None
        end_date = request.args.get('end_date', type=str) or None
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
        return redirect(url_for('corrective.pending_comments'))
    finally:
        cursor.close()
        conn.close()

@corrective.route('/pedido_spares/<int:id>', methods=['POST'])
def pedido_spares(id):
    
    max_tentativas = 3
    tentativa = 0

    while tentativa < max_tentativas:
        try:
            conn = pyodbc.connect(conexao_mms)
            cursor = conn.cursor()

            query = "INSERT INTO rpa_corretiva (id_tecnico, id_corretiva) VALUES (?, ?)"
            cursor.execute(query, (session['id_mt'], id))
            cursor.commit()

            sap_order_number = aguardar_sap_order(cursor, id)

            if sap_order_number:
                return jsonify({"message": f"Ordem {sap_order_number} criada com sucesso!"}), 200
            else:
                raise Exception("Tempo limite atingido")

        except Exception as e:
            print(f"Erro: {e}")
            if cursor:
                cursor.execute("DELETE FROM rpa_corretiva WHERE id_tecnico = ? AND id_corretiva = ?", 
                               (session['id_mt'], id))
                cursor.commit()

            tentativa += 1

            if tentativa == max_tentativas:
                return jsonify({"error": "Falha ao criar a ordem após várias tentativas."}), 500
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

@corrective.route('/mt_profile', methods=['GET'])
def mt_profile_page():
    turnos = [
        ("A", "Manhã"),
        ("B", "Tarde"),
        ("C", "Noite"),
        ("D", "Intermédio"),
        ("E", "Fim de semana (6h-18h)"),
        ("F", "Fim de semana (18h-6h)"),
    ]
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
                "email": row.email
            }
            
            shift = get_mt_shift(row.n_tecnico)
            
            return render_template('corrective/mt_profile.html',maintenance="Perfil", tecnico=tecnico, shift=shift, turnos=turnos)
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
        password = request.form.get('password')
        #sap_user = request.form.get('sap_user')
        #sap_pass = request.form.get('sap_pass')
        turno = request.form.get('turno')
        actual_shift = get_mt_shift(n_tecnico)
        print(f"Turno: ", turno + " Atual: ", actual_shift)
        if actual_shift != turno:
            update_shift(n_tecnico, turno)
        
        if not password or len(password) < 6:
            flash('A password deve ter pelo menos 6 caracteres.', category='error')
            return redirect(url_for('corrective.mt_profile_page'))
        
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        query = """
            UPDATE tecnicos
            SET nome = ?, n_tecnico = ?, card_number = ?, username = ?, email = ?, password = ?
            WHERE id = ?
        """
        cursor.execute(query, (nome, n_tecnico, card_number, username, email, password, mt_id))
        conn.commit()
        flash('Perfil atualizado com sucesso!', category='success')

        return redirect(url_for('corrective.mt_profile_page'))

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

def get_mt_shift(n_tecnico):
    conn = pyodbc.connect(conexao_sms)
    cursor = conn.cursor()

    query = "SELECT Shift FROM [Contacts] WHERE numberBW = ?"
    cursor.execute(query, (n_tecnico,))
    row = cursor.fetchone()
    
    return row.Shift if row else None

def update_shift(n_tecnico, turno):
    try:
        conn = pyodbc.connect(conexao_sms)
        cursor = conn.cursor()

        query = "UPDATE [Contacts] SET Shift = ? WHERE numberBW = ?"
        cursor.execute(query, (turno, n_tecnico))
        conn.commit()
        cursor.close()
        
        return {"success": True, "message": "Turno atualizado com sucesso."}
    
    except pyodbc.Error as e:
        print(e)
        return {"success": False, "message": f"Erro ao atualizar turno: {e}"}

@corrective.route('/get_equipments', methods=['GET'])
def get_equipments():
    try:
        prod_line = request.args.get('prod_line', '')
        conn = pyodbc.connect(conexao_capture)
        cursor = conn.cursor()
        if prod_line:
            query = "SELECT [id], [Equipment] FROM [Capture].[dbo].[EquipamentSAP] WHERE [ProdLine] LIKE ?"
            cursor.execute(query, prod_line + '%')
            results = cursor.fetchall()

            if not results and '-' in prod_line:
                new_prod_line = prod_line.split('-')[0]
                cursor.execute(query, new_prod_line)
                results = cursor.fetchall()

        equipamentos = [{"id": row.id, "Equipment": row.Equipment} for row in results]
        return jsonify(equipamentos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@corrective.route('/api/update_comment', methods=['POST'])
def update_comment():
    id_corretiva = request.form.get('id_corretiva')
    id_tecnico = request.form.get('id_tecnico')
    comment = request.form.get('comment')
    id_tipo_avaria = request.form.get('id_tipo_avaria')
    parou = request.form.get('stopped_prod')
    elegivel = request.form.get('elegivel_sistemica')
    definida = request.form.get('definida_acao') 
    
    elegivel_bit = 1 if elegivel == "Sim" else 0
    definida_bit = 1 if definida == "Sim" else 0

    if not id_corretiva or not id_tecnico or not comment:
        return jsonify({'error': 'Parâmetros insuficientes'}), 400

    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id FROM corretiva_tecnicos
            WHERE id_corretiva = ? AND id_tecnico = ? and data_fim IS NULL
        ''', (id_corretiva, id_tecnico))
        row = cursor.fetchone()

        if not row:
            return jsonify({'error': 'Registo nao encontrado para atualizacao'}), 404
        else:
            id_ct = row.id
        
        cursor.execute('''
            UPDATE corretiva_tecnicos
            SET maintenance_comment = ?, 
                id_tipo_avaria = ?, 
                data_fim = GETDATE(),
                elegivel_sistemica = ?, 
                definida_acao = ?
            WHERE id = ?
        ''', (comment, id_tipo_avaria, elegivel_bit, definida_bit, id_ct))

        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'images')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        invalid_files = []
        files = request.files.getlist("images[]")
        invalid_files = insert_files(cursor, id_ct, files, upload_folder)
        
        cursor.execute('''
            UPDATE corretiva
            SET stopped_production = ?
            WHERE id = ?
        ''', (parou, id_corretiva))
        
        if cursor.rowcount == 0:
            flash('Registo não encontrado para atualização', category='error')
            return jsonify({'status': 'error', 'message': 'Registo não encontrado para atualização!'}), 404

        conn.commit()
        if invalid_files and len(invalid_files) > 0:
            message = (f"Intervenção Concluída!"
                       f"No entanto, os seguintes ficheiros têm tipos inválidos e não foram carregados: "
                       f"{', '.join(invalid_files)}")
            flash(message, category='warning')
            return jsonify({'status': 'warning', 'message': message})
        else:
            flash('Intervenção terminada e imagens adicionadas com sucesso!', category='success')
            return jsonify({'status': 'success', 'message': 'Comentários e imagens adicionados com sucesso!'})
    except Exception as e:
        print(e)
        flash('Erro ao fazer o comentário!', category='error')
        return jsonify({'status': 'error', 'message': 'Erro ao fazer o comentário!'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

