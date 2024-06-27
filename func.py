from sqlite_tool import SqliteTool
import re
import pandas as pd

#db = SqliteTool('example.db')
def extract_matched_rows_from_database(db, source_table, matched_rows_str, gene_list):
    gene_condition = " OR ".join([f"symbol = ?" for gene in gene_list])
    columns = ['cell_name', 'tissue_name', 'symbol', 'expr_mean', 'expr_pct', 'active_expr_mean']
    query = f"""
    SELECT {', '.join(columns)}
    FROM {source_table}
    WHERE cell_name IN ({matched_rows_str}) AND ({gene_condition});
    """
    params = gene_list
    db._cur.execute(query, params)
    filtered_data = db._cur.fetchall()
    # Convert the result to a DataFrame
    df_filtered = pd.DataFrame(filtered_data, columns=columns)
    df_filtered['cell_label'] = df_filtered['cell_name'] + ' # ' + df_filtered['tissue_name']

    return df_filtered


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



def df_data(db, source_table, matched_rows_str, combined_gene_list, threshold=0.2):
    columns = ['cell_name', 'tissue_name', 'symbol', 'expr_mean', 'expr_pct', 'active_expr_mean']

    # Convert matched_rows_str to a list of cell names
    matched_rows_list = matched_rows_str.replace("'", "").split(", ")

    # Construct the filter query
    filter_query = f"""
    SELECT {', '.join(columns)}
    FROM {source_table}
    WHERE symbol IN ({','.join(['?' for _ in combined_gene_list])})
    AND cell_name IN ({','.join(['?' for _ in matched_rows_list])})
    AND (tissue_name, cell_name) IN (
        SELECT tissue_name, cell_name
        FROM {source_table}
        GROUP BY tissue_name, cell_name
        HAVING SUM(CASE WHEN expr_mean > ? THEN 1 ELSE 0 END) > 0
    )
    """

    # Construct params list
    params = combined_gene_list + matched_rows_list + [threshold]

    # Execute the query
    db._cur.execute(filter_query, params)
    filtered_data = db._cur.fetchall()

    # Convert the result to a DataFrame
    df_filtered = pd.DataFrame(filtered_data, columns=columns)
    df_filtered['cell_label'] = df_filtered['cell_name'] + ' # ' + df_filtered['tissue_name']

    return df_filtered


def unique_group(db, rows_str, table):
    count_unique_combinations_query = f"""
    SELECT COUNT(*) AS unique_combinations
    FROM (
        SELECT DISTINCT tissue_name, cell_name
        FROM {table}
        WHERE cell_name IN ({rows_str})
    )
    """
    db._cur.execute(count_unique_combinations_query)
    unique_combinations = db._cur.fetchone()[0]
    return unique_combinations

def filter_genes_by_threshold(db, matched_rows_str, threshold_value, min_count_value):

    query = f"""
    SELECT
        symbol,
        AVG(expr_mean) AS expr_mean,
        AVG(expr_pct) AS expr_pct,
        AVG(active_expr_mean) AS active_expr_mean,
        AVG(tissue_cell_num) AS tissue_cell_num,
        AVG(cell_pct) AS cell_pct,
        SUM(CASE WHEN expr_mean > ? THEN 1 ELSE 0 END) AS count_above_threshold
    FROM
        target_table
    WHERE
        cell_name IN ({matched_rows_str})
    GROUP BY
        symbol
    HAVING
        count_above_threshold >= ?;
    """

    db._cur.execute(query, (threshold_value, min_count_value))
    results = db._cur.fetchall()
    return results

def filter_genes_by_threshold_other(db, unmatched_rows_str, threshold_value, rows, min_count_value):

    query = f"""
    SELECT
        symbol,
        AVG(expr_mean) AS expr_mean,
        AVG(expr_pct) AS expr_pct,
        AVG(active_expr_mean) AS active_expr_mean,
        AVG(tissue_cell_num) AS tissue_cell_num,
        AVG(cell_pct) AS cell_pct,
        SUM(CASE WHEN expr_mean > ? THEN 1 ELSE 0 END) AS opp_count_below_threshold
    FROM
        target_table
    WHERE
        cell_name IN ({unmatched_rows_str})
    GROUP BY
        symbol
    HAVING        
        ?-opp_count_below_threshold >= ?;
    """
    db._cur.execute(query, (threshold_value, rows, min_count_value))
    other_results = db._cur.fetchall()
    return other_results

def insert_rows_with_combined_genes(db, source_table, target_table, combined_gene_list):
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {target_table} AS
    SELECT * FROM {source_table}
    WHERE symbol IN ({','.join(['?' for _ in combined_gene_list])})
    ;
    """
    db._cur.execute(create_table_sql, combined_gene_list)
    db._conn.commit()
    print(f"Rows with genes from combined_gene_list have been inserted into table '{target_table}'.")

def filter_groups_above_threshold(db):
    db._cur.execute('''
        DELETE FROM final
        WHERE (tissue_name, cell_name) IN (
            SELECT tissue_name, cell_name
            FROM final
            GROUP BY tissue_name, cell_name
            HAVING SUM(CASE WHEN expr_mean > 0.2 THEN 1 ELSE 0 END) = 0
        )
    ''')
    db._conn.commit()

if __name__ == '__main__':
    db = SqliteTool('example.db')
    db.drop_table_if_exists("final")
    tissue_list = ["mast cell"]
    source_table = "target_table"
    matched_rows_str, unmathed_rows_str = extract_matched_and_unmatched_rows_by_cell_name(db, source_table, tissue_list)
    print(matched_rows_str)
    target_count = unique_group(db, matched_rows_str, source_table)
    other_count = unique_group(db, unmathed_rows_str, source_table)
    threshold_gt = 1
    threshold_lt = 0.1
    target_p = 0.7
    other_p = 0.98
    print(target_count)
    print(other_count)
    filtered_genes = filter_genes_by_threshold(db, matched_rows_str, threshold_gt, target_p * target_count)
    filtered_genes_other = filter_genes_by_threshold_other(db, unmathed_rows_str, threshold_lt, other_count,
                                                           other_p * other_count)
    gene_list1 = [gene[0] for gene in filtered_genes]
    gene_list2 = [gene[0] for gene in filtered_genes_other]
    intersection_gene_set = set(gene_list1).intersection(gene_list2)
    selected_gene = [gene for gene in intersection_gene_set if gene != 'blank']

    print(selected_gene)
    print(len(gene_list1))
    print(len(gene_list2))
    print(len(selected_gene))
    insert_rows_with_combined_genes(db, "target_table", "final", selected_gene)
    filter_groups_above_threshold(db)