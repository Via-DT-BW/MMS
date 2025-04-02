import io
from flask import Blueprint, Response, jsonify, request, session, redirect, url_for, flash, render_template
import pyodbc
from datetime import date, datetime
import pyodbc
from utils.call_conn import conexao_mms
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

preventive_sec = Blueprint("preventive", __name__, static_folder="static", static_url_path='/Main/static', template_folder="templates")

@preventive_sec.route('/preventive', methods=['GET'])
def preventive():
    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        filter_order = request.args.get('filter_order', '', type=str)
        filter_cost = request.args.get('filter_cost', '', type=str)
        filter_status = request.args.get('filter_status', '', type=str)
        start_date = request.args.get('start_date', '', type=str)
        end_date = request.args.get('end_date', '', type=str)
        start_date = str(start_date)
        end_date = str(end_date)

        preventive_page_size = request.args.get('preventive_page_size', 10, type=int)
        preventive_page = request.args.get('preventive_page', 1, type=int)

        orders_page_size = request.args.get('orders_page_size', 10, type=int)
        orders_page = request.args.get('orders_page', 1, type=int)

        filter_order = None if filter_order == "" else filter_order
        filter_status = None if filter_status == "" else filter_status
        start_date = None if start_date == "" else start_date
        end_date = None if end_date == "" else end_date

        cursor.execute("""
            EXEC GetPreventiveRecords  
                @FilterOrder = ?,
                @FilterCost = ?,
                @FilterStatus = ?,
                @StartDate = ?, 
                @EndDate = ?, 
                @PageSize = ?, 
                @Page = ?
        """, filter_order, filter_cost, filter_status,start_date, end_date, preventive_page_size, preventive_page)


        preventive_total = cursor.fetchone()[0]
        cursor.nextset()
        preventive_data = cursor.fetchall()

        cursor.execute("""
            EXEC GetPreventiveOrders 
                @FilterOrder = ?,
                @FilterCost = ?,
                @StartDate = ?, 
                @EndDate = ?, 
                @PageSize = ?,
                @Page = ?
        """, filter_order, filter_cost, start_date, end_date, orders_page_size, orders_page)

        orders_total = cursor.fetchone()[0]
        cursor.nextset()
        finished_orders_data = cursor.fetchall()

        return render_template(
            'preventive/notifications.html',
            maintenance="Manutenção Preventiva",
            preventive=preventive_data,
            preventive_total=preventive_total,
            preventive_page_size=preventive_page_size,
            preventive_current_page=preventive_page,
            finished_orders_data=finished_orders_data,
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
    return redirect(url_for('preventive.preventive'))

@preventive_sec.route('/start-preventive', methods=['POST'])
def start_preventive():
    try:
        data = request.get_json()
        order_number = data.get('order_number')
        id_mt = data.get('technician_id')

        if not order_number:
            return jsonify({'error': 'Número da ordem é obrigatório!'}), 400
        
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM preventive_orders 
            WHERE id_tecnico = ? AND id_estado = 2
        """, id_mt)
        existing_preventives = cursor.fetchone()[0]

        if existing_preventives > 0:
            flash('Já está a executar uma preventiva e não pode iniciar outra.', category='error')
            return jsonify({'error': 'Já está a executar uma preventiva e não pode iniciar outra.'}), 400
        
        cursor.execute("EXEC StartPreventiveOrder @OrderNumber = ?, @MT_id = ?", order_number, id_mt)
        conn.commit()
        flash('Preventiva iniciada com sucesso!', category='success')
        return jsonify({'message': 'Preventiva iniciada com sucesso!'}), 200

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@preventive_sec.route('/end-preventive', methods=['POST'])
def end_preventive():
    try:
        data = request.get_json()
        id = data.get('id')
        comment = data.get('comentario')

        if not id:
            return jsonify({'error': 'Número da ordem é obrigatório!'}), 400

        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("UPDATE preventive_orders SET id_estado = 3, data_fim = GETDATE(), comment= ? WHERE id = ?", (comment, id))
        conn.commit()
        flash('Preventiva finalizada com sucesso!', category='success')
        return jsonify({'message': 'Preventiva finalizada com sucesso!'}), 200

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@preventive_sec.route('/pause_intervention/<order_id>', methods=['POST'])
def pause_intervention(order_id):

    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("UPDATE preventive_orders SET id_estado = 5 WHERE id = ?", order_id)

        cursor.execute("INSERT INTO preventive_pauses (order_id, start_pause) VALUES (?, GETDATE())", order_id)

        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Intervenção interrompida com sucesso!'}), 200
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

@preventive_sec.route('/resume_intervention/<order_id>', methods=['POST'])
def resume_intervention(order_id):
    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("UPDATE preventive_orders SET id_estado = 2 WHERE id = ?", order_id)

        cursor.execute("""
            UPDATE preventive_pauses 
            SET end_pause = GETDATE() 
            WHERE order_id = ? AND end_pause IS NULL
        """, order_id)

        cursor.execute("""
            SELECT SUM(DATEDIFF(MINUTE, start_pause, end_pause))
            FROM preventive_pauses
            WHERE order_id = ?
        """, order_id)
        total_pausa = cursor.fetchone()[0] or 0

        cursor.execute("""
            UPDATE preventive_orders 
            SET tempo_pausa_min = ?
            WHERE id = ?
        """, total_pausa, order_id)

        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Intervenção retomada com sucesso!'}), 200
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

@preventive_sec.route('/finished_preventives', methods=['GET'])
def finished_preventives():
    filter_finished_order = request.args.get('filter_finished_order', '', type=str)
    filter_finished_cost = request.args.get('filter_finished_cost', '', type=str)
    start_finished_date = request.args.get('start_finished_date', '', type=str)
    end_finished_date = request.args.get('end_finished_date', '', type=str)
    
    start_finished_date = None if not start_finished_date else start_finished_date
    end_finished_date = None if not end_finished_date else end_finished_date
    
    preventive_page_size = request.args.get('preventive_page_size', 10, type=int)
    preventive_page = request.args.get('preventive_page', 1, type=int)

    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("""
            EXEC GetFinishedPreventiveOrders  
                @FilterOrder = ?,
                @FilterCost = ?,
                @StartDate = ?, 
                @EndDate = ?, 
                @PageSize = ?, 
                @Page = ?
        """, filter_finished_order, filter_finished_cost, start_finished_date, end_finished_date, preventive_page_size, preventive_page)
        
        preventive_total = cursor.fetchone()[0]
        
        cursor.nextset()
        preventive_data = cursor.fetchall()
        cursor.close()
        conn.close()

        return render_template(
            'preventive/finished.html',
            maintenance="Manutenção Preventiva",
            finished_orders_data=preventive_data,
            preventive_total=preventive_total,
            preventive_page_size=preventive_page_size,
            preventive_current_page=preventive_page,
        )
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

@preventive_sec.route('/mapa_por_equipamento', methods=['GET'])
def mapa_por_equipamento():
    line_filter = request.args.get('linha', '', type=str)

    if not line_filter:
        return render_template(
            'preventive/mapa_por_equip.html',
            equipamentos=[]
        )
    
    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        query = """
            SELECT 
            e.equipment,
            p.id AS periocity_id,
            p.periocity,
            p.n_dias,
            CASE 
                WHEN MAX(hg.data_execucao) IS NULL THEN 9999
                ELSE DATEDIFF(DAY, MAX(hg.data_execucao), GETDATE())
            END AS dias_desde_execucao,
            CASE 
                WHEN (CASE WHEN MAX(hg.data_execucao) IS NULL THEN 9999 ELSE DATEDIFF(DAY, MAX(hg.data_execucao), GETDATE()) END) >= p.n_dias 
                THEN 1
                ELSE 0
            END AS overdue
            FROM equipments e
            JOIN equipment_gama eg ON e.id = eg.id_equipment
            JOIN periocity p ON eg.id_periocity = p.id
            LEFT JOIN history_gama hg ON eg.id = hg.id_equipment_gama
            WHERE e.cost_center LIKE '%' + ? + '%'
            GROUP BY e.equipment, p.id, p.periocity, p.n_dias
            ORDER BY e.equipment, p.id;
        """
        cursor.execute(query, line_filter)
        rows = cursor.fetchall()

        equipamentos = {}
        for row in rows:
            equip_name = row[0]
            periocity_id = row[1]
            periocity_name = row[2]
            n_dias = row[3]
            dias_desde_execucao = row[4]
            overdue = bool(row[5])
            if equip_name not in equipamentos:
                equipamentos[equip_name] = {
                    "equipament": equip_name,
                    "semanal": None,
                    "mensal": None,
                    "trimestral": None,
                    "semestral": None,
                    "anual": None
                }

            key = periocity_name.lower()
            equipamentos[equip_name][key] = {
                "n_dias": n_dias,
                "dias_desde_execucao": dias_desde_execucao,
                "overdue": overdue
            }

        cursor.close()
        conn.close()
        equipamentos_list = list(equipamentos.values())
        return render_template(
            'preventive/mapa_por_equip.html',
            equipamentos=equipamentos_list
        )
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

@preventive_sec.route('/mapa_por_linha', methods=['GET'])
def mapa_por_linha():
    line_filter = request.args.get('linha', '', type=str)
    
    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        query = """
            WITH UltimaExecucao AS (
                SELECT 
                    hg.id_equipment_gama,
                    MAX(hg.data_execucao) AS ultima_data_execucao
                FROM history_gama hg
                GROUP BY hg.id_equipment_gama
            )

            SELECT 
                e.cost_center AS linha,
                p.id AS periocity_id,
                p.periocity,
                p.n_dias,
                ue.ultima_data_execucao,
                CASE 
                    WHEN ue.ultima_data_execucao IS NULL THEN -1
                    ELSE DATEDIFF(DAY, ue.ultima_data_execucao, GETDATE())
                END AS dias_desde_execucao,
                CASE 
                    WHEN ue.ultima_data_execucao IS NULL THEN 1
                    WHEN DATEDIFF(DAY, ue.ultima_data_execucao, GETDATE()) >= p.n_dias THEN 1
                    ELSE 0
                END AS overdue
            FROM equipments e
            JOIN equipment_gama eg ON e.id = eg.id_equipment
            JOIN periocity p ON eg.id_periocity = p.id
            LEFT JOIN UltimaExecucao ue ON eg.id = ue.id_equipment_gama
            WHERE e.cost_center LIKE '%' + ? + '%'
            ORDER BY e.cost_center, p.id;
        """
        
        cursor.execute(query, line_filter)
        rows = cursor.fetchall()

        linhas = {}
        for row in rows:
            linha = row[0]
            periocity_id = row[1]
            periocity_name = row[2]
            n_dias = row[3]
            ultima_data_execucao = row[4]
            dias_desde_execucao = row[5]
            overdue = bool(row[6])
            
            if linha not in linhas:
                linhas[linha] = {
                    "linha": linha,
                    "semanal": None,
                    "mensal": None,
                    "trimestral": None,
                    "semestral": None,
                    "anual": None
                }
            key = periocity_name.lower()
            linhas[linha][key] = {
                "n_dias": n_dias,
                "dias_desde_execucao": dias_desde_execucao,
                "overdue": overdue
            }
        
        cursor.close()
        conn.close()
        
        linhas_list = list(linhas.values())
        return render_template(
            'preventive/mapa_por_linha.html',
            linhas=linhas_list
        )
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

@preventive_sec.route('/get_gama', methods=['POST'])
def get_gama():
    data = request.get_json()
    equipament = data.get('equipament')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        query = """
            SELECT 
                CONVERT(VARCHAR(10), h.data_execucao, 103) as data_execucao, 
                g.[desc] as gama_desc,
                g.id
            FROM equipments e
            JOIN equipment_gama eg ON e.id = eg.id_equipment
            JOIN history_gama h ON eg.id = h.id_equipment_gama
            JOIN gama g ON eg.id_gama = g.id
            WHERE e.equipment = ? 
              AND h.data_execucao BETWEEN ? AND ?
            ORDER BY h.data_execucao
        """
        cursor.execute(query, equipament, start_date, end_date)
        tasks = []
        for row in cursor.fetchall():
            tasks.append({
                'data_execucao': row.data_execucao,
                'gama_id': row.id,
                'gama_desc': row.gama_desc
            })
        return jsonify({'tasks': tasks})
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@preventive_sec.route('/tasks_history', methods=['GET'])
def tasks_history():
    filter_cost = request.args.get('filter_history_cost', '', type=str)
    start_date = request.args.get('start_history_date', '', type=str)
    end_date = request.args.get('end_history_date', '', type=str)
    
    start_date = None if not start_date else start_date
    end_date = None if not end_date else end_date
    
    preventive_page_size = request.args.get('preventive_page_size', 10, type=int)
    preventive_page = request.args.get('preventive_page', 1, type=int)

    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        if filter_cost:
            count_query = """
                SELECT COUNT(*) AS TotalRecords
                FROM equipments e
                JOIN equipment_gama eg ON e.id = eg.id_equipment
                JOIN history_gama h ON eg.id = h.id_equipment_gama
                JOIN gama g ON eg.id_gama = g.id
                WHERE e.cost_center LIKE '%' + ? + '%'
                  AND (? IS NULL OR h.data_execucao >= ?)
                  AND (? IS NULL OR h.data_execucao <= ?)
            """
            cursor.execute(count_query, filter_cost, start_date, start_date, end_date, end_date)
            preventive_total = cursor.fetchone()[0]
            
            offset = (preventive_page - 1) * preventive_page_size
            
            data_query = """
                SELECT 
                    e.equipment,
                    e.cost_center,
                    e.[desc] as equipment_desc,
                    CONVERT(VARCHAR(10), h.data_execucao, 103) as data_execucao,
                    g.[desc] as gama_desc,
                    g.id as gama_id
                FROM equipments e
                JOIN equipment_gama eg ON e.id = eg.id_equipment
                JOIN history_gama h ON eg.id = h.id_equipment_gama
                JOIN gama g ON eg.id_gama = g.id
                WHERE e.cost_center LIKE '%' + ? + '%'
                  AND (? IS NULL OR h.data_execucao >= ?)
                  AND (? IS NULL OR h.data_execucao <= ?)
                ORDER BY h.data_execucao DESC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY;
            """
            cursor.execute(data_query, filter_cost, start_date, start_date, end_date, end_date, offset, preventive_page_size)
            tasks_data = cursor.fetchall()
            cursor.close()
            conn.close()
            
            print(tasks_data)

            return render_template(
                'preventive/tasks_history.html',
                maintenance="Manutenção Preventiva",
                tasks_data=tasks_data,
                preventive_total=preventive_total,
                preventive_page_size=preventive_page_size,
                preventive_current_page=preventive_page,
                filter_history_cost=filter_cost,
                start_history_date=start_date if start_date else '',
                end_history_date=end_date if end_date else ''
            )
        else:
            return render_template(
                'preventive/tasks_history.html',
                maintenance="Manutenção Preventiva"
            )
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

@preventive_sec.route('/tasks_for_gama/<int:gama_id>')
def tasks_for_gama(gama_id):
    conn = pyodbc.connect(conexao_mms)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT t.id, t.descricao
        FROM tarefas t
        INNER JOIN tarefas_gama tg ON t.id = tg.tarefa_id
        WHERE tg.gama_id = ?
    """, (gama_id,))
    
    tarefas = [{"id": row[0], "descricao": row[1]} for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    return jsonify(tarefas)

@preventive_sec.route('/view_tarefas/<int:gama_id>')
def view_tarefas(gama_id):
    
    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT t.id, t.descricao, g.[desc]
            FROM tarefas t
            INNER JOIN tarefas_gama tg ON t.id = tg.tarefa_id
            INNER JOIN gama g ON tg.gama_id = g.id
            WHERE tg.gama_id = ?
        """, (gama_id,))

        tarefas = cursor.fetchall()

        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)

        if tarefas:
            titulo = f"Lista de Tarefas - {tarefas[0][2]}"
            pdf.setTitle(titulo)
        else:
            titulo = "Nenhuma tarefa encontrada nesta Lista de Tarefas."
            pdf.setTitle(titulo)

        pdf.drawString(100, 800, titulo)
        pdf.line(100, 790, 500, 790)
        
        if tarefas:
            let_y = 770
            for tarefa in tarefas:
                pdf.drawString(100, let_y, f"{tarefa[0]} - {tarefa[1]}")
                let_y -= 20
        else:
            pdf.drawString(100, 770, "Nenhuma tarefa disponível.")

        pdf.showPage()
        pdf.save()
        buffer.seek(0)

        return Response(buffer, mimetype="application/pdf",
                        headers={"Content-Disposition": f"inline; filename=tarefas_gama_{gama_id}.pdf"})
    
    except Exception as e:
        print(e)
        flash(f'Ocorreu um erro: {str(e)}', category='error')
        return redirect(url_for('preventive.preventive'))
    
    finally:
        cursor.close()
        conn.close()
