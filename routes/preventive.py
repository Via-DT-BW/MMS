from flask import Blueprint, jsonify, request, session, redirect, url_for, flash, render_template
import pyodbc
from datetime import date, datetime
import pyodbc
from utils.call_conn import conexao_mms

preventive_sec = Blueprint("preventive", __name__, static_folder="static", static_url_path='/Main/static', template_folder="templates")

@preventive_sec.route('/preventive', methods=['GET'])
def preventive():
    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        filter_order = request.args.get('filter_order', '', type=str)
        filter_cost = request.args.get('filter_cost', '', type=str)
        start_date = request.args.get('start_date', '', type=str)
        end_date = request.args.get('end_date', '', type=str)

        preventive_page_size = request.args.get('preventive_page_size', 10, type=int)
        preventive_page = request.args.get('preventive_page', 1, type=int)

        orders_page_size = request.args.get('orders_page_size', 10, type=int)
        orders_page = request.args.get('orders_page', 1, type=int)

        filter_order = None if filter_order == "" else filter_order
        start_date = None if start_date == "" else start_date
        end_date = None if end_date == "" else end_date

        cursor.execute("""
            EXEC GetPreventiveRecords  
                @FilterOrder = ?,
                @FilterCost = ?,
                @StartDate = ?, 
                @EndDate = ?, 
                @PageSize = ?, 
                @Page = ?
        """, filter_order, filter_cost, start_date, end_date, preventive_page_size, preventive_page)

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
    return redirect(url_for('preventive.preventive'))

@preventive_sec.route('/start-preventive', methods=['POST'])
def start_preventive():
    try:
        data = request.get_json()
        order_number = data.get('order_number')
        id_mt = data.get('technician_id')
        print(order_number, id_mt)
        if not order_number:
            return jsonify({'error': 'Número da ordem é obrigatório!'}), 400

        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        cursor.execute("EXEC StartPreventiveOrder @OrderNumber = ?, @MT_id = ?", order_number, id_mt)
        conn.commit()

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
     