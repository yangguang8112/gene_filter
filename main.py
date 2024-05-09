import gradio as gr
from func import extract_matched_and_unmatched_rows_by_cell_name, unique_group, filter_groups_above_threshold, filter_genes_by_threshold_other, insert_rows_with_combined_genes, filter_genes_by_threshold
from sqlite_tool import SqliteTool
from cellxgene import plot_dotplot


def filter_plotting(tissue_list, target_offset, target_p, other_offset, other_p, add_gene):
    db = SqliteTool('example.db')
    source_table = "target_table"
    db.drop_table_if_exists("final")
    matched_rows_str, unmathed_rows_str = extract_matched_and_unmatched_rows_by_cell_name(db, source_table, tissue_list)
    target_count = unique_group(db, matched_rows_str, source_table)
    other_count = unique_group(db, unmathed_rows_str, source_table)
    filtered_genes = filter_genes_by_threshold(db, matched_rows_str, target_offset, target_p * target_count)
    filtered_genes_other = filter_genes_by_threshold_other(db, unmathed_rows_str, other_offset, other_count, other_p * other_count)
    gene_list1 = [gene[0] for gene in filtered_genes]
    gene_list2 = [gene[0] for gene in filtered_genes_other]
    intersection_gene_set = set(gene_list1).intersection(gene_list2)
    selected_gene = [gene for gene in intersection_gene_set if gene != 'blank']
    if add_gene:
        selected_gene = selected_gene + add_gene
    print(selected_gene)
    insert_rows_with_combined_genes(db, "target_table", "final", selected_gene)
    filter_groups_above_threshold(db)
    fig = plot_dotplot(db)
    db.close_connection()
    return fig


db = SqliteTool('example.db')
cell_names = db.get_unique_column_values("target_table", "cell_name")
cell_names = set([c for cell in cell_names for c in cell.split(",")])
gene_list = db.get_unique_column_values("target_table", "symbol")
db.close_connection()


demo = gr.Interface(
    fn=filter_plotting,
    inputs=[
        gr.Dropdown(cell_names, multiselect=True, label="select tissue"),
        gr.Number(),
        gr.Number(),
        gr.Number(),
        gr.Number(),
        gr.Dropdown(gene_list, multiselect=True, label="额外添加gene")
        ],
    outputs=[gr.Plot()],
)
demo.launch(server_name="127.0.0.1")
