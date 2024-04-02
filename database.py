import sqlite3
import csv

# 连接到SQLite数据库
conn = sqlite3.connect('example.db')
cursor = conn.cursor()

# 创建表
create_table_sql = '''
CREATE TABLE IF NOT EXISTS csv_data (
    id INTEGER,
    tissue_id TEXT,
    cell_type_id TEXT,
    gene_id TEXT,
    number_nonzero_expression_cells INTEGER,
    expression_sum REAL,
    number_cells INTEGER,
    symbol TEXT,
    cell_name TEXT,
    tissue_name TEXT,
    expression_sum_QC REAL,
    expr_pct REAL,
    active_expr_mean REAL,
    expr_mean REAL
)
'''
cursor.execute(create_table_sql)

# 读取CSV文件并插入数据
with open('small.csv', 'r') as file:
    csv_reader = csv.reader(file, delimiter=',')
    next(csv_reader)  # 跳过标题行

    for row in csv_reader:
        # 根据列标题来解析CSV数据
        id_value = row[0].strip()
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
        cursor.execute('''INSERT INTO csv_data (id, tissue_id, cell_type_id, gene_id, number_nonzero_expression_cells, 
                                     expression_sum, number_cells, symbol, cell_name, tissue_name, 
                                     expression_sum_QC, expr_pct, active_expr_mean, expr_mean)
                                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                       (id_value, tissue_id, cell_type_id, gene_id, number_nonzero_expression_cells, expression_sum,
                        number_cells,
                        symbol, cell_name, tissue_name, expression_sum_QC, expr_pct, active_expr_mean, expr_mean))
# 提交事务
conn.commit()
conn.close()