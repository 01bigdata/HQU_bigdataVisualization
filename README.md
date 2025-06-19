# 基于LDA的中国科技新闻主题分析与可视化

**项目简介**：本项目是一个针对中国科技新闻的大数据可视化课设，旨在通过自然语言处理（NLP）和数据可视化技术，深度挖掘新闻文本中的潜在主题和核心趋势。

**数据来源**：[中国经济网-科技频道](http.www.ce.cn/cysc/tech/)

---

## 核心功能与可视化展示

1.  **交互式仪表盘**：基于 `Dash` 和 `Pyecharts` 构建，集成了动态趋势图、关键词云和新闻详情表。
2.  **LDA主题模型分析**：利用 `Gensim` 和 `pyLDAvis` 自动从文本中发现隐藏的主题，并提供交互式可视化报告，直观展示主题-词汇分布和主题关联度。
3.  **词语共现网络**：通过构建词语共现矩阵，使用 `NetworkX` 或 `Pyecharts` 可视化高频关键词之间的关联强度与网络结构。
4.  **多维度图表**：包括词云图、热力图、总体词频分布图等，全面展示数据特征。

*(你可以在这里插入你的可视化截图)*
*![仪表盘截图](![image](https://github.com/user-attachments/assets/9d931561-ea8b-4946-afe6-f481369a9770)
)*

---

## 技术架构与核心流程

![项目流程图](https://via.placeholder.com/900x150.png?text=Data+Crawling+->+Preprocessing+->+LDA+Topic+Modeling+->+Interactive+Visualization)

1.  **数据采集**：编写爬虫脚本，自动化采集中国经济网特定时间范围内的科技新闻标题、时间和内容。
2.  **数据预处理**: 对原始文本进行清洗（如去HTML标签、特殊字符），使用 `jieba` 进行中文分词，并结合自定义词典和停用词表，提升分词准确性。
3.  **主题建模与分析 (LDA)**:
    * **确定最佳主题数(K)**: 通过计算不同 K 值下的**主题一致性得分 (C_v Score)**，绘制折线图找到最优的主题数量。
    * **模型训练**: 使用确定的 K 值训练最终的 LDA 模型。
    * **结果可视化**: 生成可交互的 `pyLDAvis` 报告，用于深入分析主题。
4.  **特征工程与关联分析**:
    * **TF-IDF**: 计算关键词的 TF-IDF 值，衡量其重要性。
    * **词语共现网络**: 在特定窗口大小（如 10）内统计词语共现频率和提升度，构建关联网络。超参数包括：最小词频 `MIN_FREQUENCY=5`，关联对数量 `TOP_N=50` 等。
5.  **前端可视化呈现**:
    * 使用 `Dash` 框架搭建 Web 应用的整体布局。
    -   利用 `Pyecharts` 或 `Plotly` 生成交互式图表，嵌入到 Dash 仪表盘中。

---

## 环境配置

-   **操作系统**：Windows 11 / Linux / macOS
-   **Python 版本**：`3.10` 或更高版本

项目的主要依赖库已在 `requirements.txt` 中列出。请使用以下命令安装：

```bash
pip install -r requirements.txt
```

**`requirements.txt` 核心内容应包括:**

```text
Pillow==11.2.1
dash==3.0.4
gensim==4.3.3
jieba==0.42.1
matplotlib==3.8.3
networkx==3.4.2
numpy==1.26.0
pandas==1.5.3
plotly==6.1.2
pyecharts==2.0.8
pyldavis==3.4.1
pyvis==0.3.2
scikit-learn==1.4.1.post1
seaborn==0.13.2
selenium==4.26.1
webdriver-manager==4.0.2
wordcloud==1.9.4
```

---

## 如何运行

1.  **克隆项目**
    ```bash
    git clone [https://github.com/your-username/HQU_bigdataVisualization.git](https://github.com/your-username/HQU_bigdataVisualization.git)
    cd HQU_bigdataVisualization
    ```

2.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    ```

3.  **执行数据分析与建模 (Jupyter)**
    -   本项目的数据探索、预处理和模型训练过程主要在 Jupyter Notebooks (`.ipynb` 文件) 中完成。
    -   建议您按照 Notebook 的顺序依次运行，以复现完整的分析流程。
    -   如果需要重新爬取数据，请运行对应的数据采集脚本。

4.  **启动可视化仪表盘**
    -   运行最终的 Dash 应用文件来启动交互式Web仪表盘。
    ```bash
    python final_result.py 
    ```
    *注意：请将 `final_result.py` 替换为您实际的启动文件名。*

---

## 未来工作

-   [ ] 修复当前最终版仪表盘 (`final_result.py`) 中存在的报错问题。
-   [ ] 将 Jupyter Notebook 中的核心代码重构为模块化的 `.py` 脚本，提高复用性。
-   [ ] 增加更多维度的可视化分析，例如情感分析、时间序列预测等。
