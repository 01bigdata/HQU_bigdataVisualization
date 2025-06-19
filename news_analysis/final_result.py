import pandas as pd
import json
import jieba
import io
import base64
from wordcloud import WordCloud
from collections import Counter
import sys
from datetime import datetime
import matplotlib.font_manager as fm
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.graph_objects as go

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
TOPIC_COLORS = {
    "人才培养": "#3498db",
    "基础科研": "#2ecc71",
    "技术创新": "#e74c3c",
    "全部主题": "#9b59b6"
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
external_stylesheets = [
    {'href': 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css', 'rel': 'stylesheet'},
    {'href': 'https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&display=swap', 'rel': 'stylesheet'}
]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
app.title = "新闻主题动态分析仪表盘"

min_date = df['time'].min().date()
max_date = df['time'].max().date()

# 卡片式链接样式
card_container_style = {
    'display': 'flex',
    'justifyContent': 'space-around',
    'gap': '20px',
    'flexWrap': 'wrap',
    'margin': '20px 0'
}

card_style = {
    'flex': '1',
    'minWidth': '300px',
    'padding': '25px',
    'textAlign': 'center',
    'backgroundColor': '#ffffff',
    'borderRadius': '12px',
    'boxShadow': '0 6px 15px rgba(0,0,0,0.08)',
    'transition': 'all 0.3s ease',
    'display': 'flex',
    'flexDirection': 'column',
    'justifyContent': 'space-between',
    'borderTop': '4px solid #3498db',
    'position': 'relative',
    'overflow': 'hidden'
}

card_hover_style = {
    'transform': 'translateY(-5px)',
    'boxShadow': '0 12px 20px rgba(0,0,0,0.12)'
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
    'borderRadius': '25px',
    'textDecoration': 'none',
    'cursor': 'pointer',
    'transition': 'all 0.3s ease',
    'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'
}

card_button_hover_style = {
    'backgroundColor': '#2980b9',
    'transform': 'translateY(-2px)',
    'boxShadow': '0 4px 8px rgba(0,0,0,0.15)'
}

app.layout = html.Div(style={
    'fontFamily': '"Noto Sans SC", "Segoe UI", Roboto, sans-serif',
    'padding': '20px 40px',
    'backgroundColor': '#f8f9fa',
    'minHeight': '100vh'
}, children=[
    dcc.Store(id='current-topic-store', data=None),
    dcc.Store(id='pause-state-store', data=False),

    # 顶部标题栏
    html.Div(style={
        'background': 'linear-gradient(135deg, #2c3e50, #3498db)',
        'padding': '30px',
        'borderRadius': '12px',
        'marginBottom': '30px',
        'boxShadow': '0 8px 15px rgba(0,0,0,0.15)',
        'color': 'white',
        'position': 'relative',
        'overflow': 'hidden'
    }, children=[
        html.Div(style={
            'position': 'absolute',
            'top': '-50px',
            'right': '-50px',
            'width': '200px',
            'height': '200px',
            'backgroundColor': 'rgba(255,255,255,0.1)',
            'borderRadius': '50%'
        }),
        html.Div(style={
            'position': 'absolute',
            'bottom': '-80px',
            'left': '-30px',
            'width': '150px',
            'height': '150px',
            'backgroundColor': 'rgba(255,255,255,0.1)',
            'borderRadius': '50%'
        }),
        html.H1("新闻主题热度与关键词动态分析仪表盘", style={
            'textAlign': 'center',
            'marginBottom': '10px',
            'fontWeight': '700',
            'fontSize': '32px',
            'textShadow': '0 2px 4px rgba(0,0,0,0.2)'
        }),
        html.P("实时监测三大主题发展趋势与核心关键词", style={
            'textAlign': 'center',
            'fontSize': '16px',
'opacity': '0.9',
            'marginBottom': '0'
        })
    ]),

    # 外部可视化报告链接区域
    html.Div([
        html.H2("拓展分析报告", style={
            'textAlign': 'center',
            'color': '#2c3e50',
            'marginBottom': '25px',
            'fontWeight': '600',
            'position': 'relative',
            'paddingBottom': '10px'
        }),
        html.Div(style={
            'position': 'absolute',
            'left': '50%',
            'transform': 'translateX(-50%)',
            'bottom': '0',
            'width': '80px',
            'height': '3px',
            'backgroundColor': '#3498db',
            'borderRadius': '3px'
        }),
        html.Div([
            # 卡片1: 共现网络
            html.Div([
                html.Div([
                    html.Div(style={
                        'width': '60px',
                        'height': '60px',
                        'backgroundColor': 'rgba(52, 152, 219, 0.1)',
                        'borderRadius': '50%',
                        'display': 'flex',
                        'alignItems': 'center',
                        'justifyContent': 'center',
                        'margin': '0 auto 15px'
                    }, children=[
                        html.I(className="fas fa-project-diagram", style={
                            'fontSize': '24px',
                            'color': '#3498db'
                        })
                    ]),
                    html.H5("词语共现网络图", style={
                        'color': '#34495e',
                        'margin': '0 0 10px 0',
                        'fontWeight': '600'
                    }),
                    html.P("探索高频词汇之间的关联强度与网络结构。", style={
                        'fontSize': '14px',
                        'color': '#7f8c8d',
                        'lineHeight': '1.6',
                        'marginBottom': '0'
                    }),
                ]),
                html.A("点击查看", href="/assets/word_co-occurrence_network_warm_theme.html", 
                       target="_blank", style=card_button_style,
                       id='card-button-1')
            ], style=card_style, id='card-1'),
            
            # 卡片2: LDA主题模型
            html.Div([
                html.Div([
                    html.Div(style={
                        'width': '60px',
                        'height': '60px',
                        'backgroundColor': 'rgba(46, 204, 113, 0.1)',
                        'borderRadius': '50%',
                        'display': 'flex',
                        'alignItems': 'center',
                        'justifyContent': 'center',
                        'margin': '0 auto 15px'
                    }, children=[
                        html.I(className="fas fa-chart-pie", style={
                            'fontSize': '24px',
                            'color': '#2ecc71'
                        })
                    ]),
                    html.H5("LDA主题模型分析", style={
                        'color': '#34495e',
                        'margin': '0 0 10px 0',
                        'fontWeight': '600'
                    }),
                    html.P("从文本数据中自动发现隐藏的主题分布与关键特征词。", style={
                        'fontSize': '14px',
                        'color': '#7f8c8d',
                        'lineHeight': '1.6',
                        'marginBottom': '0'
                    }),
                ]),
                html.A("点击查看", href="/assets/lda_visualization_final_k3.html", 
                       target="_blank", style=card_button_style,
                       id='card-button-2')
            ], style=card_style, id='card-2'),
            
            # 卡片3: 总体分析仪表盘
            html.Div([
                html.Div([
                    html.Div(style={
                        'width': '60px',
                        'height': '60px',
                        'backgroundColor': 'rgba(155, 89, 182, 0.1)',
                        'borderRadius': '50%',
                        'display': 'flex',
                        'alignItems': 'center',
                        'justifyContent': 'center',
                        'margin': '0 auto 15px'
                    }, children=[
                        html.I(className="fas fa-tachometer-alt", style={
                            'fontSize': '24px',
                            'color': '#9b59b6'
                        })
                    ]),
                    html.H5("新闻数据总体分析", style={
                        'color': '#34495e',
                        'margin': '0 0 10px 0',
                        'fontWeight': '600'
                    }),
                    html.P("一个包含多维度图表的交互式可视化仪表盘。", style={
                        'fontSize': '14px',
                        'color': '#7f8c8d',
                        'lineHeight': '1.6',
                        'marginBottom': '0'
                    }),
                ]),
                html.A("点击查看", href="/assets/data_visualization_dashboard.html", 
                       target="_blank", style=card_button_style,
                       id='card-button-3')
            ], style=card_style, id='card-3'),
        ], style=card_container_style)
    ], style={
        'padding': '30px',
        'marginBottom': '30px',
        'backgroundColor': 'white',
        'borderRadius': '12px',
        'boxShadow': '0 5px 15px rgba(0,0,0,0.05)'
    }),

    # 控制面板区域
    html.Div(style={
        'display': 'flex',
        'justifyContent': 'space-between',
        'marginBottom': '30px',
        'flexWrap': 'wrap',
        'gap': '20px'
    }, children=[
        # 日期选择器
        html.Div(style={
            'flex': '1',
            'minWidth': '300px',
            'padding': '25px',
            'backgroundColor': 'white',
            'borderRadius': '12px',
            'boxShadow': '0 5px 15px rgba(0,0,0,0.05)',
            'position': 'relative',
            'overflow': 'hidden'
        }, children=[
            html.Div(style={
                'position': 'absolute',
                'top': '0',
                'left': '0',
                'width': '5px',
                'height': '100%',
                'backgroundColor': '#3498db'
            }),
            html.H4(style={
                'marginBottom': '20px',
                'color': '#2c3e50',
                'display': 'flex',
                'alignItems': 'center',
                'fontWeight': '600'
            }, children=[
                html.I(className="far fa-calendar-alt", style={
                    'marginRight': '10px',
                    'color': '#3498db',
                    'fontSize': '20px'
                }),
                "请选择分析的时间范围:"
            ]),
            dcc.DatePickerRange(
                id='date-picker-range',
                min_date_allowed=min_date,
                max_date_allowed=max_date,
                start_date=min_date,
                end_date=max_date,
                display_format='YYYY-MM-DD',
                style={'width': '100%'},
                className='custom-date-picker'
            )
        ]),
        
        # 主题切换按钮组
        html.Div(style={
            'flex': '1',
            'minWidth': '300px',
            'padding': '25px',
            'backgroundColor': 'white',
            'borderRadius': '12px',
            'boxShadow': '0 5px 15px rgba(0,0,0,0.05)',
            'position': 'relative',
            'overflow': 'hidden'
        }, children=[
            html.Div(style={
                'position': 'absolute',
                'top': '0',
                'left': '0',
                'width': '5px',
                'height': '100%',
                'backgroundColor': '#e74c3c'
            }),
            html.H4(style={
                'marginBottom': '20px',
                'color': '#2c3e50',
                'display': 'flex',
                'alignItems': 'center',
                'fontWeight': '600'
            }, children=[
                html.I(className="fas fa-tags", style={
                    'marginRight': '10px',
                    'color': '#e74c3c',
                    'fontSize': '20px'
                }),
                "点击按钮快速切换主题:"
            ]),
            html.Div(style={
                'display': 'flex',
                'justifyContent': 'space-between',
                'flexWrap': 'wrap',
                'gap': '10px'
            }, children=[
                html.Button("全部主题", id='btn-all', n_clicks=0, style={
                    'flex': '1',
                    'minWidth': '120px',
                    'padding': '12px',
                    'backgroundColor': '#9b59b6',
                    'color': 'white',
                    'border': 'none',
                    'borderRadius': '8px',
                    'cursor': 'pointer',
                    'fontWeight': '500',
                    'transition': 'all 0.3s ease',
                    'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'
                }),
                *[html.Button(topic, id=f'btn-{i}', n_clicks=0, style={
                    'flex': '1',
                    'minWidth': '120px',
                    'padding': '12px',
                    'backgroundColor': TOPIC_COLORS[topic],
                    'color': 'white',
                    'border': 'none',
                    'borderRadius': '8px',
                    'cursor': 'pointer',
                    'fontWeight': '500',
                    'transition': 'all 0.3s ease',
                    'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'
                }) for i, topic in TOPIC_MAP.items()]
            ])
        ])
    ]),

    # 主图表区域
    html.Div(style={
        'display': 'flex',
        'marginTop': '20px',
        'gap': '30px',
        'flexWrap': 'wrap'
    }, children=[
        # 面积图
        html.Div(style={
            'flex': '2',
            'minWidth': '600px',
            'padding': '25px',
            'backgroundColor': 'white',
            'borderRadius': '12px',
            'boxShadow': '0 5px 15px rgba(0,0,0,0.05)',
            'position': 'relative'
        }, children=[
            html.Div(style={
                'display': 'flex',
                'justifyContent': 'space-between',
                'alignItems': 'center',
                'marginBottom': '20px'
            }, children=[
                html.H3("主题热度趋势分析", style={
                    'margin': '0',
                    'fontSize': '20px',
                    'color': '#2c3e50',
                    'fontWeight': '600'
                }),
                html.Div(style={
                    'display': 'flex',
                    'alignItems': 'center',
                    'backgroundColor': '#f8f9fa',
                    'padding': '8px 12px',
                    'borderRadius': '6px'
                }, children=[
                    html.I(className="fas fa-info-circle", style={
                        'marginRight': '8px',
                        'color': '#3498db'
                    }),
                    html.Span("点击图例或图表切换主题", style={
                        'fontSize': '14px',
                        'color': '#7f8c8d'
                    })
                ])
            ]),
            dcc.Graph(id='stacked-area-chart', style={'height': '400px'})
        ]),
        
        # 词云图
        html.Div(style={
            'flex': '1',
            'minWidth': '400px',
            'padding': '25px',
            'backgroundColor': 'white',
            'borderRadius': '12px',
            'boxShadow': '0 5px 15px rgba(0,0,0,0.05)',
            'position': 'relative'
        }, children=[
            html.Div(style={
                'display': 'flex',
                'justifyContent': 'space-between',
                'alignItems': 'center',
                'marginBottom': '20px'
            }, children=[
                html.H3(id='wordcloud-title', style={
                    'margin': '0',
                    'fontSize': '20px',
                    'color': '#2c3e50',
                    'fontWeight': '600'
                }),
                html.Button(
                    "暂停轮播",
                    id='pause-button',
                    n_clicks=0,
                    style={
                        'padding': '10px 15px',
                        'backgroundColor': '#e74c3c',
                        'color': 'white',
                        'border': 'none',
                        'borderRadius': '8px',
                        'cursor': 'pointer',
                        'fontWeight': '500',
                        'transition': 'all 0.3s ease',
                        'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'
                    }
                )
            ]),
            dcc.Interval(id='wordcloud-interval', interval=5*1000, n_intervals=0),
            html.Div(style={
                'width': '100%',
                'height': '400px',
                'display': 'flex',
                'alignItems': 'center',
                'justifyContent': 'center',
                'backgroundColor': '#f8f9fa',
                'borderRadius': '8px',
                'overflow': 'hidden'
            }, children=[
                html.Img(
                    id='word-cloud-image',
                    style={
                        'width': '100%',
                        'height': 'auto',
                        'objectFit': 'contain',
                        'transition': 'opacity 0.5s ease'
                    }
                )
            ])
        ])
    ]),
    
    # 新闻表格区域
    html.Div(style={
        'marginTop': '30px',
        'padding': '30px',
        'backgroundColor': 'white',
        'borderRadius': '12px',
        'boxShadow': '0 5px 15px rgba(0,0,0,0.05)',
        'position': 'relative'
    }, children=[
        html.Div(style={
            'display': 'flex',
            'justifyContent': 'space-between',
            'alignItems': 'center',
            'marginBottom': '20px'
        }, children=[
            html.H3(id='news-table-title', style={
                'margin': '0',
'fontSize': '20px',
                'color': '#2c3e50',
                'fontWeight': '600'
            }),
            html.Div(style={
                'display': 'flex',
                'alignItems': 'center',
                'backgroundColor': '#f8f9fa',
                'padding': '8px 12px',
                'borderRadius': '6px'
            }, children=[
                html.I(className="fas fa-info-circle", style={
                    'marginRight': '8px',
                    'color': '#3498db'
                }),
                html.Span("点击标题可访问原文 | 支持排序和筛选", style={
                    'fontSize': '14px',
                    'color': '#7f8c8d'
                })
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
            style_cell={
                'textAlign': 'left',
                'whiteSpace': 'normal',
                'height': 'auto',
                'padding': '15px',
                'fontFamily': '"Noto Sans SC", Roboto, sans-serif',
                'border': '1px solid #f0f0f0',
                'fontSize': '14px'
            },
            style_header={
                'fontWeight': '600',
                'backgroundColor': '#f8f9fa',
                'border': '1px solid #e0e0e0',
                'textTransform': 'uppercase',
                'fontSize': '14px',
                'color': '#2c3e50'
            },
            style_data={
                'border': '1px solid #f0f0f0',
                'fontSize': '14px',
                'color': '#34495e'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgba(248, 248, 248, 0.7)'
                },
                {
                    'if': {'column_id': 'probability'},
                    'textAlign': 'center'
                },
                {
                    'if': {'column_id': 'title_link'},
                    'color': '#3498db',
                    'textDecoration': 'underline',
                    'cursor': 'pointer'
                }
            ],
            page_size=10,
            sort_action='native',
            filter_action='native',
            style_table={
                'overflowX': 'auto',
                'borderRadius': '8px',
                'border': '1px solid #f0f0f0'
            },
            style_filter={
                'backgroundColor': '#f8f9fa',
                'padding': '10px'
            }
        )
    ]),
    
    # 页脚
    html.Footer(style={
        'marginTop': '40px',
        'padding': '20px',
        'textAlign': 'center',
        'color': '#7f8c8d',
        'fontSize': '14px',
        'backgroundColor': 'white',
        'borderRadius': '12px',
        'boxShadow': '0 5px 15px rgba(0,0,0,0.05)'
    }, children=[
        html.P(f"© 2025 新闻分析仪表盘 | 数据更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", style={
            'margin': '0'
        })
    ])
])

# ========================= 3. 定义交互逻辑 (回调函数) =========================

# 卡片悬停效果
app.clientside_callback(
    """
    function(hoverData, cardId) {
        if (hoverData) {
            return Object.assign({}, card_style, card_hover_style);
        } else {
            return card_style;
        }
    }
    """,
    [Output('card-1', 'style'),
     Output('card-2', 'style'),
     Output('card-3', 'style')],
    [Input('card-1', 'n_events'),
     Input('card-2', 'n_events'),
     Input('card-3', 'n_events')],
    prevent_initial_call=True
)

app.clientside_callback(
    """
    function(hoverData, buttonId) {
        if (hoverData) {
            return Object.assign({}, card_button_style, card_button_hover_style);
        } else {
            return card_button_style;
        }
    }
    """,
    [Output('card-button-1', 'style'),
     Output('card-button-2', 'style'),
     Output('card-button-3', 'style')],
    [Input('card-button-1', 'n_events'),
     Input('card-button-2', 'n_events'),
     Input('card-button-3', 'n_events')],
    prevent_initial_call=True
)

# 暂停/播放按钮逻辑
@app.callback(
    Output('pause-state-store', 'data'),
    Output('wordcloud-interval', 'disabled'),
    Output('pause-button', 'style'),
    Input('pause-button', 'n_clicks'),
    State('pause-state-store', 'data')
)
def toggle_pause_state(n_clicks, is_paused):
    if n_clicks == 0:
        return False, False, {
            'padding': '10px 15px',
            'backgroundColor': '#e74c3c',
            'color': 'white',
            'border': 'none',
            'borderRadius': '8px',
            'cursor': 'pointer',
            'fontWeight': '500',
            'transition': 'all 0.3s ease',
            'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'
        }

    new_pause_state = not is_paused
    
    if new_pause_state:
        style = {
            'padding': '10px 15px',
            'backgroundColor': '#2ecc71',
            'color': 'white',
            'border': 'none',
            'borderRadius': '8px',
            'cursor': 'pointer',
            'fontWeight': '500',
            'transition': 'all 0.3s ease',
            'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'
        }
    else:
        style = {
            'padding': '10px 15px',
            'backgroundColor': '#e74c3c',
            'color': 'white',
            'border': 'none',
            'borderRadius': '8px',
            'cursor': 'pointer',
            'fontWeight': '500',
            'transition': 'all 0.3s ease',
            'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'
        }
        
    return new_pause_state, new_pause_state, style

# 主题切换逻辑
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
        topic_list = [None] + list(TOPIC_MAP.values())
        try:
            current_index = topic_list.index(current_topic)
            next_index = (current_index + 1) % len(topic_list)
        except ValueError:
            next_index = 0
        return topic_list[next_index]
    else:
        return dash.no_update

# 主仪表盘更新逻辑
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

    # 1. 更新面积图
    topic_counts = dff_time_filtered.groupby([dff_time_filtered['time'].dt.date, 'topic_name']).size().reset_index(name='count')
    
    area_fig = go.Figure()
    for topic in TOPIC_MAP.values():
        topic_data = topic_counts[topic_counts['topic_name'] == topic]
        area_fig.add_trace(go.Scatter(
            x=topic_data['time'],
            y=topic_data['count'],
            mode='lines',
            stackgroup='one',
            name=topic,
            line=dict(width=2, color=TOPIC_COLORS[topic]),
            fill='tonexty',
            hovertemplate=f'<b>{topic}</b><br>日期: %{{x|%Y-%m-%d}}<br>数量: %{{y}}<extra></extra>',
            customdata=[[topic]] * len(topic_data)
        ))
    
    area_fig.update_layout(
        clickmode='event+select',
        legend_title_text='点击图例切换',
        hovermode='x unified',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin={'l': 50, 'r': 30, 't': 30, 'b': 50},
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
            bgcolor='rgba(255,255,255,0.7)',
            bordercolor='rgba(0,0,0,0.1)',
            borderwidth=1
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            title='日期'
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            title='新闻数量'
        )
    )

    # 2. 更新词云图
    all_keywords = [word for sublist in dff_final_filtered['keywords'] for word in sublist]
    wordcloud_title = f"「{current_topic}」主题核心词" if current_topic else "「全部主题」核心词"
    wordcloud_src = ""
    
    text_for_wordcloud = " ".join(all_keywords)

    if text_for_wordcloud:
        try:
            wc = WordCloud(
                font_path=SYSTEM_FONT_PATH,
                width=800,
                height=500,
                background_color=None,
                mode="RGBA",
                max_words=100,
                collocations=False,
                colormap='viridis',
                prefer_horizontal=0.9,
                relative_scaling=0.5
            )
            wc.generate(text_for_wordcloud)
            img_buffer = io.BytesIO()
            wc.to_image().save(img_buffer, format='PNG')
            wordcloud_src = f"data:image/png;base64,{base64.b64encode(img_buffer.getvalue()).decode()}"
        except Exception as e:
            print(f"!!! 生成词云时出错: {e} !!!")

    # 3. 更新新闻表格
    dff_table = dff_final_filtered.copy().sort_values('time', ascending=False)
    table_title = f"「{current_topic}」主题相关新闻列表" if current_topic else "全部主题相关新闻列表"
    dff_table['time_str'] = dff_table['time'].dt.strftime('%Y-%m-%d %H:%M')
    dff_table['title_link'] = dff_table.apply(lambda row: f"[{row['title']}]({row['url']})", axis=1)
    columns_to_display = ['time_str', 'title_link', 'topic_name', 'probability']
    table_data = dff_table[columns_to_display].to_dict('records')

    return area_fig, wordcloud_title, wordcloud_src, table_title, table_data

# ========================= 4. 运行Dash应用 =========================
if __name__ == '__main__':
    app.run(debug=True, dev_tools_ui=True, dev_tools_hot_reload=True)