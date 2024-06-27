import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def plotting(df):
    df['size'] = df['expr_pct'] * 200  # Adjust size for Plotly
    num_cells = len(df['cell_label'].unique())
    num_genes = len(df['symbol'].unique())

    fig = px.scatter(
        df,
        x='symbol',
        y='cell_label',
        size='size',
        color='active_expr_mean',
        hover_data={
            'cell_name': True,
            'tissue_name': True,
            'symbol': True,
            'expr_pct': True,
            'active_expr_mean': True,
            'size': False  # Hide the size field
        },
        color_continuous_scale='viridis',
        range_color=[0, 4],
        title='scRNA_seq'
    )

    # Adjust width and height based on the number of genes and cells
    fig.update_layout(
        width=1000 + 100 * num_genes,
        height=250 + 50 * num_cells,
        yaxis=dict(
            tickmode='array',
            tickvals=list(range(len(df['cell_label'].unique()))),
            ticktext=df['cell_label'].unique()
        ),
        xaxis=dict(
            tickmode='array',
            tickvals=list(range(len(df['symbol'].unique()))),
            ticktext=df['symbol'].unique(),
            tickangle=90
        )
    )

    fig.update_traces(marker=dict(line=dict(width=0.5, color='White')))

    # Add legend for circle sizes
    sizes = [0.2, 0.5, 0.8, 1.0]  # Example sizes
    for size in sizes:
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode='markers',
            marker=dict(
                size=size * 200,  # Adjust the size here similarly
                color='lightgray',
                line=dict(width=0.5, color='White')
            ),
            showlegend=True,
            name=f'Size: {size}'
        ))
    fig.update_layout(
        legend=dict(
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.1,
            traceorder="normal",
            font=dict(size=10)
        )
    )
    #print(fig)
    return fig