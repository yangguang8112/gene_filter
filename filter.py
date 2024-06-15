from sqlite_tool import SqliteTool
import re

#db = SqliteTool('example.db')

def extract_matched_and_unmatched_rows_by_cell_name(db, source_table, keywords):
    matched_rows = []
    unmatched_rows = []

    unique_cell_names = db.get_index_column_values("unique_csv_data", "cell_name")

    for cell_name in unique_cell_names:
        matched = False
        for keyword in keywords:
            pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
            if re.search(pattern, cell_name):
                matched_rows.append(cell_name)
                matched = True
                break
        if not matched:
            unmatched_rows.append(cell_name)
    matched_rows = list(set(matched_rows))
    matched_rows_str = ', '.join([f"'{row}'" for row in matched_rows])
    unmatched_rows_str = ', '.join([f"'{row}'" for row in unmatched_rows])
    #print(matched_rows_str)
    #print(unmatched_rows_str)
    return matched_rows_str, unmatched_rows_str


def extract_matched_rows_from_database(db, source_table, matched_rows_str, new_table_name, gene_list):
    # 构建基因列表的条件
    gene_condition = " OR ".join([f"symbol = '{gene}'" for gene in gene_list])

    # 构建完整的查询语句
    query = f"""
    CREATE TABLE IF NOT EXISTS {new_table_name} AS
    SELECT *
    FROM {source_table}
    WHERE (cell_name IN ({matched_rows_str})) AND ({gene_condition});
    """
    db._cur.execute(query)


def extract_matched_and_unmatched_rows_from_database(db, source_table, matched_rows_str, unmatched_rows_str,
                                                     matched_table_name, unmatched_table_name):
    # 创建匹配的表格
    matched_query = f"""
    CREATE TABLE IF NOT EXISTS {matched_table_name} AS
    SELECT *
    FROM {source_table}
    WHERE cell_name IN ({matched_rows_str});
    """
    db._cur.execute(matched_query)

    # 创建不匹配的表格
    unmatched_query = f"""
    CREATE TABLE IF NOT EXISTS {unmatched_table_name} AS
    SELECT *
    FROM {source_table}
    WHERE cell_name IN ({unmatched_rows_str});
    """
    db._cur.execute(unmatched_query)

    db._conn.commit()


if __name__ == '__main__':
    db = SqliteTool('example.db')
    #db.drop_table_if_exists("final")
    tissue_list = ["mast cell"]
    source_table = "target_table"
    matched_rows_str, unmathed_rows_str = extract_matched_and_unmatched_rows_by_cell_name(db, source_table, tissue_list)
    print(matched_rows_str)
    print(unmathed_rows_str)
    db.drop_table_if_exists("new")
    add_gene = ["KRIT1", "CD99"]
    extract_matched_rows_from_database(db, "target_table", matched_rows_str, "new", add_gene)
    #extract_matched_and_unmatched_rows_from_database(db, "target_table", matched_rows_str, unmathed_rows_str, "new", "old")