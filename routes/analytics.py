from flask import Blueprint, jsonify, request, flash, render_template
import pyodbc
from datetime import datetime
import pyodbc
from utils.call_conn import conexao_mms, conexao_capture

analytics_bp = Blueprint("analytics", __name__, static_folder="static", static_url_path='/Main/static', template_folder="templates")

@analytics_bp.route('/analytics')
def analytics():  
    filter_prod_line = request.args.get('filter_prod_line', '')
    start_date = request.args.get('start_date', type=str)
    end_date = request.args.get('end_date', type=str)
    page = request.args.get('page', 1, type=int)
    per_page = 20

    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()

        query = """
            SELECT 
                c.id, c.id_estado, c.prod_line, c.description, c.equipament, c.stopped_production,
                c.n_operador, c.functional_location, c.main_workcenter, c.data_pedido, c.data_inicio_man,
                c.data_fim_man, c.sap_order, c.sms_date, c.tempo_manutencao, c.idSMS, c.SMSState, c.sap_order_number,
                ct.id_tecnico, ct.id_tipo_avaria, ct.maintenance_comment, ct.data_inicio, ct.data_fim, ct.duracao,
                ta.tipo, ta.area
            FROM [dbo].[corretiva] c
            LEFT JOIN [dbo].[corretiva_tecnicos] ct ON c.id = ct.id_corretiva
            LEFT JOIN [dbo].[tipo_avaria] ta ON ct.id_tipo_avaria = ta.id
            WHERE 1=1
        """
        params = []

        if filter_prod_line:
            prod_lines = filter_prod_line.split(',')
            placeholders = ','.join('?' for _ in prod_lines)
            query += f" AND c.prod_line IN ({placeholders})"
            params.extend(prod_lines)

        if start_date:
            query += " AND c.data_pedido >= ?"
            params.append(start_date)

        if end_date:
            query += " AND c.data_pedido <= ?"
            params.append(end_date)

        query += " ORDER BY c.id desc OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        offset = (page - 1) * per_page
        params.extend([offset, per_page])

        cursor.execute(query, params)

        data = []
        columns = [column[0] for column in cursor.description]
        for row in cursor.fetchall():
            record = {}
            for idx, value in enumerate(row):
                if isinstance(value, datetime):
                    value = value.strftime("%Y-%m-%d %H:%M:%S")
                record[columns[idx]] = value
            data.append(record)

        count_query = """
            SELECT COUNT(*)
            FROM [dbo].[corretiva] c
            LEFT JOIN [dbo].[corretiva_tecnicos] ct ON c.id = ct.id_corretiva
            LEFT JOIN [dbo].[tipo_avaria] ta ON ct.id_tipo_avaria = ta.id
            WHERE 1=1
        """
        count_params = []

        if filter_prod_line:
            count_query += f" AND c.prod_line IN ({placeholders})"
            count_params.extend(prod_lines)

        if start_date:
            count_query += " AND c.data_pedido >= ?"
            count_params.append(start_date)

        if end_date:
            count_query += " AND c.data_pedido <= ?"
            count_params.append(end_date)

        cursor.execute(count_query, count_params)
        total_records = cursor.fetchone()[0]
        total_pages = (total_records + per_page - 1) // per_page
        
        return render_template('analytics/analytics.html', maintenance="Analytics", records=data, page=page, total_pages=total_pages, filter_prod_line=filter_prod_line, start_date=start_date, end_date=end_date)

    except Exception as e:
        print(e)
        flash(f'Ocorreu um erro: {str(e)}', category='error')
        return render_template('analytics/analytics.html', maintenance="Analytics", records=[], page=1, total_pages=1)

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
            
@analytics_bp.route('/analytics_per_line')
def analytics_per_line(): 
    filter_prod_line = request.args.get('filter_prod_line', '')
    filter_shift = request.args.get('filter_shift', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    return render_template('analytics/analytics_per_line.html', 
        maintenance="Analytics", 
        filter_prod_line=filter_prod_line,
        filter_shift=filter_shift,
        start_date=start_date,
        end_date=end_date
    )

@analytics_bp.route('/analytics_per_area')
def analytics_per_area(): 
    filter_area = request.args.get('filter_area', '')
    filter_shift = request.args.get('filter_shift', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    return render_template('analytics/analytics_per_area.html', 
        maintenance="Analytics", 
        filter_area=filter_area,
        filter_shift=filter_shift,
        start_date=start_date,
        end_date=end_date
    )

@analytics_bp.route("/api/total_time_fail_mode", methods=['GET'])
def total_time_fail_mode():
    filter_prod_line = request.args.get("filter_prod_line", "")
    
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    filter_shift = request.args.get("filter_shift", "Todos")

    if not filter_prod_line or not start_date or not end_date:
        return jsonify({"error": "Preencha todos os filtros"}), 400

    try:
        conn = pyodbc.connect(conexao_capture)
        cursor = conn.cursor()

        cursor.execute("EXEC MMS.dbo.GetTotalTimeFailMode ?, ?, ?, ?", filter_prod_line, start_date, end_date, filter_shift)
        rows = cursor.fetchall()

        data = {}
        for row in rows:
            equipament = row[1]
            fail_mode = row[0]
            n_incidents = row[2]
            total_minutes = row[3]

            if equipament not in data:
                data[equipament] = {"fail_modes": {}, "n_incidents": 0}

            data[equipament]["fail_modes"][fail_mode] = total_minutes
            data[equipament]["n_incidents"] += n_incidents

        formatted_data = [
            {"equipament": equipament, "fail_modes": fail_modes["fail_modes"], "n_incidents": fail_modes["n_incidents"]}
            for equipament, fail_modes in data.items()
        ]

        return jsonify(formatted_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        
@analytics_bp.route("/api/total_time_tipologia", methods=['GET'])
def get_total_time_tipologia():
    filter_prod_line = request.args.get("filter_prod_line", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    filter_shift = request.args.get("filter_shift", "")

    if not filter_prod_line or not start_date or not end_date:
         return jsonify({"error": "Preencha todos os filtros"}), 400

    try:
        conn = pyodbc.connect(conexao_capture)
        cursor = conn.cursor()
        cursor.execute("EXEC MMS.dbo.GetTotalTimeByTipologia ?, ?, ?, ?", filter_prod_line, start_date, end_date, filter_shift)
        rows = cursor.fetchall()
        data = {}
        for row in rows:
            tipologia = row[0]
            equipament = row[1]
            n_incidents = row[2]
            total_minutes = row[3]

            if tipologia not in data:
                data[tipologia] = {"equipaments": {}, "n_incidents": 0}

            data[tipologia]["equipaments"][equipament] = total_minutes
            data[tipologia]["n_incidents"] += n_incidents

        formatted_data = [
            {"tipologia": tipologia, "equipaments": tipology_data["equipaments"], "n_incidents": tipology_data["n_incidents"]}
            for tipologia, tipology_data in data.items()
        ]

        return jsonify(formatted_data)

    except Exception as e:
         return jsonify({"error": str(e)}), 500
    finally:
         if 'cursor' in locals():
              cursor.close()
         if 'conn' in locals():
              conn.close()
              
@analytics_bp.route("/api/get_intervention_stats", methods=['GET'])
def get_intervention_stats():
    filter_prod_line = request.args.get("filter_prod_line", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    filter_shift = request.args.get("filter_shift", "")
    stopped_prod = request.args.get("stopped_prod", "")

    if not filter_prod_line or not start_date or not end_date:
        return jsonify({"error": "Preencha todos os filtros"}), 400

    try:
        conn = pyodbc.connect(conexao_capture)
        cursor = conn.cursor()
        cursor.execute("""
            EXEC MMS.dbo.GetInterventionStats ?, ?, ?, ?, ?
        """, filter_prod_line, start_date, end_date, filter_shift, stopped_prod)
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            result.append({
                "downtime": row.total_downtime,
                "technician_time": row.total_technician_time
            })
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@analytics_bp.route('/api/get_equipment_stats', methods=['GET'])
def get_equipment_stats():
    try:
        filter_prod_line = request.args.get('filter_prod_line', '')
        start_date = request.args.get('start_date', "")
        end_date = request.args.get('end_date', "")
        filter_shift = request.args.get('filter_shift', '')

        conn = pyodbc.connect(conexao_capture)
        cursor = conn.cursor()

        cursor.execute("EXEC MMS.dbo.GetTotalTimeByEquipment ?, ?, ?, ?", filter_prod_line, start_date, end_date, filter_shift)
        data = cursor.fetchall()

        result = []
        for row in data:
            result.append({
                'equipament': row.equipament,
                'total_incidents': row.total_incidents,
                'total_minutes': row.total_minutes
            })

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@analytics_bp.route("/api/get_weekly_maintenance_evolution", methods=['GET'])
def get_weekly_maintenance_evolution():
    filter_prod_line = request.args.get("filter_prod_line", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    filter_shift = request.args.get("filter_shift", "")

    if not filter_prod_line or not start_date or not end_date:
        return jsonify({"error": "Preencha todos os filtros"}), 400

    try:
        conn = pyodbc.connect(conexao_capture)
        cursor = conn.cursor()

        cursor.execute("EXEC MMS.dbo.GetWeeklyMaintenanceEvolution ?, ?, ?, ?", filter_prod_line, start_date, end_date, filter_shift)
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            result.append({
                "week_start": row.week_start.strftime("%Y-%m-%d"),
                "total_minutes": row.total_minutes,
                "total_incidents": row.total_incidents,
                "tipo": row.tipo
            })

        return jsonify(result)

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@analytics_bp.route("/api/get_weekly_maintenance_evolution_fail_mode", methods=['GET'])
def get_weekly_maintenance_evolution_fail_mode():
    filter_prod_line = request.args.get("filter_prod_line", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    filter_shift = request.args.get("filter_shift", "")

    if not filter_prod_line or not start_date or not end_date:
        return jsonify({"error": "Preencha todos os filtros"}), 400

    try:
        conn = pyodbc.connect(conexao_capture)
        cursor = conn.cursor()

        cursor.execute("EXEC MMS.dbo.GetWeeklyMaintenanceEvolutionFailMode ?, ?, ?, ?", filter_prod_line, start_date, end_date, filter_shift)
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            result.append({
                "week_start": row.week_start.strftime("%Y-%m-%d"),
                "total_minutes": row.total_minutes,
                "total_incidents": row.total_incidents,
                "description": row.description
            })

        return jsonify(result)

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@analytics_bp.route('/api/get_average_response_time_stats', methods=['GET'])
def get_average_response_time_stats():
    try:
        filter_line = request.args.get('filter_prod_line', '')
        start_date = request.args.get("start_date", None)
        end_date = request.args.get("end_date", None)
        filter_shift = request.args.get('filter_shift', '')

        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

        conn = pyodbc.connect(conexao_capture)
        cursor = conn.cursor()

        query = "EXEC MMS.dbo.GetAverageResponseTimeByProdLine ?, ?, ?, ?"
        params = (filter_line, start_date, end_date, filter_shift)
        cursor.execute(query, params)

        data = []
        for row in cursor.fetchall():
            data.append({
                'prod_line': row.prod_line,
                'avg_response_time': row.avg_response_time
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

@analytics_bp.route('/api/get_average_resolution_time_stats', methods=['GET'])
def get_average_resolution_time_stats():
    try:
        filter_line = request.args.get('filter_prod_line', '')
        start_date = request.args.get("start_date", None)
        end_date = request.args.get("end_date", None)
        filter_shift = request.args.get('filter_shift', '')

        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

        conn = pyodbc.connect(conexao_capture)
        cursor = conn.cursor()

        query = "exec MMS.dbo.GetAverageResolutionTimeByProdLine ?, ?, ?, ?"
        params = (filter_line, start_date, end_date, filter_shift)
        cursor.execute(query, params)

        data = []
        for row in cursor.fetchall():
            data.append({
                'prod_line': row.prod_line,
                'avg_resolution_time': row.avg_resolution_time
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

@analytics_bp.route('/api/get_average_stopped_machine_time', methods=['GET'])
def get_average_stopped_machine_time():
    try:
        filter_line = request.args.get('filter_prod_line', '')
        start_date = request.args.get("start_date", None)
        end_date = request.args.get("end_date", None)
        filter_shift = request.args.get('filter_shift', '')

        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

        conn = pyodbc.connect(conexao_capture)
        cursor = conn.cursor()

        query = "EXEC MMS.dbo.GetAverageStoppedMachineTime ?, ?, ?, ?"
        params = (filter_line, start_date, end_date, filter_shift)
        cursor.execute(query, params)
        
        data = []
        for row in cursor.fetchall():
            data.append({
                'prod_line': row.prod_line,
                'avg_stopped_time': row.avg_stopped_time
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

@analytics_bp.route("/api/get_technician_interventions", methods=['GET'])
def get_technician_interventions():
    filter_prod_line = request.args.get("filter_prod_line", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    filter_shift = request.args.get("filter_shift", "")

    try:
        conn = pyodbc.connect(conexao_capture)
        cursor = conn.cursor()
        cursor.execute("EXEC MMS.dbo.GetTechnicianInterventions ?, ?, ?, ?", filter_prod_line, start_date, end_date, filter_shift)
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            result.append({
                "technician_name": row.technician_name,
                "total_interventions": row.total_interventions,
                "avg_resolution_time": row.avg_resolution_time
            })
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@analytics_bp.route("/api/get_scatter_data", methods=['GET'])
def get_scatter_data():
    filter_prod_line = request.args.get("filter_prod_line", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    filter_shift = request.args.get("filter_shift", "")

    if not filter_prod_line or not start_date or not end_date:
        return jsonify({"error": "Preencha todos os filtros"}), 400

    try:
        conn = pyodbc.connect(conexao_capture)
        cursor = conn.cursor()
        
        cursor.execute(
            "EXEC MMS.dbo.GetScatterData ?, ?, ?, ?",
            filter_prod_line, start_date, end_date, filter_shift
        )
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            result.append({
                "responseTime": row.responseTime,
                "resolutionTime": row.resolutionTime
            })
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@analytics_bp.route("/api/get_mtbf_by_equipment", methods=["GET"])
def get_mtbf_by_equipment():
    filter_prod_line = request.args.get("filter_prod_line", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    filter_shift = request.args.get("filter_shift", "")

    if not filter_prod_line or not start_date or not end_date:
        return jsonify({"error": "Preencha todos os filtros"}), 400

    try:
        conn = pyodbc.connect(conexao_capture)
        cursor = conn.cursor()
        cursor.execute("EXEC MMS.dbo.GetMTBFByEquipment ?, ?, ?, ?", filter_prod_line, start_date, end_date, filter_shift)
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            result.append({
                "equipment": row.equipament,
                "mtbf": row.MTBF_in_minutes
            })
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@analytics_bp.route("/api/get_mtbf_by_equipment_per_area", methods=["GET"])
def get_mtbf_by_equipment_per_area():
    filter_area = request.args.get("filter_area", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    filter_shift = request.args.get("filter_shift", "")

    if not filter_area or not start_date or not end_date:
        return jsonify({"error": "Preencha todos os filtros"}), 400

    try:
        conn = pyodbc.connect(conexao_capture)
        cursor = conn.cursor()
        cursor.execute("EXEC MMS.dbo.GetMTBFByEquipmentByArea ?, ?, ?, ?", filter_area, start_date, end_date, filter_shift)
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            result.append({
                "equipment": row.equipament,
                "mtbf": row.MTBF_in_minutes,
                "prod_line": row.prod_line
            })
            
        return jsonify(result)
    
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@analytics_bp.route('/api/get_average_response_time_stats_per_area', methods=['GET'])
def get_average_response_time_stats_per_area():
    try:
        filter_area = request.args.get("filter_area", "")
        start_date = request.args.get("start_date", None)
        end_date = request.args.get("end_date", None)
        filter_shift = request.args.get('filter_shift', '')

        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

        conn = pyodbc.connect(conexao_capture)
        cursor = conn.cursor()
        query = "EXEC MMS.dbo.GetAverageResponseTimePerArea ?, ?, ?, ?"
        params = (filter_area, start_date, end_date, filter_shift)
        cursor.execute(query, params)

        data = []
        for row in cursor.fetchall():
            data.append({
                'prod_line': row.prod_line,
                'avg_response_time': row.avg_response_time
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

@analytics_bp.route('/api/get_average_stopped_machine_time_per_area', methods=['GET'])
def get_average_stopped_machine_time_per_area():
    try:
        filter_area = request.args.get("filter_area", "")
        start_date = request.args.get("start_date", None)
        end_date = request.args.get("end_date", None)
        filter_shift = request.args.get('filter_shift', '')

        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

        conn = pyodbc.connect(conexao_capture)
        cursor = conn.cursor()

        query = "EXEC MMS.dbo.GetAverageStoppedMachineTimePerArea ?, ?, ?, ?"
        params = (filter_area, start_date, end_date, filter_shift)
        cursor.execute(query, params)
        
        data = []
        for row in cursor.fetchall():
            data.append({
                'prod_line': row.prod_line,
                'avg_stopped_time': row.avg_stopped_time
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

@analytics_bp.route('/api/get_average_resolution_time_stats_per_area', methods=['GET'])
def get_average_resolution_time_stats_per_area():
    try:
        filter_area = request.args.get("filter_area", "")
        start_date = request.args.get("start_date", None)
        end_date = request.args.get("end_date", None)
        filter_shift = request.args.get('filter_shift', '')

        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

        conn = pyodbc.connect(conexao_capture)
        cursor = conn.cursor()

        query = "exec MMS.dbo.GetAverageResolutionTimePerArea ?, ?, ?, ?"
        params = (filter_area, start_date, end_date, filter_shift)
        cursor.execute(query, params)

        data = []
        for row in cursor.fetchall():
            data.append({
                'prod_line': row.prod_line,
                'avg_resolution_time': row.avg_resolution_time
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

@analytics_bp.route("/api/total_time_tipologia_per_area", methods=['GET'])
def get_total_time_tipologia_per_area():
    filter_area = request.args.get("filter_area", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    filter_shift = request.args.get("filter_shift", "")

    if not filter_area or not start_date or not end_date:
         return jsonify({"error": "Preencha todos os filtros"}), 400

    try:
         conn = pyodbc.connect(conexao_capture)
         cursor = conn.cursor()
         cursor.execute("EXEC MMS.dbo.GetTotalTimeByTipologiaPerArea ?, ?, ?, ?", filter_area, start_date, end_date, filter_shift)
         rows = cursor.fetchall()
         data = [{"tipologia": row[0], "total_incidents": row[1], "total_minutes": row[2], "prod_line": row[3]} for row in rows]
         
         return jsonify(data)
    except Exception as e:
         return jsonify({"error": str(e)}), 500
    finally:
         if 'cursor' in locals():
              cursor.close()
         if 'conn' in locals():
              conn.close()
 
@analytics_bp.route("/api/total_time_fail_mode_per_area", methods=['GET'])
def total_time_fail_mode_per_area():
    
    filter_area = request.args.get("filter_area", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    filter_shift = request.args.get("filter_shift", "Todos")

    if not filter_area or not start_date or not end_date:
        return jsonify({"error": "Preencha todos os filtros"}), 400

    try:
        conn = pyodbc.connect(conexao_capture)
        cursor = conn.cursor()

        cursor.execute("EXEC MMS.dbo.GetTotalTimeFailModePerArea ?, ?, ?, ?", filter_area, start_date, end_date, filter_shift)
        rows = cursor.fetchall()

        data = [{"description": row[0],'total_incidents': row[1] ,"total_minutes": row[2], "prod_line": row[3]} for row in rows]
        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        
@analytics_bp.route("/api/get_intervention_stats_per_area", methods=['GET'])
def get_intervention_stats_per_area():
    filter_area = request.args.get("filter_area", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    filter_shift = request.args.get("filter_shift", "")
    stopped_prod = request.args.get("stopped_prod", "")

    if not filter_area or not start_date or not end_date:
        return jsonify({"error": "Preencha todos os filtros"}), 400

    try:
        conn = pyodbc.connect(conexao_capture)
        cursor = conn.cursor()
        cursor.execute("""
            EXEC MMS.dbo.GetInterventionStatsPerArea ?, ?, ?, ?, ?
        """, filter_area, start_date, end_date, filter_shift, stopped_prod)
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            result.append({
                "prod_line": row.prod_line,
                "downtime": row.total_downtime,
                "technician_time": row.total_technician_time
            })
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@analytics_bp.route('/api/get_equipment_stats_per_area', methods=['GET'])
def get_equipment_stats_per_area():
    try:
        filter_area = request.args.get('filter_area', '')
        start_date = request.args.get('start_date', "")
        end_date = request.args.get('end_date', "")
        filter_shift = request.args.get('filter_shift', '')

        conn = pyodbc.connect(conexao_capture)
        cursor = conn.cursor()

        cursor.execute("EXEC MMS.dbo.GetTotalTimeByEquipmentPerArea ?, ?, ?, ?", 
                       filter_area, start_date, end_date, filter_shift)
        data = cursor.fetchall()

        result = []
        for row in data:
            result.append({
                'prod_line': row.prod_line,
                'equipament': row.equipament,
                'total_incidents': row.total_incidents,
                'total_minutes': row.total_minutes
            })

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@analytics_bp.route("/api/get_weekly_maintenance_evolution_per_area", methods=['GET'])
def get_weekly_maintenance_evolution_per_area():
    filter_area = request.args.get("filter_area", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    filter_shift = request.args.get("filter_shift", "")

    if not filter_area or not start_date or not end_date:
        return jsonify({"error": "Preencha todos os filtros"}), 400

    try:
        conn = pyodbc.connect(conexao_capture)
        cursor = conn.cursor()

        cursor.execute("EXEC MMS.dbo.GetWeeklyMaintenanceEvolutionPerArea ?, ?, ?, ?", filter_area, start_date, end_date, filter_shift)
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            result.append({
                "week_start": row.week_start.strftime("%Y-%m-%d"),
                "total_minutes": row.total_minutes,
                "total_incidents": row.total_incidents,
                "prod_line": row.prod_line
            })

        return jsonify(result)

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@analytics_bp.route("/api/get_technician_interventions_per_area", methods=['GET'])
def get_technician_interventions_per_area():
    filter_area = request.args.get("filter_area", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    filter_shift = request.args.get("filter_shift", "")

    try:
        conn = pyodbc.connect(conexao_capture)
        cursor = conn.cursor()
        cursor.execute("EXEC MMS.dbo.GetTechnicianInterventionsPerArea ?, ?, ?, ?", filter_area, start_date, end_date, filter_shift)
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            result.append({
                "technician_name": row.technician_name,
                "total_interventions": row.total_interventions,
                "avg_resolution_time": row.avg_resolution_time,
                "prod_line": row.prod_line
            })
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@analytics_bp.route("/api/get_scatter_data_per_area", methods=['GET'])
def get_scatter_data_per_area():
    filter_area = request.args.get("filter_area", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    filter_shift = request.args.get("filter_shift", "")

    if not filter_area or not start_date or not end_date:
        return jsonify({"error": "Preencha todos os filtros"}), 400

    try:
        conn = pyodbc.connect(conexao_capture)
        cursor = conn.cursor()
        
        cursor.execute(
            "EXEC MMS.dbo.GetScatterDataPerArea ?, ?, ?, ?",
            filter_area, start_date, end_date, filter_shift
        )
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            result.append({
                "responseTime": row.responseTime,
                "resolutionTime": row.resolutionTime,
                "prod_line": row.prod_line
            })
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
