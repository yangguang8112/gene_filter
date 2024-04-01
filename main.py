import gradio as gr
from func import process_raw, filter, plotting

# def greet(name, is_morning, temperature):
#     salutation = "Good morning" if is_morning else "Good evening"
#     greeting = f"{salutation} {name}. It is {temperature} degrees today"
#     celsius = (temperature - 32) * 5 / 9
#     return greeting, round(celsius, 2)

pct_df, expr_df, actExpr_df = process_raw()


def filter_plotting(tissue_list, target_offset, target_p, other_offset, other_p, add_gene):
    # print(type(tissue_list))
    print(target_offset, target_p, other_offset, other_p)
    selected_genes = filter(expr_df, tissue_list, target_offset, target_p, other_offset, other_p)
    selected_genes = selected_genes.columns.values
    print(selected_genes)
    fig = plotting(selected_genes, add_gene, expr_df, actExpr_df, pct_df)
    # print(fig)
    return fig


# print(expr_df)
# print(expr_df.index.get_level_values('cell_name'))
cell_names = expr_df.index.get_level_values('cell_name').tolist()
cell_names = set([c for cell in cell_names for c in cell.split(",")])
gene_list = expr_df.columns.tolist()



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
demo.launch(server_name="0.0.0.0")
