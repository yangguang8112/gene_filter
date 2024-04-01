import pandas as pd
import numpy as np
from cellxgene import plot_dotplot
import gradio as gr


def process_raw():
    print("Database init....")
    # expr1 = pd.read_csv("human-normal-expression-summary-condensed-07-23-23.csv", index_col=0)
    expr1 = pd.read_csv("small.csv", index_col=0)
    print("DB Ready")
    ###计算细胞比例。但是可能没有那么重要，因为太受实验操作的影响了。
    df_unique = expr1.drop_duplicates(subset=['tissue_id', 'cell_type_id'])
    # 接下来，我们对每个组织的细胞数目进行汇总
    tissue_cell_num = df_unique.groupby('tissue_id')['number_cells'].sum().reset_index()
    tissue_cell_num.rename(columns={'number_cells': 'tissue_cell_num'}, inplace=True)
    # 将汇总的细胞数目合并回原始dataframe
    expr1 = expr1.merge(tissue_cell_num, on='tissue_id')
    # 计算每个细胞系在其组织中的细胞比例
    expr1['cell_pct'] = expr1['number_cells'] / expr1['tissue_cell_num']
    ##转化成矩阵
    expr_df = expr1[expr1.number_cells>50].pivot_table(index=['tissue_name','cell_name'], columns='symbol', values='expr_mean', fill_value=0)
    actExpr_df = expr1[expr1.number_cells>50].pivot_table(index=['tissue_name','cell_name'], columns='symbol', values='active_expr_mean', fill_value=0)
    pct_df = expr1[expr1.number_cells>50].pivot_table(index=['tissue_name','cell_name'], columns='symbol', values='expr_pct', fill_value=0)
    pct_df=pct_df.loc[:,expr_df.columns]
    ##确保是行、列是对齐的
    assert expr_df.index.equals(pct_df.index)
    assert expr_df.columns.equals(pct_df.columns)
    assert actExpr_df.index.equals(pct_df.index)
    assert actExpr_df.columns.equals(pct_df.columns)
    return pct_df, expr_df, actExpr_df



def filter(expr_df, tissue_list, target_offset=1, target_p=0.7, other_offset=0.1, other_p=0.98):
    ##################进行基因筛选##################
    # 筛选细胞系
    target_cell = expr_df.index.get_level_values('cell_name').str.contains("|".join(tissue_list), case=False)  
    d=expr_df
    target_expr_high = ((d[target_cell] >  target_offset)).sum(axis=0) >= d[target_cell].shape[0]*target_p    ##在大部分（70%）目标细胞系中表达高（>1）
    other_expr_low = ((d[~target_cell] <  other_offset) ).sum(axis=0) >= (d[~target_cell].shape[0]*other_p)    ##在绝大部分（98%）其他细胞系表达低（<0.1）
    d_result=pd.DataFrame({'high':target_expr_high,'low':other_expr_low})
    selected_genes = d.loc[:,target_expr_high & other_expr_low]
    return selected_genes


def plotting(selected_genes, add_gene, expr_df, actExpr_df, pct_df):
    #################画图##########################
    # genes=selected_genes.columns.values
    # add_gene = ['ACVR1C','GHR','MMP9','THRA','THRB']
    # print(type(selected_genes), type(add_gene))
    if len(selected_genes) + len(add_gene) == 0:
        raise gr.Error("没有符合条件的基因！！！！请重新调整参数")
    genes=np.append(selected_genes, add_gene)   ##额外添加感兴趣的基因。
    flag = (expr_df.loc[:,genes] <  0.2).all(axis=1)    ##细胞系太多，排除掉全部低表达的细胞系。
    sub_expr_df = expr_df.loc[~flag,genes]
    sub_actExpr_df = actExpr_df.loc[~flag, genes]
    sub_pct_df = pct_df.loc[~flag, genes]
    return plot_dotplot(sub_expr_df,sub_actExpr_df,sub_pct_df)


if __name__ == '__main__':
    pct_df, expr_df, actExpr_df = process_raw()
    selected_genes = filter(expr_df, ["fat", "adipocyte"], )
    selected_genes = selected_genes.columns.values
    print(selected_genes)
    plotting(selected_genes, [], expr_df, actExpr_df, pct_df)
