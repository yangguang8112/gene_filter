import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

####画图函数 dotplot####
def plot_dotplot(sub_expr_df,sub_actExpr_df,sub_pct_df,pdf_file='None'):
    ####是否需要聚类绘图？？###################
    #print('cluster start...')
    #linked = linkage(sub_expr_df, method='median')
    #print('cluster end...')
    ## 获取聚类后的细胞系顺序
    #order = leaves_list(linked)
    ## 对DataFrame进行重排序以匹配聚类结果
    #sub_expr_df = sub_expr_df.iloc[order]
    #sub_actExpr_df = sub_actExpr_df.iloc[order]
    #sub_pct_df = sub_pct_df.iloc[order]
    ######################################
    # 创建一个绘图网格
    fig, ax = plt.subplots(figsize=(18+0.25*sub_actExpr_df.shape[1], 0.25*sub_actExpr_df.shape[0]-8))
    # 绘制dotplot
    for i, cell_line in enumerate(sub_actExpr_df.index):
        for j, gene in enumerate(sub_actExpr_df.columns):
            # 圆圈大小由pct_df决定
            size = sub_pct_df.loc[cell_line, gene]  # 调整大小比例因子
            # 圆圈颜色由expr_df决定
            color = sub_actExpr_df.loc[cell_line, gene]
            ax.scatter(j, i, s=size*200, c=color, cmap='viridis', vmin=0, vmax=4)
    # 设置轴标签
    ylable=sub_actExpr_df.index.get_level_values('cell_name').astype(str) + ' # ' + sub_actExpr_df.index.get_level_values('tissue_name').astype(str)
    ax.set_xticks(range(len(sub_actExpr_df.columns)))
    ax.set_xticklabels(sub_actExpr_df.columns, rotation=90)
    ax.set_yticks(range(len(sub_actExpr_df.index)))
    ax.set_yticklabels(ylable)
    ax.set_title('scRNA_seq', fontsize=12, fontweight='bold')
    # 添加颜色条
    norm = plt.Normalize(vmin=0, vmax=4)
    sm = plt.cm.ScalarMappable(cmap='viridis', norm=norm)
    sm.set_array([])
    plt.colorbar(sm, ax=ax, orientation='vertical', fraction=0.04, pad=0.04)

    # 添加图例（用条状图表示圆圈大小）
    for size in [0.2, 0.5, 0.8, 1]:  # 这里的大小值应该根据你的pct_df的实际范围进行调整
        ax.scatter([], [], s=size*200, c='k', label=str(size))
    h, l = ax.get_legend_handles_labels()
    size_legend = ax.legend(h, l, title="Pct Value", labelspacing=1.5, loc='center left', bbox_to_anchor=(1, 0.9))
    
    plt.ylim(-1, sub_actExpr_df.shape[0] )
    if pdf_file=='None':
        return fig
        plt.show()
    else:
        plt.savefig(pdf_file, bbox_inches='tight')

if __name__ == '__main__':
    #############数据预处理##################
    expr1=pd.read_csv('/data/wusijie/database/CELLxGENE/expression_dir/human-normal-expression-summary-condensed-07-23-23.csv',index_col=0)
    expr1.head()
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

    ##################进行基因筛选##################
    # 筛选细胞系
    target_cell = expr_df.index.get_level_values('cell_name').str.contains('fat|adipocyte', case=False)   
    d=expr_df
    target_expr_high = ((d[target_cell] >  1)).sum(axis=0) >= d.shape[0]*0.7    ##在大部分（70%）目标细胞系中表达高（>1）
    other_expr_low = ((d[~target_cell] <  0.1) ).sum(axis=0) >= (d[~target_cell].shape[0]*0.98)    ##在绝大部分（98%）其他细胞系表达低（<0.1）
    d_result=pd.DataFrame({'high':target_expr_high,'low':other_expr_low})
    selected_genes = d.loc[:,target_expr_high & other_expr_low]
    #################画图##########################
    genes=selected_genes.columns.values
    genes=np.append(genes,['ACVR1C','GHR','MMP9','THRA','THRB'])   ##额外添加感兴趣的基因。
    flag = (expr_df.loc[:,genes] <  0.2).all(axis=1)    ##细胞系太多，排除掉全部低表达的细胞系。
    sub_expr_df = expr_df.loc[~flag,genes]
    sub_actExpr_df = actExpr_df.loc[~flag, genes]
    sub_pct_df = pct_df.loc[~flag, genes]
    plot_dotplot(sub_expr_df,sub_actExpr_df,sub_pct_df)
