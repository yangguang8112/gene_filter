import sqlite3
import csv
import os
import glob


def upload_csv_to_db(db_name, table_name):
    script_dir = os.path.dirname(os.path.realpath(__file__))
    upload_dir = os.path.join(script_dir, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)

    # 查找目录中的所有CSV文件
    csv_files = glob.glob(os.path.join(upload_dir, '*.csv'))

    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    for csv_file in csv_files:
        # 读取CSV文件并插入数据
        with open(csv_file, 'r', encoding='utf-8') as file:
            csv_reader = csv.reader(file, delimiter=',')
            next(csv_reader)  # 跳过标题行

            for row in csv_reader:
                # 根据列标题来解析CSV数据
                tissue_id = row[1].strip() or 'blank'
                cell_type_id = row[2].strip() or 'blank'
                gene_id = row[3].strip() or 'blank'
                number_nonzero_expression_cells = int(row[4].strip() if row[4].strip().isdigit() else 0)
                expression_sum = float(row[5].strip().replace(',', '.')) if row[5].strip() else 0.0
                number_cells = int(row[6].strip() if row[6].strip().isdigit() else 0)
                symbol = row[7].strip() or 'blank'
                cell_name = row[8].strip() or 'blank'
                tissue_name = row[9].strip() or 'blank'
                expression_sum_QC = float(row[10].strip().replace(',', '.')) if row[10].strip() else 0.0
                expr_pct = float(row[11].strip().replace(',', '.')) if row[11].strip() else 0.0
                active_expr_mean = float(row[12].strip().replace(',', '.')) if row[12].strip() else 0.0
                expr_mean = float(row[13].strip().replace(',', '.')) if row[13].strip() else 0.0

                # 插入数据到表中，包括id列
                cursor.execute(f'''INSERT INTO {table_name} (tissue_id, cell_type_id, gene_id, number_nonzero_expression_cells, 
                                            expression_sum, number_cells, symbol, cell_name, tissue_name, 
                                            expression_sum_QC, expr_pct, active_expr_mean, expr_mean)
                                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                               (tissue_id, cell_type_id, gene_id, number_nonzero_expression_cells, expression_sum,
                                number_cells, symbol, cell_name, tissue_name, expression_sum_QC, expr_pct,
                                active_expr_mean, expr_mean))

        # 提交事务
        conn.commit()
        # 删除已处理的CSV文件
        os.remove(csv_file)

    conn.close()


# 示例调用
upload_csv_to_db('example.db', 'csv_data')

