# dashboard.py (最终版 - 包含所有修正及美化后的外部HTML链接)

import pandas as pd
import json
import jieba
import io
import base64
from wordcloud import WordCloud
from collections import Counter
import sys
from datetime import datetime

# 导入matplotlib的字体管理器
import matplotlib.font_manager as fm

import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import plotly.express as px

# ========================= 0. 自动查找系统字体函数 =========================

def get_system_font():
    """自动在系统中查找可用的中文字体。"""
    print("--- 正在自动查找系统中可用的中文字体... ---")
    font_preferences = [
        'SimHei',          # 黑体 (Windows)
        'Microsoft YaHei', # 微软雅黑 (Windows)
        'PingFang SC',     # 苹方 (macOS)
        'WenQuanYi Zen Hei'# 文泉驿正黑 (Linux)
    ]
    
    for font_name in font_preferences:
        try:
            font_path = fm.findfont(fm.FontProperties(family=font_name))
            if font_path:
                print(f"--- 成功找到字体: {font_name} @ {font_path} ---")
                return font_path
        except Exception:
            continue
            
    print("!!! 未找到指定的中文字体。词云图可能无法正确显示中文。!!!")
    return None

# ========================= 1. 数据加载与预处理 =========================

SYSTEM_FONT_PATH = get_system_font()
if not SYSTEM_FONT_PATH:
    sys.exit("错误：无法生成词云图，因为缺少必要的中文字体。程序已终止。")

print("--- 正在加载和处理 classified_news_data_v2.json ---")
TOPIC_MAP = {
    1: "人才培养",
    2: "基础科研",
    3: "技术创新"
}
try:
    with open('classified_news_data_v2.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
except FileNotFoundError:
    print("致命错误：'classified_news_data_v2.json' 文件未找到！请确保该文件在脚本的同一目录下。")
    exit()

df = pd.json_normalize(data)
df.rename(columns={'predicted_topic.id': 'topic_id', 'predicted_topic.probability': 'probability'}, inplace=True)
df['topic_id'] = df['topic_id'].astype(int)
df['topic_name'] = df['topic_id'].map(TOPIC_MAP)
df['time'] = pd.to_datetime(df['time'])

stop_words = {'我们', '的', '了', '是', '在', '也', '等', '该', '将', '为', '以', '对', '和', '中', '月', '日', '年'}
jieba.setLogLevel('WARN')
def get_keywords(text):
    if not isinstance(text, str): return []
    words = jieba.lcut(text)
    return [word for word in words if word not in stop_words and len(word) > 1 and not word.isnumeric()]

print("--- 正在对所有新闻内容进行预分词... ---")
df['keywords'] = df['content'].apply(get_keywords)
print("--- 数据准备完成！即将启动Web服务... ---")

# ========================= 2. 定义Dash应用布局 =========================

external_stylesheets = [{'href': 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css', 'rel': 'stylesheet'}]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
app.title = "新闻主题动态分析仪表盘"

min_date = df['time'].min().date()
max_date = df['time'].max().date()

# 【新增】为卡片式链接定义通用样式
card_container_style = {
    'display': 'flex',
    'justifyContent': 'space-around',
    'gap': '20px',
    'flexWrap': 'wrap'
}
card_style = {
    'flex': '1',
    'minWidth': '300px',
    'padding': '25px',
    'textAlign': 'center',
    'backgroundColor': '#ffffff',
    'borderRadius': '10px',
    'boxShadow': '0 4px 8px 0 rgba(0,0,0,0.1)',
    'transition': 'transform 0.3s ease-in-out',
    'display': 'flex',
    'flexDirection': 'column',
    'justifyContent': 'space-between'
}
card_button_style = {
    'display': 'inline-block',
    'padding': '10px 20px',
    'marginTop': '15px',
    'fontSize': '14px',
    'fontWeight': 'bold',
    'color': '#ffffff',
    'backgroundColor': '#3498db',
    'border': 'none',
    'borderRadius': '5px',
    'textDecoration': 'none',
    'cursor': 'pointer',
}


app.layout = html.Div(style={
    'fontFamily': '"Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif', 'padding': '20px 40px',
    'backgroundColor': '#f5f7fa', 'minHeight': '100vh'
}, children=[
    
    dcc.Store(id='current-topic-store', data=None),
    dcc.Store(id='pause-state-store', data=False),

    # 顶部标题栏
    html.Div(style={'background': 'linear-gradient(135deg, #2c3e50, #3498db)', 'padding': '20px', 'borderRadius': '8px',
                   'marginBottom': '25px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)', 'color': 'white'}, children=[
        html.H1("新闻主题热度与关键词动态分析仪表盘", style={'textAlign': 'center', 'marginBottom': '10px', 'fontWeight': '600'}),
        html.P("实时监测三大主题发展趋势与核心关键词", style={'textAlign': 'center', 'fontSize': '16px', 'opacity': '0.9'})
    ]),

    # 【核心修改】外部可视化报告链接区域，采用卡片式布局
    html.Div([
        html.H2("拓展分析报告", style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '25px'}),
        html.Div([
            # 卡片1: 共现网络
            html.Div([
                html.Div([
                    html.H5("词语共现网络图", style={'color': '#34495e', 'margin': '0 0 10px 0'}),
                    html.P("探索高频词汇之间的关联强度与网络结构。", style={'fontSize': '14px', 'color': '#7f8c8d', 'lineHeight': '1.5'}),
                ]),
                html.A("点击查看", href="/assets/word_co-occurrence_network_warm_theme.html", 
                       target="_blank", style=card_button_style)
            ], style=card_style),
            # 卡片2: LDA主题模型
            html.Div([
                html.Div([
                    html.H5("LDA主题模型分析", style={'color': '#34495e', 'margin': '0 0 10px 0'}),
                    html.P("从文本数据中自动发现隐藏的主题分布与关键特征词。", style={'fontSize': '14px', 'color': '#7f8c8d', 'lineHeight': '1.5'}),
                ]),
                html.A("点击查看", href="/assets/lda_visualization_final_k3.html", 
                       target="_blank", style=card_button_style)
            ], style=card_style),
            # 卡片3: 总体分析仪表盘
            html.Div([
                html.Div([
                    html.H5("新闻数据总体分析", style={'color': '#34495e', 'margin': '0 0 10px 0'}),
                    html.P("一个包含多维度图表的交互式可视化仪表盘。", style={'fontSize': '14px', 'color': '#7f8c8d', 'lineHeight': '1.5'}),
                ]),
                html.A("点击查看", href="/assets/data_visualization_dashboard.html", 
                       target="_blank", style=card_button_style)
            ], style=card_style),
        ], style=card_container_style)
    ], style={'padding': '20px 0', 'marginBottom': '25px'}),

    # 控制面板区域
    html.Div(style={'display': 'flex', 'justifyContent': 'space-between', 'marginBottom': '25px', 'flexWrap': 'wrap'}, children=[
        # 日期选择器
        html.Div(style={'flex': '1', 'minWidth': '300px', 'padding': '15px', 'backgroundColor': 'white',
                       'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.05)', 'marginRight': '20px'}, children=[
            html.H4(style={'marginBottom': '15px', 'color': '#2c3e50', 'display': 'flex', 'alignItems': 'center'}, children=[
                html.I(className="far fa-calendar-alt", style={'marginRight': '10px'}), "请选择分析的时间范围:"
            ]),
            dcc.DatePickerRange(id='date-picker-range', min_date_allowed=min_date, max_date_allowed=max_date,
                                start_date=min_date, end_date=max_date, display_format='YYYY-MM-DD', style={'width': '100%'})
        ]),
        
        # 主题切换按钮组
        html.Div(style={'flex': '1', 'minWidth': '300px', 'padding': '15px', 'backgroundColor': 'white',
                       'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.05)'}, children=[
            html.H4(style={'marginBottom': '15px', 'color': '#2c3e50', 'display': 'flex', 'alignItems': 'center'}, children=[
                html.I(className="fas fa-tags", style={'marginRight': '10px'}), "点击按钮快速切换主题:"
            ]),
            html.Div(style={'display': 'flex', 'justifyContent': 'space-between'}, children=[
                html.Button("全部主题", id='btn-all', n_clicks=0, style={'flex': '1', 'margin': '0 5px', 'padding': '10px', 'backgroundColor': '#3498db', 'color': 'white', 'border': 'none', 'borderRadius': '4px', 'cursor': 'pointer'}),
                *[html.Button(topic, id=f'btn-{i}', n_clicks=0, style={'flex': '1', 'margin': '0 5px', 'padding': '10px', 'backgroundColor': '#ecf0f1', 'color': '#2c3e50', 'border': 'none', 'borderRadius': '4px', 'cursor': 'pointer'}) for i, topic in TOPIC_MAP.items()]
            ])
        ])
    ]),

    # 主图表区域
    html.Div(style={'display': 'flex', 'marginTop': '20px', 'gap': '25px', 'flexWrap': 'wrap'}, children=[
        # 面积图
        html.Div(style={'flex': '2', 'minWidth': '600px', 'padding': '20px', 'backgroundColor': 'white', 'borderRadius': '8px', 'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'}, children=[
            html.Div(style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '15px'}, children=[
                html.H3("主题热度趋势分析", style={'margin': '0', 'fontSize': '18px', 'color': '#2c3e50'}),
                html.Div(style={'display': 'flex', 'alignItems': 'center'}, children=[
                    html.Span("交互提示:", style={'marginRight': '10px', 'fontSize': '14px', 'color': '#7f8c8d'}),
                    html.I(className="fas fa-mouse-pointer", style={'marginRight': '5px'}),
                    html.Span("点击图例/图表切换主题", style={'fontSize': '14px'})
                ])
            ]),
            dcc.Graph(id='stacked-area-chart', style={'height': '400px'})
        ]),
        
        # 词云图
        html.Div(style={'flex': '1', 'minWidth': '400px', 'padding': '20px', 'backgroundColor': 'white', 'borderRadius': '8px', 'boxShadow': '0 2px 5px rgba(0,0,0,0.1)', 'position': 'relative'}, children=[
            html.Div(style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '15px'}, children=[
                html.H3(id='wordcloud-title', style={'margin': '0', 'fontSize': '18px', 'color': '#2c3e50'}),
                html.Button("暂停/播放", id='pause-button', n_clicks=0, style={'padding': '5px 10px', 'backgroundColor': '#3498db', 'color': 'white', 'border': 'none', 'borderRadius': '4px', 'cursor': 'pointer', 'fontSize': '12px'})
            ]),
            dcc.Interval(id='wordcloud-interval', interval=5*1000, n_intervals=0),
            html.Img(id='word-cloud-image', style={'width': '100%', 'height': 'auto', 'borderRadius': '4px'})
        ])
    ]),
    
    # 新闻表格区域
    html.Div(style={'marginTop': '30px', 'padding': '25px', 'backgroundColor': 'white', 'borderRadius': '8px', 'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'}, children=[
        html.Div(style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '15px'}, children=[
            html.H3(id='news-table-title', style={'margin': '0', 'fontSize': '18px', 'color': '#2c3e50'}),
            html.Div(style={'display': 'flex', 'alignItems': 'center'}, children=[
                html.Span("交互提示:", style={'marginRight': '10px', 'fontSize': '14px', 'color': '#7f8c8d'}),
                html.I(className="fas fa-sort", style={'marginRight': '5px'}),
                html.Span("点击列标题排序", style={'marginRight': '15px', 'fontSize': '14px'}),
                html.I(className="fas fa-filter", style={'marginRight': '5px'}),
                html.Span("点击表格筛选", style={'fontSize': '14px'})
            ])
        ]),
        dash_table.DataTable(
            id='news-table',
            columns=[
                {'name': '发布时间', 'id': 'time_str', 'type': 'datetime'},
                {'name': '新闻标题 (点击访问)', 'id': 'title_link', 'presentation': 'markdown'},
                {'name': '所属主题', 'id': 'topic_name'},
                {'name': '主题概率', 'id': 'probability', 'type': 'numeric', 'format': {'specifier': '.2%'}}
            ],
            style_cell={'textAlign': 'left', 'whiteSpace': 'normal', 'height': 'auto', 'padding': '12px', 'fontFamily': '"Segoe UI", Roboto, sans-serif', 'border': '1px solid #f0f0f0'},
            style_header={'fontWeight': '600', 'backgroundColor': '#f8f9fa', 'border': '1px solid #e0e0e0', 'textTransform': 'uppercase', 'fontSize': '14px'},
            style_data={'border': '1px solid #f0f0f0', 'fontSize': '14px'},
            style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': 'rgba(248, 248, 248, 0.7)'}],
            page_size=10, sort_action='native', filter_action='native', style_table={'overflowX': 'auto', 'borderRadius': '4px'}
        )
    ]),
    
    # 页脚
    html.Footer(style={'marginTop': '40px', 'padding': '15px', 'textAlign': 'center', 'color': '#7f8c8d', 'fontSize': '14px'}, children=[
        html.P(f"© 2025 新闻分析仪表盘 | 数据更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    ])
])

# ========================= 3. 定义交互逻辑 (回调函数) =========================

@app.callback(
    Output('pause-state-store', 'data'),
    Output('wordcloud-interval', 'disabled'),
    Output('pause-button', 'style'),
    Input('pause-button', 'n_clicks'),
    State('pause-state-store', 'data')
)
def toggle_pause_state(n_clicks, is_paused):
    if n_clicks == 0: # 初始加载时，按钮为“暂停”状态的颜色
        return False, False, {'padding': '5px 10px', 'backgroundColor': '#e74c3c', 'color': 'white', 'border': 'none', 'borderRadius': '4px', 'cursor': 'pointer', 'fontSize': '12px'}

    new_pause_state = not is_paused
    
    if new_pause_state:
        # 暂停状态，按钮显示为绿色（表示可“播放”）
        style = {'padding': '5px 10px', 'backgroundColor': '#2ecc71', 'color': 'white', 'border': 'none', 'borderRadius': '4px', 'cursor': 'pointer', 'fontSize': '12px'}
    else:
        # 播放状态，按钮显示为红色（表示可“暂停”）
        style = {'padding': '5px 10px', 'backgroundColor': '#e74c3c', 'color': 'white', 'border': 'none', 'borderRadius': '4px', 'cursor': 'pointer', 'fontSize': '12px'}
        
    return new_pause_state, new_pause_state, style

@app.callback(
    Output('current-topic-store', 'data'),
    Input('stacked-area-chart', 'clickData'),
    Input('btn-all', 'n_clicks'),
    Input('btn-1', 'n_clicks'),
    Input('btn-2', 'n_clicks'),
    Input('btn-3', 'n_clicks'),
    Input('wordcloud-interval', 'n_intervals'),
    State('current-topic-store', 'data'),
    State('pause-state-store', 'data')
)
def update_current_topic(clickData, btn_all, btn1, btn2, btn3, n_intervals, current_topic, is_paused):
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else 'initial_load'

    if triggered_id == 'stacked-area-chart' and clickData:
        return clickData['points'][0]['customdata'][0]
    elif triggered_id == 'btn-all':
        return None
    elif triggered_id in ['btn-1', 'btn-2', 'btn-3']:
        return TOPIC_MAP[int(triggered_id.split('-')[1])]
    elif triggered_id == 'wordcloud-interval' and not is_paused:
        # 轮播顺序: 全部 -> 人才培养 -> 基础科研 -> 技术创新 -> ...
        topic_list = [None] + list(TOPIC_MAP.values())
        try:
            current_index = topic_list.index(current_topic)
            next_index = (current_index + 1) % len(topic_list)
        except ValueError:
            next_index = 0
        return topic_list[next_index]
    else:
        return dash.no_update

@app.callback(
    Output('stacked-area-chart', 'figure'),
    Output('wordcloud-title', 'children'),
    Output('word-cloud-image', 'src'),
    Output('news-table-title', 'children'),
    Output('news-table', 'data'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'),
    Input('current-topic-store', 'data')
)
def update_dashboard(start_date, end_date, current_topic):
    dff_time_filtered = df[(df['time'] >= start_date) & (df['time'] <= end_date)]
    if current_topic:
        dff_final_filtered = dff_time_filtered[dff_time_filtered['topic_name'] == current_topic]
    else:
        dff_final_filtered = dff_time_filtered

    topic_counts = dff_time_filtered.groupby([dff_time_filtered['time'].dt.date, 'topic_name']).size().reset_index(name='count')
    area_fig = px.area(
        topic_counts, x='time', y='count', color='topic_name',
        labels={'time': '日期', 'count': '新闻数量', 'topic_name': '新闻主题'},
        custom_data=['topic_name'], color_discrete_sequence=['#3498db', '#2ecc71', '#e74c3c']
    )
    area_fig.update_layout(
        clickmode='event+select', legend_title_text='点击图例切换', hovermode='x unified',
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        margin={'l': 50, 'r': 30, 't': 30, 'b': 50},
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    area_fig.update_traces(hovertemplate='<b>%{customdata[0]}</b><br>日期: %{x|%Y-%m-%d}<br>数量: %{y}<extra></extra>', line=dict(width=2))

    all_keywords = [word for sublist in dff_final_filtered['keywords'] for word in sublist]
    wordcloud_title = f"“{current_topic}”主题核心词" if current_topic else "全部主题核心词"
    wordcloud_src = ""
    
    text_for_wordcloud = " ".join(all_keywords)

    if text_for_wordcloud:
        try:
            wc = WordCloud(
                font_path=SYSTEM_FONT_PATH, width=600, height=400, background_color=None,
                mode="RGBA", max_words=70, collocations=False, colormap='viridis'
            )
            wc.generate(text_for_wordcloud)
            img_buffer = io.BytesIO()
            wc.to_image().save(img_buffer, format='PNG')
            wordcloud_src = f"data:image/png;base64,{base64.b64encode(img_buffer.getvalue()).decode()}"
        except Exception as e:
            print(f"!!! 生成词云时出错: {e} !!!")

    dff_table = dff_final_filtered.copy().sort_values('time', ascending=False)
    table_title = f"“{current_topic}”主题相关新闻列表" if current_topic else "全部主题相关新闻列表"
    dff_table['time_str'] = dff_table['time'].dt.strftime('%Y-%m-%d %H:%M')
    dff_table['title_link'] = dff_table.apply(lambda row: f"[{row['title']}]({row['url']})", axis=1)
    columns_to_display = ['time_str', 'title_link', 'topic_name', 'probability']
    table_data = dff_table[columns_to_display].to_dict('records')

    return area_fig, wordcloud_title, wordcloud_src, table_title, table_data

# ========================= 4. 运行Dash应用 =========================
if __name__ == '__main__':
    app.run(debug=True)
