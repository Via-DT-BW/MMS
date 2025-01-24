from collections import defaultdict
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
        
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE [dbo].[tecnicos]
            SET area = ?, card_number = ?
            WHERE id = ?
        """, area, n_card,id)
        
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
        return redirect(url_for('settings.contacts'))
    except Exception as e:
        print(f"Error adding contact: {e}")
        return "Error adding contact", 500

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