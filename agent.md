# Agent 工作说明

本项目是一个数理统计课程项目，主题聚焦于胡塞武装/红海危机事件与红海关键航道通行量、绕航行为之间的统计关系。当前代码主要完成数据下载、数据整理和初步真实数据分析，算法与论文部分仍在完善中。

## 执行环境优先级

后续执行脚本、测试或分析时，优先在 WSL 中使用 conda 的 `Prob` 环境，不要优先使用 Windows 侧 Python。

推荐命令模板：

```bash
cd /mnt/e/python/prob
/home/kelvin2005/anaconda3/bin/conda run --no-capture-output -n Prob python -u <script>
```

常用示例：

```bash
cd /mnt/e/python/prob
/home/kelvin2005/anaconda3/bin/conda run --no-capture-output -n Prob python -u scripts/run_analysis_real.py
```

如需下载 PortWatch 数据：

```bash
cd /mnt/e/python/prob
/home/kelvin2005/anaconda3/bin/conda run --no-capture-output -n Prob python -u scripts/download_portwatch.py --start-date 2023-10-01 --batch-size 500 --delay-seconds 1
```

如需下载 ACLED 数据：

```bash
cd /mnt/e/python/prob
/home/kelvin2005/anaconda3/bin/conda run --no-capture-output -n Prob python -u scripts/download_acled.py
```

## 项目结构

```text
.
├── readme.md
├── diary.md
├── data/
│   ├── acled_API.json
│   ├── Middle-East_aggregated_data_up_to_week_of-2026-05-09.xlsx
│   ├── acled_data/
│   └── portwatch/
├── docs/
│   ├── acled_data_overview.md
│   ├── aishub_collection.md
│   ├── current_data.md
│   └── portwatch_data.md
├── references/
│   ├── T7_T11_T15_detailed_guide.pdf
│   ├── topic_selection_guide.pdf
│   └── 数理统计_完整选题手册.docx
└── scripts/
    ├── collect_aishub.py
    ├── download_acled.py
    ├── download_portwatch.py
    ├── run_analysis_real.py
    └── sample_data.py
```

## 关键文件说明

- `readme.md`：项目简要说明，当前仍偏草稿。
- `docs/current_data.md`：最重要的项目现状说明，包含已有数据、可支持研究问题、推荐统计方法和下一步建议。
- `docs/acled_data_overview.md`：ACLED 数据采集范围、筛选规则、字段结构和复现命令。
- `docs/portwatch_data.md`：PortWatch/PortStraitWatch 航道通行指标说明和下载命令。
- `docs/aishub_collection.md`：AISHub 实时 AIS 采集说明。当前 AIS 历史数据不足，不适合作为主要因果分析数据源。
- `scripts/run_analysis_real.py`：读取真实 ACLED 与 PortWatch 数据，做周度聚合、VAR 脉冲响应、分船型 OLS + Newey-West 回归。
- `scripts/download_acled.py`：ACLED 数据下载与关键词筛选脚本。
- `scripts/download_portwatch.py`：PortWatch chokepoint 日度通行数据下载与派生指标生成脚本。
- `scripts/collect_aishub.py`：AISHub 近实时 AIS 快照采集脚本。

## 当前数据主线

当前项目适合完成聚合层面的统计分析：

```text
胡塞武装袭击对红海关键航道通行量与绕航行为的统计分析
```

推荐核心数据组合：

```text
ACLED 胡塞/红海相关事件数据
+
PortWatch Suez Canal / Bab el-Mandeb / Cape of Good Hope 日度通行指标
```

推荐因变量：

```text
bab_el_mandeb_n_total
suez_n_total
cape_good_hope_n_total
rerouting_index_total
suez_share_total
```

推荐解释变量：

```text
attack_count_acled
explosion_count_acled
battle_count_acled
fatalities_acled
post_red_sea_crisis
```

## 数据与安全注意事项

- `data/acled_API.json` 包含 ACLED API token，视为敏感文件，不要公开、粘贴或提交到公共仓库。
- AISHub 用户名不要写入代码，应通过环境变量 `AISHUB_USERNAME` 或命令行参数传入。
- `data/aishub/raw/` 可能快速增长，长期采集前需要确认存储和忽略规则。
- 当前历史 AIS 数据缺失，因此不要把研究结论写成“AIS 开关对单船遇袭风险的因果影响”。更稳妥的表述是“胡塞相关事件与航运通行量、绕航行为的统计关联”。
- 工作区已有若干未提交改动，后续 agent 不应擅自回滚用户改动。

## 建议下一步

1. 从 ACLED 筛选数据构造日度事件表，区分 `Explosions/Remote violence`、`Battles`、`Violence against civilians`、`Strategic developments` 等事件类型。
2. 与 `data/portwatch/portwatch_red_sea_analysis.csv` 按日期合并。
3. 绘制袭击事件数、Bab el-Mandeb、Suez、Cape of Good Hope、绕航指数的时间序列图。
4. 完成事件研究、中断时间序列或周度回归模型，并使用 Newey-West 标准误处理时间序列自相关。
5. 在论文中明确写出 AIS 历史数据不足、ACLED 关键词筛选可能误筛/漏筛、PortWatch 是聚合指标等限制。
