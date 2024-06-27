import gradio as gr
from func import extract_matched_and_unmatched_rows_by_cell_name, unique_group, filter_groups_above_threshold, \
    filter_genes_by_threshold_other, insert_rows_with_combined_genes, filter_genes_by_threshold, extract_matched_rows_from_database, df_data
from sqlite_tool import SqliteTool
# from cellxgene import plot_dotplot, fetch_data_from_database
# from cellxgene_filter import plot_dot, fetch_data
from plot import plotting
import os
import pandas as pd
import tempfile
import shutil
from upload import upload_csv_to_db
from process import process_raw

global tmpdir
db = SqliteTool('example.db')
disease = ['normal']
sex = ['female', 'male', 'unknown']
self_reported_ethnicity = ['British']
organism = ['Homo sapiens']
cell_names = db.get_unique_column_values("target_table", "cell_name")
cell_names = set([c for cell in cell_names for c in cell.split(",")])
gene_list = db.get_unique_column_values("target_table", "symbol")
db.close_connection()


def filter_plot(tissue_list, add_gene):
    print("You are choosing interface 2!")
    print(add_gene)
    db = SqliteTool('example.db')
    source_table = "target_table"
    db.drop_table_if_exists("new")
    matched_rows_str, unmathed_rows_str = extract_matched_and_unmatched_rows_by_cell_name(db, source_table, tissue_list)
    df = extract_matched_rows_from_database(db, "target_table", matched_rows_str, add_gene)
    # df = fetch_data(db)
    fig = plotting(df)
    db.close_connection()
    return fig

def filter_plotting(tissue_list, target_offset, target_p, other_offset, other_p, add_gene):
    print("You are choosing interface 1!")
    db = SqliteTool('example.db')
    source_table = "target_table"
    #db.drop_table_if_exists("final")
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
    #insert_rows_with_combined_genes(db, "target_table", "final", selected_gene)
    #filter_groups_above_threshold(db)
    #df = fetch_data_from_database(db)
    df = df_data(db, source_table, matched_rows_str, selected_gene, 0.2)
    fig = plotting(df)
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


def generate_file(file_obj):
    required_columns = [
        'tissue_id', 'cell_type_id', 'gene_id', 'number_nonzero_expression_cells',
        'expression_sum', 'number_cells', 'symbol', 'cell_name', 'tissue_name',
        'expression_sum_QC', 'expr_pct', 'active_expr_mean', 'expr_mean'
    ]

    with tempfile.TemporaryDirectory(dir='.') as tmpdir:
        print('临时文件夹地址：{}'.format(tmpdir))
        print('上传文件的地址：{}'.format(file_obj.name))

        # Get the file name and construct the new file path
        file_name = os.path.basename(file_obj.name)
        uploaded_file_path = os.path.join(tmpdir, file_name)

        # Copy the file to the temporary directory
        shutil.copy(file_obj.name, uploaded_file_path)

        # Print the path of the uploaded file
        print('复制到临时文件夹的路径：{}'.format(uploaded_file_path))
        try:
            df = pd.read_csv(uploaded_file_path)
        except Exception as e:
            return f"文件读取失败：{e}"

        # Check if required columns are present
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return f"文件中缺少以下必要的列：{', '.join(missing_columns)}"

        upload_csv_to_db(uploaded_file_path)

        return "文件已上传并处理完成"

css_style = """
    .output-html {
        overflow-x: auto;
        white-space: nowrap;
        max-width: 100%;
    }
    """

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
            #sex = gr.Dropdown(sex, multiselect=True, label="sex")
            #disease = gr.Dropdown(disease, multiselect=True, label="disease")
        plot_btn2 = gr.Button("Plot")
        plot_output2 = gr.Plot()
        plot_btn2.click(filter_plot, inputs=[tissue_list2, add_gene2], outputs=plot_output2)

    with gr.TabItem("Database"):
        info_text = """
        上传的CSV文件应包含以下列：
        - tissue_id: 组织ID
        - cell_type_id: 细胞类型ID
        - gene_id: 基因ID
        - number_nonzero_expression_cells: 非零表达细胞数
        - expression_sum: 表达总和
        - number_cells: 细胞数
        - symbol: 符号
        - cell_name: 细胞名称
        - tissue_name: 组织名称
        - expression_sum_QC: 质量控制后的表达总和
        - expr_pct: 表达百分比
        - active_expr_mean: 活跃表达均值
        - expr_mean: 表达均值
        """
        gr.Markdown(info_text)

        with gr.TabItem("Upload"):
            inputs = gr.File(label="上传CSV文件")
            outputs = gr.Textbox(label="处理结果")
            plot_btn3 = gr.Button("submit")
            plot_btn3.click(generate_file, inputs=inputs, outputs=outputs)

    # with gr.TabItem("Calculate"):
    #     info_text = """
    #             点击按钮可以实现对各个组织的细胞数目进行汇总和计算每个细胞系在其组织中的细胞比例
    #             """
    #     gr.Markdown(info_text)
    #     with gr.TabItem("calculate"):
    #         plot_btn3 = gr.Button("calculate")
    #         plot_btn3.click(process_raw)




demo.launch(server_name="127.0.0.1")
