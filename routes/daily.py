from flask import Blueprint, jsonify, request, session, redirect, url_for, flash, render_template
import pyodbc
from datetime import datetime, timedelta
import pyodbc
from utils.call_conn import conexao_mms

daily_sec = Blueprint("daily", __name__, static_folder="static", static_url_path='/Main/static', template_folder="templates")

def empty_to_none(value):
    return None if value == "" else value

def get_effective_date(shift, now):
    if shift == 'C':
        if now.hour < 8:
            return (now - timedelta(days=1)).date()
        else:
            return now.date()
    else:
        return now.date()

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
        effective_date = get_effective_date(turno, now)
        
        cursor.execute("""
            SELECT id
            FROM daily
            WHERE id_tl = ? AND CONVERT(date, data) = ?
        """, id_tl, effective_date)
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
