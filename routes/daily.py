import os
import uuid
from flask import Blueprint, json, jsonify, request, current_app, session, redirect, url_for, flash, render_template
import pyodbc
from datetime import datetime, timedelta
import pyodbc
from werkzeug.utils import secure_filename
from utils.call_conn import conexao_mms

daily_sec = Blueprint("daily", __name__, static_folder="static", static_url_path='/Main/static', template_folder="templates")

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def empty_to_none(value):
    return None if value == "" else value

def insert_files(cursor, daily_id, uploaded_files, upload_folder):

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
                INSERT INTO daily_images (id_daily, image_path)
                VALUES (?, ?)
            """, (daily_id, relative_path))
        else:
            invalid_files.append(file.filename)
    return invalid_files

@daily_sec.route('/daily', methods=['GET'])
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
        role = session.get('role')
        id_tl = session.get('id_tl')

        now = datetime.now()
        cutoff = now - timedelta(hours=12)
        
        cursor.execute("""
            SELECT id
            FROM daily
            WHERE id_tl = ? AND data >= ?
        """, id_tl, cutoff)
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
                @area = ?,
                @Role = ?
            """,
            filter_turno, filter_tl, start_date, end_date, page_size, page, area, role
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
                (tl.area = ?) AND
                (tl.role = ?)
                
        """
        cursor.execute(count_query, filter_turno, filter_turno, filter_tl, filter_tl, start_date, start_date, end_date, end_date, area, role)
        total_records = cursor.fetchone()[0]
        
        total_pages = (total_records + page_size - 1) // page_size
        start_page = max(1, page - 3)
        end_page = min(total_pages, page + 3)

        return render_template('daily/log.html', 
                               maintenance="Comentários Diários", 
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

    return redirect(url_for('daily.daily'))

@daily_sec.route('/login_daily', methods=['POST'])
def login_daily():
    try:
        username = request.form.get('username')
        password = request.form.get('password')

        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("SELECT id, username, area, role, turno FROM teamleaders WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()

        if user:
            session['username'] = user.username
            session['id_tl'] = user.id
            session['turno'] = user.turno
            session['area'] = user.area
            session['role'] = user.role
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Credenciais inválidas'}), 401

    except Exception as e:
        print(e)
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@daily_sec.route('/tl_profile', methods=['GET'])
def tl_profile():
    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()
        tl_id = session.get('id_tl')

        query = "SELECT * FROM teamleaders WHERE id = ? and ativo = 1"
        cursor.execute(query, (tl_id,))
        row = cursor.fetchone()

        if row:
            tl = {
                "id": row.id,
                "username": row.username,
                "password": row.password,
                "email": row.email,
                "n_colaborador": row.n_colaborador,
                "turno": row.turno,
                "area": row.area,
                "card_number": row.card_number
            }
                   
            return render_template('daily/profile.html', maintenance="Perfil", tl=tl)
        else:
            return render_template('daily/profile.html', maintenance="Perfil", error="Team Leader não encontrado")
    except Exception as e:
        print(e)
        return render_template('daily/profile.html', maintenance="Perfil", error="Erro ao carregar o perfil")

@daily_sec.route('/update_profile_tl', methods=['POST'])
def update_profile_tl():
    try:
        tl_id = session.get('id_tl')

        passw = request.form.get('password')

        if not passw or len(passw) < 6:
            flash('A password deve ter pelo menos 6 caracteres.', category='error')
            return redirect(url_for('daily.tl_profile'))
        
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        query = """
            UPDATE teamleaders
            SET password = ?
            WHERE id = ?
        """
        cursor.execute(query, (passw, tl_id))
        conn.commit()
        flash('Perfil atualizado com sucesso!', category='success')

        return redirect(url_for('daily.tl_profile'))

    except Exception as e:
        print(e)
        return jsonify({"error": "Erro ao salvar alterações"}), 500

@daily_sec.route('/api/add_daily_record', methods=['POST'])
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
            OUTPUT INSERTED.id
            VALUES (?, GETDATE(), ?, ?, ?, ?)
        """, session['id_tl'], safety_comment, quality_comment, volume_comment, people_comment)
        daily_id = cursor.fetchone()[0]

        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'images')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        invalid_files = []
        uploaded_files = request.files.getlist("images")
        invalid_files = insert_files(cursor, daily_id, uploaded_files, upload_folder)

        conn.commit()
        
        if invalid_files and len(invalid_files) > 0:
            message = (f"Comentários adicionados! "
                       f"No entanto, os seguintes ficheiros têm tipos inválidos e não foram carregados: "
                       f"{', '.join(invalid_files)}")
            flash(message, category='warning')
            return jsonify({'status': 'warning', 'message': message})
        else:
            flash('Comentários e imagens adicionados com sucesso!', category='success')
            return jsonify({'status': 'success', 'message': 'Comentários e imagens adicionados com sucesso!'})


    except Exception as e:
        print(e)
        flash('Erro ao adicionar os comentários.', category='error')
        return jsonify({'status': 'error', 'message': 'Erro ao adicionar comentários!'}), 500
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@daily_sec.route('/api/edit_daily_record', methods=['POST'])
def edit_daily_record():
    if 'username' not in session:
        return jsonify({'status': 'error', 'message': 'Usuário não autenticado.'}), 403
    conn = pyodbc.connect(conexao_mms)
    cursor = conn.cursor()

    try:
        record_id = request.form.get('id')
        safety_comment = request.form.get('safety_comment')
        quality_comment = request.form.get('quality_comment')
        volume_comment = request.form.get('volume_comment')
        people_comment = request.form.get('people_comment')
        removed_images = json.loads(request.form.get('removed_images', '[]'))

        cursor.execute("""
            UPDATE daily
            SET safety_comment = ?, quality_comment = ?, volume_comment = ?, people_comment = ?
            WHERE id = ?
        """, (safety_comment, quality_comment, volume_comment, people_comment, record_id))

        if removed_images:
            cursor.executemany("""
                DELETE FROM daily_images WHERE id = ?
            """, [(image_id,) for image_id in removed_images])

        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'images')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        uploaded_files = request.files.getlist("images")
        
        invalid_files = insert_files(cursor, record_id, uploaded_files, upload_folder)

        conn.commit()
        
        if invalid_files and len(invalid_files) > 0:
            message = (f"Comentários atualizados! "
                       f"Mas os seguintes ficheiros têm tipos inválidos e não foram carregados: "
                       f"{', '.join(invalid_files)}")
            flash(message, category='warning')
            return jsonify({'status': 'warning', 'message': message}), 200
        else:
            return jsonify({'status': 'success', 'message': 'Comentários atualizados com sucesso.'}), 200

    except Exception as e:
        print(f"Erro ao atualizar comentário: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Ocorreu um erro ao atualizar o comentário.'}), 500

    finally:
        cursor.close()
        conn.close()

@daily_sec.route('/api/get_images/<int:daily_id>', methods=['GET'])
def get_images(daily_id):
    conn = pyodbc.connect(conexao_mms)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, image_path FROM daily_images WHERE id_daily = ?", daily_id)
        images = [{
            "id": row.id,
            "url": url_for('static', filename=row.image_path.replace("static/", ""))
        } for row in cursor.fetchall()]

        return jsonify({"status": "success", "images": images}), 200
    except Exception as e:
        print(f"Erro ao obter imagens: {str(e)}")
        return jsonify({"status": "error", "message": "Erro ao obter imagens."}), 500
    finally:
        cursor.close()
        conn.close()

@daily_sec.route('/api/delete_image/<int:image_id>', methods=['DELETE'])
def delete_image(image_id):
    if 'username' not in session:
        return jsonify({'status': 'error', 'message': 'Usuário não autenticado.'}), 403
    conn = pyodbc.connect(conexao_mms)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT image_path FROM daily_images WHERE id = ?", image_id)
        row = cursor.fetchone()
        if row:
            image_path = os.path.join(current_app.static_folder, row.image_path)
            if os.path.exists(image_path):
                os.remove(image_path)
            cursor.execute("DELETE FROM daily_images WHERE id = ?", image_id)
            conn.commit()
            return jsonify({"status": "success", "message": "Imagem removida com sucesso."}), 200
        else:
            return jsonify({"status": "error", "message": "Imagem não encontrada."}), 404
    except Exception as e:
        print(f"Erro ao deletar imagem: {str(e)}")
        return jsonify({"status": "error", "message": "Erro ao deletar imagem."}), 500
    finally:
        cursor.close()
        conn.close()
