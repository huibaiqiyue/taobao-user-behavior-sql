# 淘宝用户行为数据分析 — SQL + Power BI 版

基于500万+条淘宝用户行为数据，MySQL分析 + Power BI交互式可视化。

&gt; Python(Pandas)版：[点击查看](http://github.com/huibaiqiyue/taobao-user-behavior-analysis)  
&gt; CSDN详细报告：[点击查看](你的CSDN链接)

---

## 核心结论

| 指标 | 结果 |
|:---|:---|
| 总数据量 | 5,000,007 条 |
| 加购→购买流失率 | **46.5%**（核心瓶颈） |
| 收藏→购买转化率 | 28.1% |
| 购买用户占比 | 67.7% |

---

## 技术栈

- MySQL 8.0（数据存储、复杂查询）
- Python + SQLAlchemy（数据导入）
- Power BI Desktop（可视化看板）

---

## 文件说明

| 文件 | 内容 |
|:---|:---|
| `src/data_import.py` | parquet → MySQL 批量导入脚本 |
| `docs/SQL查询.docx` | 5组分析查询（漏斗、分层、趋势） |
| `assets/powerbi_dashboard.png` | 可视化看板截图 |

---

## 快速开始

```bash
# 安装依赖
pip install pandas sqlalchemy pymysql pyarrow

# 导入数据（修改密码后执行）
python src/data_import.py
