import io
from flask import Config, Flask, flash, jsonify, redirect, render_template, request, send_file, send_from_directory, session, url_for
from datetime import date, datetime
import pyodbc
from utils.generate_pass import gerar_pass
from utils.call_conn import conexao_capture, conexao_mms
import pandas as pd
#email
from flask_mail import Mail, Message
from flask_cors import CORS
from flask_toastr import Toastr
from utils.mail_config import Config

from routes.corrective import corrective
from routes.daily import daily_sec
from routes.settings import settings_sec
from routes.preventive import preventive_sec
from routes.analytics import analytics_bp
from apscheduler.schedulers.background import BackgroundScheduler
from utils.delete_images import delete_old_photos

app = Flask(__name__)

CORS(app)

app.config.from_object(Config)
mail = Mail(app)
toastr = Toastr(app)
app.secret_key = 'secret_key_mms'

today = date.today()
year = today.strftime("%Y")

app.register_blueprint(corrective)
app.register_blueprint(daily_sec)
app.register_blueprint(settings_sec)
app.register_blueprint(preventive_sec)
app.register_blueprint(analytics_bp)

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route('/out')
def logout():

   session.pop('username', None)
   session.pop('password', None)
   session.pop('email', None)
   session.pop('workernumber', None)
   session.pop('accesslevel', None)
   session.clear()
   return redirect(url_for('index'))

@app.route('/manual')
def serve_pdf():
    return send_from_directory(
        directory='static/content', 
        path='manual.pdf',           
        mimetype='application/pdf',
    )

@app.route('/')
def index():
    logout()
    return render_template('index.html', year=year)

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

@app.route('/api/authenticate', methods=['POST'])
def authenticate_tecnico():
    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        data = request.get_json()
        card_number = data.get('card_number')
        username = data.get('username')
        password = data.get('password')

        if card_number:
            cursor.execute("""
                SELECT id, nome, ativo, password
                FROM tecnicos 
                WHERE card_number = ?
            """, card_number)
            tecnico = cursor.fetchone()
            if not tecnico:
                return jsonify({'success': False, 'message': 'Cartão inválido ou técnico não encontrado.'}), 404
            if tecnico.ativo != 1:
                return jsonify({'success': False, 'message': 'Técnico encontrado, mas não está ativo.'}), 403
        elif username and password:
            cursor.execute("""
                SELECT id, nome, ativo, password
                FROM tecnicos 
                WHERE username = ? and password = ?
            """, username, password)
            tecnico = cursor.fetchone()

            if not tecnico:
                return jsonify({'success': False, 'message': 'Nome de utilizador não encontrado.'}), 404

            if tecnico.password != password:
                return jsonify({'success': False, 'message': 'Palavra-passe incorreta.'}), 401
            if tecnico.ativo != 1:
                return jsonify({'success': False, 'message': 'Técnico encontrado, mas não está ativo.'}), 403
        else:
            return jsonify({'success': False, 'message': 'Credenciais inválidas.'}), 400

        if tecnico:
            return jsonify({
                'success': True,
                'technician_id': tecnico.id,
            })
        
        else:
            return jsonify({'success': False, 'message': 'Técnico não encontrado ou inativo'}), 404

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

@app.route('/api/get_corrective_stats')
def get_corrective_stats():
    try:
        filter_prod_line = request.args.get('filter_prod_line', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')

        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        else:
            start_date = None
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
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
          
@app.route('/api/export_corrective_records')
def export_corrective_records():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not start_date or not end_date:
        return "Erro: Ambas as datas são necessárias.", 400

    try:
        conn = pyodbc.connect(conexao_mms)
        query = """
            SELECT 
                c.id, c.id_estado, c.prod_line, c.description, c.equipament, c.stopped_production,
                c.n_operador, c.functional_location, c.main_workcenter, c.data_pedido, c.data_inicio_man,
                c.data_fim_man, c.sap_order, c.sms_date, c.tempo_manutencao, c.SMSState, c.sap_order_number,
                t.nome, ct.maintenance_comment, ct.data_inicio, ct.data_fim, ct.duracao,
                ta.tipo as tipo_avaria, ta.area
            FROM [dbo].[corretiva] c
            LEFT JOIN [dbo].[corretiva_tecnicos] ct ON c.id = ct.id_corretiva
            LEFT JOIN [dbo].[tecnicos] t ON ct.id_tecnico = t.id
            LEFT JOIN [dbo].[tipo_avaria] ta ON ct.id_tipo_avaria = ta.id
            WHERE c.data_pedido BETWEEN ? AND ?
        """
        df = pd.read_sql(query, con=conn, params=[start_date, end_date])
        conn.close()

        if df.empty:
            return "Nenhum registo encontrado para o período selecionado.", 404

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Histórico')
        output.seek(0)

        filename = f"historico_corretivas_{start_date}_a_{end_date}.xlsx"
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename,
        )
        
    except Exception as e:
        return f"Erro ao exportar: {str(e)}", 500

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
        'id': row.comentario_id,
        'tecnico_nome': row.tecnico_nome,
        'n_tecnico': row.n_tecnico,
        'maintenance_comment': row.maintenance_comment,
        'duracao_intervencao': row.duracao_intervencao,
        'tipo_avaria': row.tipo_avaria,
        'data_inicio': row.ini,
        'data_fim': row.fim
    } for row in cursor.fetchall()]
    
    return jsonify(comments)

@app.route('/api/get-ct-photos')
def get_corretiva_photos():
    comment_id = request.args.get('id', type=int)
    if comment_id is None:
        return jsonify({"error": "Parâmetro 'id' é obrigatório."}), 400

    conn = pyodbc.connect(conexao_mms)
    cursor = conn.cursor()
    cursor.execute("SELECT image_path FROM tecnicos_images WHERE id_ct = ?", comment_id)
    
    photos = [row.image_path for row in cursor.fetchall()]
    return jsonify(photos)

@app.route('/api/check_comments', methods=['GET'])
def check_comments():
    if 'id_mt' not in session:
        return jsonify({'status': 'error', 'message': 'Usuário não autenticado!'}), 403

    id_tecnico = request.args.get('id_tecnico')
    
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
        print("Erro ao verificar os comentários... - ",e)
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
        
        if not comment_id or not comment_text or not tipo_avaria_id:
            return jsonify({"status": "error", "message": "Deve preencher todos os campos."}), 401

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

@app.route('/api/lines_per_area', methods=['GET'])
def lines_per_area():
  try:
    conn = pyodbc.connect(conexao_capture)
    cursor = conn.cursor()
    
    query = """
        SELECT 
            p.area, 
            STRING_AGG(p.prod_line, ', ') AS linhas_producao,
            a.nome_PL AS PL
        FROM 
            [Capture].[dbo].[ProdLineAreaPL] p
        JOIN 
            [Capture].[dbo].[Area_PL] a
            ON p.area = a.area
        GROUP BY 
            p.area, a.nome_PL
        ORDER BY 
            p.area;
        """
    cursor.execute(query)
    rows = cursor.fetchall()
    result = []
    for row in rows:
        result.append({
            "area": row[0],
            "linhas": row[1],
            "PL": row[2]
        })

    cursor.close()
    conn.close()
    return jsonify(result)

  except Exception as e:
    print(e)
    return jsonify({'error'}), 500

@app.route('/api/get_gamas', methods=['POST'])
def get_gamas():
    try:
        data = request.get_json()
        equipment = data.get('equipment')
        if not equipment:
            return jsonify({"error": "Parâmetro 'equipment' não informado."}), 400

        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        query = """
            SELECT 
                eg.id AS equipment_gama_id,
                g.id AS gama_id,
                g.[desc] AS gama_descricao,
                p.periocity AS periodicidade,
                p.n_dias AS dias_periocity,
                MAX(hg.data_execucao) AS ultima_execucao,
                CASE 
                  WHEN MAX(hg.data_execucao) IS NULL THEN 9999 
                  ELSE DATEDIFF(DAY, MAX(hg.data_execucao), GETDATE())
                END AS dias_desde_execucao,
                CASE 
                  WHEN (CASE WHEN MAX(hg.data_execucao) IS NULL THEN 9999 ELSE DATEDIFF(DAY, MAX(hg.data_execucao), GETDATE()) END) >= p.n_dias 
                       THEN 1
                  ELSE 0
                END AS overdue
            FROM equipment_gama eg
            INNER JOIN gama g ON eg.id_gama = g.id
            INNER JOIN periocity p ON eg.id_periocity = p.id
            INNER JOIN equipments e ON eg.id_equipment = e.id
            LEFT JOIN history_gama hg ON hg.id_equipment_gama = eg.id
            WHERE e.equipment = ?
            GROUP BY eg.id, g.id, g.[desc], p.periocity, p.n_dias
        """

        cursor.execute(query, equipment)
        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append({
                "equipment_gama_id": row[0],
                "gama_id": row[1],
                "gama_descricao": row[2],
                "periodicidade": row[3],
                "dias_periocity": row[4],
                "ultima_execucao": row[5].isoformat() if row[5] is not None else None,
                "dias_desde_execucao": row[6],
                "overdue": bool(row[7])
            })

        cursor.close()
        conn.close()
        return jsonify(result)

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

@app.route('/api/update_gamas', methods=['POST'])
def update_gamas():
    try:
        data = request.get_json()
        equipment_gama_ids = data.get('equipment_gama_ids')
        if not equipment_gama_ids or not isinstance(equipment_gama_ids, list):
            return jsonify({"error": "Parâmetro 'equipment_gama_ids' inválido."}), 400

        print(equipment_gama_ids)
        
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        for eg_id in equipment_gama_ids:
            cursor.execute("SELECT COUNT(*) FROM history_gama WHERE id_equipment_gama = ?", eg_id)
            existe = cursor.fetchone()[0]
            
            if existe > 0:
                query = "UPDATE history_gama SET data_execucao = GETDATE() WHERE id_equipment_gama = ?"
                cursor.execute(query, eg_id)
            else:
                query = "INSERT INTO history_gama (id_equipment_gama, data_execucao) VALUES (?, GETDATE())"
                cursor.execute(query, eg_id)
                
        conn.commit()
        cursor.close()
        conn.close()
        flash('Tarefas atualizadas com sucesso!', category='success')
        return jsonify({"message": "Gamas atualizadas com sucesso."})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

#User Related
@app.route('/recover_password', methods=['POST'])
def recover_password():
    data = request.json
    username = data.get('username')

    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        user_email, query_update = get_user_info_and_update_query(cursor, username)

        if user_email:
            nova_senha = gerar_pass(10)

            cursor.execute(query_update, (nova_senha, username))
            conn.commit()

            msg = Message(
                subject="Recuperação de Palavra Passe",
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=[user_email]
            )
            msg.body = f"Olá {username},\n\nA sua palavra passe foi redefinida.\nA nova palavra passe é: {nova_senha}\n\nPor favor, não partilhe a sua palavra passe."

            try:
                mail.send(msg)
            except Exception as e:
                return jsonify({"error": f"Erro ao enviar o e-mail: {str(e)}"}), 500

            return jsonify({"message": "Nova palavra passe enviada com sucesso!"}), 200
        else:
            return jsonify({"error": "Utilizador não encontrado"}), 404

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

#utils
def get_user_info_and_update_query(cursor, username):
    tables = [
        ("admin", "SELECT email FROM admin WHERE username = ?", "UPDATE admin SET password = ? WHERE username = ?"),
        ("teamleaders", "SELECT email FROM teamleaders WHERE username = ?", "UPDATE teamleaders SET password = ? WHERE username = ?"),
        ("tecnicos", "SELECT email FROM tecnicos WHERE username = ?", "UPDATE tecnicos SET password = ? WHERE username = ?")
    ]

    user_email = None
    query_update = None

    for table, select_query, update_query in tables:
        cursor.execute(select_query, (username,))
        result = cursor.fetchone()

        if result:
            if user_email is not None:
                raise ValueError(f"Usuário {username} encontrado em mais de uma tabela ({table})")
            user_email = result[0]
            query_update = update_query
            break 

    return user_email, query_update


scheduler = BackgroundScheduler()
#scheduler.add_job(delete_old_photos, 'interval', days=30)
scheduler.start()

if __name__ == "__main__":
    app.run(debug=True)