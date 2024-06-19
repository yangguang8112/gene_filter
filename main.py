import gradio as gr
from func import extract_matched_and_unmatched_rows_by_cell_name, unique_group, filter_groups_above_threshold, \
    filter_genes_by_threshold_other, insert_rows_with_combined_genes, filter_genes_by_threshold
from filter import extract_matched_rows_from_database
from sqlite_tool import SqliteTool
from cellxgene import plot_dotplot, fetch_data_from_database
from cellxgene_filter import plot_dot, fetch_data

db = SqliteTool('example.db')
disease = ['normal']
sex = ['female', 'male', 'unknown']
self_reported_ethnicity = ['British']
organism = ['Homo sapiens']
cell_names = db.get_unique_column_values("target_table", "cell_name")
cell_names = set([c for cell in cell_names for c in cell.split(",")])
gene_list = db.get_unique_column_values("target_table", "symbol")
db.close_connection()


def filter_plot(tissue_list, add_gene, sex, disease):
    print("You are choosing interface 2!")
    print(add_gene)
    db = SqliteTool('example.db')
    source_table = "target_table"
    db.drop_table_if_exists("new")
    matched_rows_str, unmathed_rows_str = extract_matched_and_unmatched_rows_by_cell_name(db, source_table, tissue_list)
    extract_matched_rows_from_database(db, "target_table", matched_rows_str, "new", add_gene)
    df = fetch_data(db)
    fig = plot_dot(df)
    db.close_connection()
    return fig


def filter_plotting(tissue_list, target_offset, target_p, other_offset, other_p, add_gene):
    print("You are choosing interface 1!")
    db = SqliteTool('example.db')
    source_table = "target_table"
    db.drop_table_if_exists("final")
    print(tissue_list)
    matched_rows_str, unmathed_rows_str = extract_matched_and_unmatched_rows_by_cell_name(db, source_table, tissue_list)
    target_count = unique_group(db, matched_rows_str, source_table)
    other_count = unique_group(db, unmathed_rows_str, source_table)
    filtered_genes = filter_genes_by_threshold(db, matched_rows_str, target_offset, target_p * target_count)
    filtered_genes_other = filter_genes_by_threshold_other(db, unmathed_rows_str, other_offset, other_count,
                                                           other_p * other_count)
    gene_list1 = [gene[0] for gene in filtered_genes]
    gene_list2 = [gene[0] for gene in filtered_genes_other]
    intersection_gene_set = set(gene_list1).intersection(gene_list2)
    selected_gene = [gene for gene in intersection_gene_set if gene != 'blank']
    if add_gene:
        selected_gene = selected_gene + add_gene
    print(selected_gene)
    insert_rows_with_combined_genes(db, "target_table", "final", selected_gene)
    filter_groups_above_threshold(db)
    df = fetch_data_from_database(db)
    fig = plot_dotplot(df)
    #fig = plot_dotplot(db)
    db.close_connection()
    return fig


def insert_data(tissue_id, cell_type_id, gene_id, number_nonzero_expression_cells, expression_sum,
                number_cells, symbol, cell_name, tissue_name, expression_sum_QC, expr_pct, active_expr_mean, expr_mean):
    db = SqliteTool('example.db')
    data = {
        'tissue_id': tissue_id,
        'cell_type_id': cell_type_id,
        'gene_id': gene_id,
        'number_nonzero_expression_cells': int(number_nonzero_expression_cells),
        'expression_sum': float(expression_sum),
        'number_cells': int(number_cells),
        'symbol': symbol,
        'cell_name': cell_name,
        'tissue_name': tissue_name,
        'expression_sum_QC': float(expression_sum_QC),
        'expr_pct': float(expr_pct),
        'active_expr_mean': float(active_expr_mean),
        'expr_mean': float(expr_mean)
    }

    # 检查所有必需字段是否有效
    if not all(data.values()):
        db.close_connection()
        return "Missing required fields"

    db.insert_data('csv_data', data)
    db.close_connection()
    return f"Data inserted: {data}"

def delete_data(tissue_id, cell_type_id, gene_id):
    db = SqliteTool('example.db')
    result = db.delete_data(tissue_id, cell_type_id, gene_id)
    db.close_connection()
    return result


with gr.Blocks() as demo:
    with gr.TabItem("Gene Filter"):
        with gr.Row():
            tissue_list1 = gr.Dropdown(cell_names, multiselect=True, label="Select Tissue")
            target_offset = gr.Number(label="Target Offset")
            target_p = gr.Number(label="Target P")
            other_offset = gr.Number(label="Other Offset")
            other_p = gr.Number(label="Other P")
            add_gene1 = gr.Dropdown(gene_list, multiselect=True, label="Add Gene")
        plot_btn1 = gr.Button("Plot")
        plot_output1 = gr.Plot()
        plot_btn1.click(filter_plotting,
                        inputs=[tissue_list1, target_offset, target_p, other_offset, other_p, add_gene1],
                        outputs=plot_output1)

    with gr.TabItem("Filter"):
        with gr.Row():
            tissue_list2 = gr.Dropdown(cell_names, multiselect=True, label="Select Tissue")
            add_gene2 = gr.Dropdown(gene_list, multiselect=True, label="Add Gene")
            sex = gr.Dropdown(sex, multiselect=True, label="sex")
            disease = gr.Dropdown(disease, multiselect=True, label="disease")
        plot_btn2 = gr.Button("Plot")
        plot_output2 = gr.Plot()
        plot_btn2.click(filter_plot, inputs=[tissue_list2, add_gene2, sex, disease], outputs=plot_output2)

    # with gr.TabItem("Data Insertion"):
    #     with gr.Row():
    #         tissue_id = gr.Textbox(label="Tissue ID")
    #         cell_type_id = gr.Textbox(label="Cell Type ID")
    #         gene_id = gr.Textbox(label="Gene ID")
    #         number_nonzero_expression_cells = gr.Number(label="Number Nonzero Expression Cells")
    #         expression_sum = gr.Number(label="Expression Sum")
    #         number_cells = gr.Number(label="Number Cells")
    #         symbol = gr.Textbox(label="Symbol")
    #         cell_name = gr.Textbox(label="Cell Name")
    #         tissue_name = gr.Textbox(label="Tissue Name")
    #         expression_sum_QC = gr.Number(label="Expression Sum QC")
    #         expr_pct = gr.Number(label="Expression Pct")
    #         active_expr_mean = gr.Number(label="Active Expr Mean")
    #         expr_mean = gr.Number(label="Expr Mean")
    #     insert_btn = gr.Button("Insert Data")
    #     insert_output = gr.Textbox()
    #     insert_btn.click(insert_data,
    #                      inputs=[tissue_id, cell_type_id, gene_id, number_nonzero_expression_cells, expression_sum,
    #                              number_cells, symbol, cell_name, tissue_name, expression_sum_QC, expr_pct, active_expr_mean, expr_mean],
    #                      outputs=insert_output)
    #
    # with gr.TabItem("Data Deletion"):
    #     with gr.Row():
    #         tissue_id = gr.Textbox(label="Tissue ID")
    #         cell_type_id = gr.Textbox(label="Cell Type ID")
    #         gene_id = gr.Textbox(label="Gene ID")
    #     delete_btn = gr.Button("Delete Data")
    #     delete_output = gr.Textbox()
    #     delete_btn.click(delete_data, inputs=[tissue_id, cell_type_id, gene_id], outputs=delete_output)

demo.launch(server_name="127.0.0.1")

