import os
import pyodbc
import logging
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from utils.call_conn import conexao_mms

UPLOAD_FOLDER = "static/uploads/images"

def delete_old_photos():
    try:
        conn = pyodbc.connect(conexao_mms)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=30)

        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE='BASE TABLE' AND TABLE_NAME LIKE '%\_images' ESCAPE '\'
        """)
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            logging.info(f"Processando a tabela: {table_name}")

            query = f"""
                SELECT image_path 
                FROM {table_name} 
                WHERE upload_data < ?
            """
            cursor.execute(query, (cutoff_date,))
            rows = cursor.fetchall()
            
            for row in rows:
                image_path = row[0]
                filename = secure_filename(image_path)
                full_path = os.path.join(UPLOAD_FOLDER, filename)
                
                if os.path.exists(full_path):
                    try:
                        os.remove(full_path)
                        logging.info(f"Arquivo deletado: {full_path}")
                    except Exception as e:
                        logging.error(f"Erro ao deletar o arquivo {full_path}: {str(e)}")
                else:
                    logging.warning(f"Arquivo não encontrado: {full_path}")
                    
            cursor.execute(f"DELETE FROM {table_name} WHERE upload_data < ?", (cutoff_date,))
            conn.commit()
        
        cursor.close()
        conn.close()
    except Exception as e:
        logging.error(f"Erro no delete_old_photos: {str(e)}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")
    delete_old_photos()
