from collections import defaultdict
import math
import os
import re
import unicodedata
from flask import Blueprint, jsonify, request, session, redirect, url_for, flash, render_template
import pyodbc
from datetime import datetime
import pyodbc
from utils.call_conn import conexao_mms, conexao_sms, conexao_capture

settings_sec = Blueprint("settings", __name__, static_folder="static", static_url_path='/Main/static', template_folder="templates")

UPLOAD_FOLDER = os.path.join('static', 'content')
ALLOWED_EXTENSIONS = {'pdf'}

@settings_sec.route('/login_settings', methods=['POST'])
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

@settings_sec.route('/settings', methods=['GET'])
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

    return redirect(url_for('settings.settings'))

@settings_sec.route('/cost_center_gamas', methods=['GET'])
def cost_center_gamas():
    if 'username' not in session:
        flash('É necessário fazer login para aceder a esta página.', category='error')
        return redirect(url_for('index'))

    try:
        username = session.get('username')
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT cost_center FROM equipments")
        centros_custo = cursor.fetchall()

        return render_template('configs/cost_center_gamas.html', 
                               maintenance="Settings", 
                               username=username,
                               centros_custo=centros_custo)

    except Exception as e:
        print(e)
        flash(f'Ocorreu um erro: {str(e)}', category='error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('settings.settings'))

@settings_sec.route('/gamas/<cost_center>', methods=['GET'])
def gamas(cost_center):
    if 'username' not in session:
        flash('É necessário fazer login para aceder a esta página.', category='error')
        return redirect(url_for('index'))

    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT e.id, e.equipment
            FROM equipments e
            WHERE e.cost_center = ?
        """, (cost_center,))
        equipamentos = cursor.fetchall()

        return render_template('configs/components/_equipments_content.html', 
                               equipamentos=equipamentos,
                               cost_center=cost_center)

    except Exception as e:
        print(e)
        flash(f'Ocorreu um erro: {str(e)}', category='error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('settings.cost_center_gamas'))

@settings_sec.route('/gama_associate/<cost_center>', methods=['GET'])
def gama_associate(cost_center):

    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT e.id, e.equipment
            FROM equipments e
            WHERE e.cost_center = ?
        """, (cost_center,))
        rows = cursor.fetchall()
        equipamentos = [{'id': row[0], 'equipment': row[1]} for row in rows]

        cursor.close()
        conn.close()
        
        return jsonify(equipamentos)

    except Exception as e:
        print(e)
        flash(f'Ocorreu um erro: {str(e)}', category='error')

    return redirect(url_for('settings.cost_center_gamas'))

@settings_sec.route('/get_all_gamas', methods=['GET'])
def get_all_gamas():
    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("SELECT id, [desc] FROM gama ORDER BY [desc] ASC")
        gamas = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify([{'id': g[0], 'descricao': g[1]} for g in gamas])

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

@settings_sec.route('/gamas_do_equipamento/<equipamento_id>', methods=['GET'])
def gamas_do_equipamento(equipamento_id):
    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT g.id as gama_id, g.[desc] as gama_desc, p.id as periocity_id, p.periocity
            FROM equipment_gama eg
            JOIN gama g ON eg.id_gama = g.id
            JOIN periocity p ON eg.id_periocity = p.id
            WHERE eg.id_equipment = ?
        """, (equipamento_id,))
        gamas = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify([
            {
                'gama_id': g.gama_id,
                'gama_desc': g.gama_desc,
                'periocity_id': g.periocity_id,
                'periocity': g.periocity
            } for g in gamas
        ])

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

@settings_sec.route("/unlink_gama/", methods=["DELETE"])
def unlink_gama():
    data = request.json
    equipamento_id = data.get("id_equipment")
    gama_id = data.get("id_gama")
    periocity_id = data.get("id_periocity")

    if not equipamento_id or not gama_id or not periocity_id:
        return jsonify({"error": "Parâmetros inválidos"}), 400

    conn = pyodbc.connect(conexao_mms)
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM equipment_gama 
        WHERE id_equipment = ? AND id_gama = ? AND id_periocity = ?
    """, (equipamento_id, gama_id, periocity_id))
    
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Gama e equipamento desassociados com sucesso"}), 200

@settings_sec.route('/get_periocities', methods=['GET'])
def get_periocities():
    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("SELECT id, periocity FROM periocity")
        periocities = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify([
            {'id': p.id, 'periocity': p.periocity} for p in periocities
        ])

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

@settings_sec.route('/add_gama_to_equipment', methods=['POST'])
def add_gama_to_equipment():
    try:
        descricao_gama = request.form['descricao']
        periodicidade = request.form['periodicidade']
        equipamento_id = request.form['equipamento']

        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO gama ([desc]) 
            OUTPUT INSERTED.id
            VALUES (?)
        """, descricao_gama)
        
        gama_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO equipment_gama (id_equipment, id_gama, id_periocity)
            VALUES (?, ?, ?)
        """, equipamento_id, gama_id, periodicidade)
        cursor.commit()
        cursor.close()  
        
        flash('Gama associada ao equipamento com sucesso!', category='success')
    except Exception as e:
        flash(f'Ocorreu um erro: {str(e)}', category='error')

    return redirect(request.referrer)

@settings_sec.route('/associate_gama_to_equipment', methods=['POST'])
def associate_gama_to_equipment():
    try:
        descricao_gama = request.form['descricao']
        periodicidade = request.form['periodicidade']
        equipamento_id = request.form['equipamento']
        nova_gama = request.form['novaGama']
        
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        if descricao_gama == 'outra' and nova_gama:
            cursor.execute("""
                INSERT INTO gama ([desc]) 
                OUTPUT INSERTED.id
                VALUES (?)
            """, (nova_gama,))
            gama_id = cursor.fetchone()[0]
        else:
            gama_id = descricao_gama

        cursor.execute("""
            INSERT INTO equipment_gama (id_equipment, id_gama, id_periocity)
            VALUES (?, ?, ?)
        """, (equipamento_id, gama_id, periodicidade))

        conn.commit()
        cursor.close()

        flash('Gama associada ao equipamento com sucesso!', category='success')
        return jsonify({'success': True})

    except Exception as e:
        print(e)
        flash(f'Ocorreu um erro: {str(e)}', category='error')
        return jsonify({'error': str(e)}), 500

@settings_sec.route('/adicionar_equipamento', methods=['POST'])
def adicionar_equipamento():
    data = request.get_json()
    cost_center = data['costCenter']
    equipment = data['equipment']
    descricao = data['descricao']
    
    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO equipments (equipment, [desc], cost_center)
            VALUES (?, ?, ?)
        """, (equipment, descricao, cost_center))

        conn.commit()
        flash('Equipamento adicionado com sucesso!', category='success')
        return jsonify({'success': True})

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

@settings_sec.route('/get_gama_e_periocidade/<int:gama_id>', methods=['GET'])
def get_gama_e_periocidade(gama_id):
    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT e.equipment, g.id, g.[desc] AS gama_desc, p.id AS periocity_id, p.periocity, e.id
            FROM equipments e
            JOIN equipment_gama eg ON e.id = eg.id_equipment
            JOIN gama g ON eg.id_gama = g.id
            JOIN periocity p ON eg.id_periocity = p.id
            WHERE g.id = ?
        """, (gama_id,))
        result = cursor.fetchone()

        if not result:
            return jsonify({'error': 'Gama não encontrada.'}), 404

        return jsonify({
            'equipamento': result[0],
            'id_gama': result[1],
            'gama_desc': result[2],
            'periocity_id': result[3],
            'periocity': result[4],
            'equipamento_id': result[5]
        })

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

@settings_sec.route('/update_gama_e_periocidade', methods=['POST'])
def update_gama_e_periocidade():
    data = request.get_json()
    equipamento_id = data['equipamentoId']
    gama_desc = data['gamaDesc']
    periocity_id = data['periocityId']
    id_gama = data['idGama']
    old_periocity_id = data['oldPeriocityId']

    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE gama
            SET [desc] = ?
            WHERE id = ?
        """, (gama_desc, id_gama))

        if periocity_id != old_periocity_id:
            cursor.execute("""
                UPDATE equipment_gama
                SET id_periocity = ?
                WHERE id_equipment = ? AND id_gama = ?
            """, (periocity_id, equipamento_id, id_gama))

        conn.commit()
        flash('Gama atualizada com sucesso!', category='success')
        return jsonify({'success': True})
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

@settings_sec.route('/wi', methods=['GET'])
def wi():
    if 'username' not in session:
        flash('É necessário fazer login para aceder a esta página.', category='error')
        return redirect(url_for('index'))
    try:
        username = session.get('username')
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("SELECT id, [desc] FROM gama")
        gamas = cursor.fetchall()

        selected_gama_id = request.args.get('gama_id')
        selected_gama = request.args.get('gama')
        tasks = []
        if selected_gama_id:
            cursor.execute("""
                SELECT t.id, t.descricao
                FROM tarefas t
                INNER JOIN tarefas_gama tg ON t.id = tg.tarefa_id
                WHERE tg.gama_id = ?
            """, (selected_gama_id,))
            tasks = cursor.fetchall()

        return render_template('configs/wi.html', 
                               maintenance="Settings", 
                               username=username,
                               gamas=gamas,
                               tasks=tasks,
                               selected_gama_id=selected_gama_id, 
                               selected_gama=selected_gama
                               )
    except Exception as e:
        print(e)
        flash(f'Ocorreu um erro: {str(e)}', category='error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('settings.settings'))

@settings_sec.route('/create_wi', methods=['POST'])
def create_wi():
    if 'username' not in session:
        flash('É necessário fazer login para aceder a esta página.', category='error')
        return redirect(url_for('index'))
    try:
        wi_tasks_str = request.form.get('wi_tasks', "").strip()
        gama_id = request.form.get('gama_id')

        if not wi_tasks_str:
            raise Exception("Nenhuma tarefa escrita.")

        tasks_list = [task.strip() for task in wi_tasks_str.split(';') if task.strip()]
        if not tasks_list:
            raise Exception("Nenhuma tarefa válida foi escrita.")

        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        for task in tasks_list:
            cursor.execute("INSERT INTO tarefas (descricao) VALUES (?)", (task,))
            conn.commit()

            cursor.execute("SELECT @@IDENTITY AS id")
            row = cursor.fetchone()
            tarefa_id = row.id if row else None

            if tarefa_id is None:
                raise Exception(f"Erro ao recuperar o ID da tarefa '{task}'.")

            if gama_id:
                cursor.execute("INSERT INTO tarefas_gama (tarefa_id, gama_id) VALUES (?, ?)", (tarefa_id, gama_id))

        conn.commit()

        flash("Tarefas criadas com sucesso!", category='success')
        return redirect(url_for('settings.wi'))

    except Exception as e:
        print(e)
        flash(f'Ocorreu um erro: {str(e)}', category='error')
        return redirect(url_for('settings.wi'))
    finally:
        cursor.close()
        conn.close()

@settings_sec.route('/remove_task_from_gama', methods=['POST'])
def remove_task_from_gama():
    if 'username' not in session:
        return jsonify({"success": False, "message": "É necessário fazer login"}), 403

    try:
        data = request.get_json()
        tarefa_id = data.get("tarefa_id")
        gama_id = data.get("gama_id")

        if not tarefa_id or not gama_id:
            return jsonify({"success": False, "message": "Dados inválidos"}), 400

        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM tarefas_gama WHERE tarefa_id = ? AND gama_id = ?", (tarefa_id, gama_id))
        conn.commit()
        flash("Tarefa removida com sucesso!", category='warning')
        return jsonify({"success": True})
    except Exception as e:
        print("Erro:", e)
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@settings_sec.route('/add_task_to_gama', methods=['POST'])
def add_task_to_gama():
    if 'username' not in session:
        return jsonify({"success": False, "message": "É necessário fazer login"}), 403

    try:
        data = request.get_json()
        tarefa_id = data.get("tarefa_id")
        gama_id = data.get("gama_id")

        if not tarefa_id or not gama_id:
            return jsonify({"success": False, "message": "Dados inválidos"}), 400

        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM tarefas_gama WHERE tarefa_id = ? AND gama_id = ?", (tarefa_id, gama_id))
        if cursor.fetchone():
            return jsonify({"success": False, "message": "Tarefa já associada a esta gama"}), 400

        cursor.execute("INSERT INTO tarefas_gama (tarefa_id, gama_id) VALUES (?, ?)", (tarefa_id, gama_id))
        conn.commit()   
        flash("Tarefa associada à gama com sucesso!", category='success')
        return jsonify({"success": True})
    except Exception as e:
        print("Erro:", e)
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@settings_sec.route('/get_unassigned_tasks/<int:gama_id>', methods=['GET'])
def get_unassigned_tasks(gama_id):
    conn = pyodbc.connect(conexao_mms)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT t.id, t.descricao
        FROM tarefas t
        WHERE t.id NOT IN (
            SELECT tg.tarefa_id FROM tarefas_gama tg WHERE tg.gama_id = ?
        )
    """, (gama_id,))
    
    unassigned_tasks = [{"id": row[0], "descricao": row[1]} for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    return jsonify(unassigned_tasks)

@settings_sec.route("/get_tasks_for_gama/<int:gama_id>")
def get_tasks_for_gama(gama_id):
    conn = pyodbc.connect(conexao_mms)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.id, t.descricao FROM tarefas t
        JOIN tarefas_gama tg ON t.id = tg.tarefa_id
        WHERE tg.gama_id = ?""" 
    , (gama_id,))

    tasks = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify([{"id": t.id, "descricao": t.descricao} for t in tasks])

@settings_sec.route("/tasks_for_gama/<int:gama_id>/")
def tasks_for_gama(gama_id):
    conn = pyodbc.connect(conexao_mms)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.id, t.descricao FROM tarefas t
        JOIN tarefas_gama tg ON t.id = tg.tarefa_id
        WHERE tg.gama_id = ?""" 
    , (gama_id,))

    gama_tasks = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify([{"id": t.id, "descricao": t.descricao} for t in gama_tasks])

@settings_sec.route('/admin_tl', methods=['GET'])
def admin_tl():

    try:
        username = session.get('username')
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        role="TL"
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
                @FilterNum = ?,
                @Role = ?
        """, page, page_size, filtro_area, filtro_turno, filtro_num, role)
        
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

    return redirect(url_for('settings.admin_tl'))

@settings_sec.route('/reports', methods=['GET'])
def list_reports():
    try:
        conn = pyodbc.connect(conexao_capture)
        cursor = conn.cursor()
        
        page = request.args.get('page', 1, type=int)
        filter_area = request.args.get('filter_area')
        page_size = 20
        offset = (page - 1) * page_size

        base_query = "SELECT * FROM report_email_novo"
        count_query = "SELECT COUNT(*) FROM report_email_novo"
        params = []

        if filter_area:
            base_query += " WHERE inicial = ?"
            count_query += " WHERE inicial = ?"
            params.append(filter_area)

        base_query += " ORDER BY id OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        params.extend([offset, page_size])

        cursor.execute(base_query, params)
        reports = cursor.fetchall()

        if filter_area:
            cursor.execute(count_query, (filter_area,))
        else:
            cursor.execute(count_query)
        total_registros = cursor.fetchone()[0]
        total_paginas = math.ceil(total_registros / page_size)

        return render_template(
            'configs/reports.html',
            reports=reports,
            current_page=page,
            total_paginas=total_paginas,
            filter_area=filter_area
        )

    except Exception as e:
        print(e)
        flash(f'Ocorreu um erro: {str(e)}', category='error')
        return redirect(url_for('settings.list_reports'))
    finally:
        cursor.close()
        conn.close()

@settings_sec.route('/reports/new', methods=['GET', 'POST'])
def new_report():
    if request.method == 'POST':
        nome = request.form.get('destinatario')
        inicial = request.form.get('filter_area_add')
        destinatario = f'{nome}@borgwarner.com'
        
        try:
            conn = pyodbc.connect(conexao_capture)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT DISTINCT area FROM report_email_novo where inicial = ?", inicial,
            )
            area_list = cursor.fetchone()
            area = area_list[0]
            
            print(area, destinatario, inicial)
            cursor.execute(
                "INSERT INTO report_email_novo (area, destinatario, inicial) VALUES (?, ?, ?)",
                (area, destinatario, inicial)
            )
            conn.commit()
            
            flash('Report criado com sucesso!', 'success')
            return redirect(url_for('settings.list_reports'))
        except Exception as e:
            print(e)
            flash(f'Erro ao criar report: {str(e)}', 'error')
            return redirect(url_for('settings.list_reports'))
        finally:
            cursor.close()
            conn.close()

@settings_sec.route('/reports/delete/<int:id>', methods=['POST'])
def delete_report(id):
    try:
        conn = pyodbc.connect(conexao_capture)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM report_email_novo WHERE id = ?", (id,))
        conn.commit()
        flash('Report excluído com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir report: {str(e)}', 'error')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('settings.list_reports'))

@settings_sec.route('/admin_mtl', methods=['GET'])
def admin_mtl():

    try:
        username = session.get('username')
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        role="MTL"
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
                @FilterNum = ?,
                @Role = ?
        """, page, page_size, filtro_area, filtro_turno, filtro_num, role)
        
        mtls = cursor.fetchall()
        if mtls:
            total_records = mtls[0].total_count
            total_pages = (total_records + page_size - 1) // page_size
        else:
            total_records = 0
            total_pages = 1

        start_page = max(1, page - 3)
        end_page = min(total_pages, page + 3)

        return render_template(
            'configs/mtl.html',
            maintenance="Settings",
            username=username,
            mtls=mtls,
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

    return redirect(url_for('settings.admin_mtl'))

@settings_sec.route('/admin_avarias', methods=['GET', 'POST'])
def admin_avarias():

    try:
        username = session.get('username')
        conn = pyodbc.connect(conexao_capture)
        cursor = conn.cursor()

        cursor.execute("EXEC MMS.dbo.AvariasPorArea")

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

    return redirect(url_for('settings.admin_avarias'))

@settings_sec.route('/add_avaria/<area>', methods=['POST'])
def add_avaria(area):

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

    return redirect(url_for('settings.admin_avarias'))

@settings_sec.route('/edit_avaria/<area>', methods=['POST'])
def edit_avaria(area):

    try:
        id_tipo = request.form['id']
        tipo = request.form['tipo']
        
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()
        print(id_tipo, tipo, area)
        cursor.execute("EXEC AddTipoAvaria @id=?, @tipo=?, @area=?", id_tipo, tipo, area)
        conn.commit()

        flash('Tipo de avaria atualizado com sucesso!', category='success')
        return redirect(url_for('settings.admin_avarias'))

    except Exception as e:
        flash(f'Ocorreu um erro: {str(e)}', category='error')
        return redirect(url_for('settings.admin_avarias'))

    finally:
        cursor.close()
        conn.close()

@settings_sec.route('/update_teamleader', methods=['POST'])
def update_teamleader():

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

    return redirect(url_for('settings.admin_tl'))

@settings_sec.route('/add_teamleader', methods=['POST'])
def add_teamleader():

    try:
        username = request.form['username']
        n_colaborador = request.form['n_colaborador']
        turno = request.form['turno']
        area = request.form['area']
        email = username + '@borgwarner.com'
        password = request.form['password']
        card = request.form['card']
        role = request.form['role']

        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()
        print(username, n_colaborador, turno, area, email, password, card, role)
        cursor.execute("""
            INSERT INTO [dbo].[teamleaders] (username, password, n_colaborador, turno, area, email, card_number, role)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, username, password, n_colaborador, turno, area, email, card, role)

        conn.commit()
        flash('Team Leader adicionado com sucesso!', category='success')

    except Exception as e:
        flash(f'Ocorreu um erro: {str(e)}', category='error')
    finally:
        cursor.close()
        conn.close()

    return redirect(request.referrer)

@settings_sec.route('/delete_tl/<int:id>', methods=['POST'])
def delete_tl(id):
    
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

    return redirect(url_for('settings.admin_mt'))

@settings_sec.route('/admin_mt', methods=['GET'])
def admin_mt():

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

    return redirect(url_for('settings.settings'))

@settings_sec.route('/update_mt', methods=['POST'])
def update_mt():

    try:
        id = request.form['id']
        area = request.form['area']
        n_card = request.form['n_card']
        nome = request.form['nome']
        
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE [dbo].[tecnicos]
            SET area = ?, card_number = ?, nome = ? 
            WHERE id = ?
        """, area, n_card, nome, id)
        
        conn.commit()
        flash('Dados atualizados com sucesso!', category='success')
        
    except Exception as e:
        print(e)
        flash(f'Ocorreu um erro: {str(e)}', category='error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('settings.admin_mt'))

@settings_sec.route('/add_mt', methods=['POST'])
def add_mt():

    try:
        username = request.form['username']
        n_colaborador = request.form['n_colaborador']
        area = request.form['area']
        email = username + '@borgwarner.com'
        password = request.form['password']
        nome = request.form['nome']
        n_card = request.form['card']

        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO [dbo].[tecnicos] (username, nome, password, n_tecnico, area, email, card_number)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, username, nome, password, n_colaborador, area, email, n_card)

        conn.commit()
        flash('Técnico adicionado com sucesso!', category='success')

    except Exception as e:
        flash(f'Ocorreu um erro: {str(e)}', category='error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('settings.admin_mt'))

@settings_sec.route('/delete_mt/<int:id>', methods=['POST'])
def delete_mt(id):
    
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

    return redirect(url_for('settings.admin_mt'))

@settings_sec.route('/contacts', methods=['GET'])
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
            nome=nome, 
            maintenance="Settings"
        )
    except Exception as e:
        print(f"Error fetching contacts: {e}")
        return "Error loading contacts", 500

@settings_sec.route('/contacts/add', methods=['POST'])
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
        flash('Contacto adicionado com sucesso!', category='success')
        return redirect(url_for('settings.contacts'))
    except Exception as e:
        print(f"Error adding contact: {e}")
        return "Error adding contact", 500

@settings_sec.route('/pl_areas', methods=['GET'])
def pl_areas():
    try:
        page = int(request.args.get('page', 1)) 
        page_size = int(request.args.get('page_size', 40))
        conn = pyodbc.connect(conexao_capture)

        cursor = conn.cursor()

        cursor.execute("""
            SELECT[id]
                ,[area]
                ,[nome_PL]
            FROM [Capture].[dbo].[Area_PL]
        """)
        rows = cursor.fetchall()

        cursor.execute("""
            SELECT count(*)
            FROM [Capture].[dbo].[Area_PL]
        """)
        total_count = cursor.fetchone()[0]
        pls = []

        for row in rows:
            pl = {
                "id": row.id,
                "Area": row.area,
                "PL": row.nome_PL
            }
            pls.append(pl)

        total_pages = (total_count + page_size - 1) // page_size
        start_page = max(1, page - 3)
        end_page = min(total_pages, page + 3)
        
        return render_template(
            'configs/pl_areas.html',
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            pls=pls,
            start_page=start_page,
            end_page=end_page,
            maintenance="Settings"
        )
    except Exception as e:
        print(e)
        flash(f'Ocorreu um erro: {str(e)}', category='error')
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('settings.settings'))

@settings_sec.route('/update_pl/<int:pl_id>', methods=['POST'])
def update_pl(pl_id):
    try:
        data = request.get_json()
        pl_name = data.get('plName')

        conn = pyodbc.connect(conexao_capture)
        cursor = conn.cursor()

        update_query = """
            UPDATE [Capture].[dbo].[Area_PL]
            SET nome_PL = ?
            WHERE id = ?
        """
        cursor.execute(update_query, (pl_name, pl_id))
        conn.commit()

        return jsonify({'message': 'PL atualizado com sucesso!'}), 200

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@settings_sec.route('/insert_pl', methods=['POST'])
def insert_pl():
    try:
        data = request.get_json()
        area = data.get('area')
        pl_name = data.get('plName')

        conn = pyodbc.connect(conexao_capture)
        cursor = conn.cursor()

        insert_query = """
            INSERT INTO [Capture].[dbo].[Area_PL] (area, nome_PL)
            VALUES (?, ?)
        """
        cursor.execute(insert_query, (area, pl_name))
        conn.commit()

        return jsonify({'message': 'PL inserido com sucesso!'}), 200

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@settings_sec.route('/contacts/remove', methods=['POST'])
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
        return redirect(url_for('settings.contacts'))
    except Exception as e:
        print(f"Error removing contact: {e}")
        return "Error removing contact", 500

@settings_sec.route('/contacts/edit/<int:id>', methods=['POST'])
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
        return redirect(url_for('settings.contacts'))
    except Exception as e:
        print(f"Error editing contact: {e}")
        return "Error editing contact", 500
    
@settings_sec.route('/mes_descriptions', methods=['GET'])
def mes_descriptions():
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))
    linha = request.args.get('filter_prod_line', None)

    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("EXEC GetDescriptions @PageNumber=?, @PageSize=?, @ProdLine=?", page, page_size, linha)
        rows = cursor.fetchall()
        descs = []
        total_count = 0
        for row in rows:
            desc = {
                "id": row.id,
                "desc": row.description,
                "prod_line": row.prod_line,
            }
            descs.append(desc)
            total_count = row.TotalCount

        total_pages = (total_count + page_size - 1) // page_size

        return render_template(
            'configs/descriptions.html',
            descs=descs,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            linha=linha,
            maintenance="Settings"
        )
    except Exception as e:
        print(f"Error fetching descriptions: {e}")
        return "Error loading descriptions", 500

def normalize_text(text):
    normalized = unicodedata.normalize('NFKD', text)
    text_without_accent = "".join(c for c in normalized if not unicodedata.combining(c))
    text_cleaned = re.sub(r'[^\w\s-]', '', text_without_accent)
    return text_cleaned.strip()

@settings_sec.route('/add_desc', methods=['POST'])
def add_desc():
    try:
        prod_line = request.form.get('filter_prod_line')
        description = request.form.get('desc')

        if not prod_line or not description:
            return "Campos obrigatórios não preenchidos.", 400

        conn = pyodbc.connect(conexao_capture)
        cursor = conn.cursor()
        description_normalized = normalize_text(description)
        cursor.execute("""
            INSERT INTO aux_fiori (prod_line, description)
            VALUES (?, ?)
        """, (prod_line, description_normalized))
        conn.commit()

        flash("Descrição adicionada com sucesso!", "success")
        return redirect(url_for('settings.mes_descriptions'))
    except Exception as e:
        print(f"Erro ao adicionar descrição: {e}")
        flash("Erro ao adicionar descrição.", "danger")
        return redirect(url_for('settings.mes_descriptions'))

@settings_sec.route('/get_desc/<int:id>', methods=['GET'])
def get_desc(id):
    try:
        conn = pyodbc.connect(conexao_capture)
        cursor = conn.cursor()

        cursor.execute("SELECT id, prod_line, description FROM aux_fiori WHERE id = ?", id)
        row = cursor.fetchone()
        if row:
            desc = {
                "id": row.id,
                "prod_line": row.prod_line,
                "description": row.description,
            }
            return jsonify(desc), 200
        else:
            return "Descrição não encontrada.", 404
    except Exception as e:
        print(f"Erro ao buscar descrição: {e}")
        return "Erro ao buscar descrição.", 500

@settings_sec.route('/edit_desc', methods=['POST'])
def edit_desc():
    try:
        id = request.form.get('editId')
        prod_line = request.form.get('editProdLine')
        description = request.form.get('editDescription')
        description_normalized = normalize_text(description)
        if not id or not prod_line or not description:
            return "Campos obrigatórios não preenchidos.", 400

        conn = pyodbc.connect(conexao_capture)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE aux_fiori
            SET prod_line = ?, description = ?
            WHERE id = ?
        """, (prod_line, description_normalized, id))
        conn.commit()

        flash("Registo atualizado com sucesso!", "success")
        return redirect(url_for('settings.mes_descriptions'))
    except Exception as e:
        print(f"Erro ao atualizar descrição: {e}")
        flash("Erro ao atualizar registo.", "danger")
        return redirect(url_for('settings.mes_descriptions'))

@settings_sec.route('/delete_desc/<int:id>', methods=['POST'])
def delete_desc(id):
    try:
        conn = pyodbc.connect(conexao_capture)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM aux_fiori WHERE id = ?", id)
        conn.commit()

        return "Registo removido com sucesso.", 200
    except Exception as e:
        print(f"Erro ao remover descrição: {e}")
        return "Erro ao remover registo.", 500

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@settings_sec.route('/update_manual', methods=['POST'])
def update_manual():
    try:
        if 'manual_pdf' not in request.files:
            flash('Nenhum ficheiro enviado.', 'error')
            return redirect(url_for('settings.settings'))

        file = request.files['manual_pdf']

        if file.filename == '':
            flash('Nenhum ficheiro selecionado.', 'error')
            return redirect(url_for('settings.settings'))

        if file and allowed_file(file.filename):
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)

            filepath = os.path.join(UPLOAD_FOLDER, 'manual.pdf')
            file.save(filepath)
            flash('Manual atualizado com sucesso!', 'success')
        else:
            flash('Ficheiro inválido. Apenas ficheiros em formato PDF são permitidos.', 'error')

    except Exception as e:
        flash(f'Ocorreu um erro ao atualizar o manual: {str(e)}', 'error')
        return redirect(url_for('settings.settings'))

    return redirect(url_for('settings.settings'))