import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from func import unique_group
from sqlite_tool import SqliteTool
import re
import time

def query_pct_from_database(db, cell_name, symbol):
    # 执行查询并获取结果
    query = """
    SELECT expr_pct
    FROM final
    WHERE cell_name = ? AND symbol = ?
    """
    db._cur.execute(query, (cell_name, symbol))
    result = db._cur.fetchone()
    if result is None:
        return
    return result[0]

def query_active_expr_from_database(db, cell_name, symbol):
    # 执行查询并获取结果
    query = """
    SELECT active_expr_mean
    FROM final
    WHERE cell_name = ? AND symbol = ?
    """
    db._cur.execute(query, (cell_name, symbol))
    result = db._cur.fetchone()
    if result is None:
        return
    return result[0]

def plot_dotplot(db, pdf_file='None'):

    db._cur.execute("SELECT DISTINCT cell_name, tissue_name FROM final")
    cell_tissue_data = db._cur.fetchall()

    db._cur.execute("SELECT DISTINCT symbol FROM final")
    genes_data = db._cur.fetchall()


    added_combinations = set()

    pct_dict = {}
    active_expr_dict = {}


    for cell_line, tissue in cell_tissue_data:
        if (cell_line, tissue) in added_combinations:
            continue

        pct_dict[(cell_line, tissue)] = {}
        active_expr_dict[(cell_line, tissue)] = {}


        for gene in genes_data:
            gene = gene[0]
            pct = query_pct_from_database(db, cell_line, gene)
            active_expr = query_active_expr_from_database(db, cell_line, gene)
            pct_dict[(cell_line, tissue)][gene] = pct
            active_expr_dict[(cell_line, tissue)][gene] = active_expr

        added_combinations.add((cell_line, tissue))

    min_gene_count = 15
    min_cell_tissue_count = 20
    fig, ax = plt.subplots(figsize=(max(18 + 0.25 * len(genes_data), 18 + 0.25 * min_gene_count), max(0.45 * len(cell_tissue_data) , 0.45 * min_cell_tissue_count)))

    for i, (cell_line, tissue) in enumerate(cell_tissue_data):
        for j, gene in enumerate(genes_data):
            gene = gene[0]  # 基因名称在元组的第一个位置
            size = pct_dict[(cell_line, tissue)][gene]
            if size is None:
                continue
            color = active_expr_dict[(cell_line, tissue)][gene]
            if color is None:
                continue
            ax.scatter(j, i, s=size * 200, c=color, cmap='viridis', vmin=0, vmax=4)
    # 设置 y 轴标签
    y_labels = [f"{cell} # {tissue}" for cell, tissue in cell_tissue_data]
    ax.set_yticks(range(len(y_labels)))
    #ax.set_yticklabels(y_labels)
    ax.set_yticklabels(y_labels, fontsize=5)

    # 设置 x 轴标签
    gene_names = [gene[0] for gene in genes_data]
    ax.set_xticks(range(len(gene_names)))
    ax.set_xticklabels(gene_names, rotation=90)

    # 设置标题
    ax.set_title('scRNA_seq', fontsize=12, fontweight='bold')

    # 添加颜色条
    norm = plt.Normalize(vmin=0, vmax=4)
    sm = plt.cm.ScalarMappable(cmap='viridis', norm=norm)
    sm.set_array([])
    plt.colorbar(sm, ax=ax, orientation='vertical', fraction=0.04, pad=0.08)

    for size in [0.2, 0.5, 0.8, 1]:
        ax.scatter([], [], s=size * 200, c='k', label=str(size))
    h, l = ax.get_legend_handles_labels()
    size_legend = ax.legend(h, l, title="Pct Value", labelspacing=1.5, loc='center left', bbox_to_anchor=(1, 0.6))

    plt.ylim(-1, len(cell_tissue_data))
    if pdf_file == 'None':
        return fig
        #plt.show()
    else:
        plt.savefig(pdf_file, format='png', bbox_inches='tight')


def my_function(db):

    time.sleep(2)
    start_time = time.time()
    tissue_list = ["mast cell"]
    plot_dotplot(db, pdf_file='None')
    end_time = time.time()
    run_time = end_time - start_time
    print("函数运行时间：", run_time, "秒")


if __name__ == '__main__':
    db = SqliteTool('example.db')
    #unique_count = unique_group(db, "final")
    #print(unique_count)
    #gene_count = db.get_unique_column_values("final", "symbol")
    #cell_lines = db.get_unique_column_values("final", "cell_name")
    #print(cell_lines)
    #print(gene_count)
    #print(len(gene_count))
    #result = query_pct_from_database(db, "mast cell", "TPSAB1")
    #print(result)
    #plot_dotplot(db, pdf_file='None')
    my_function(db)
