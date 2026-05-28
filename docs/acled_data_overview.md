# ACLED 数据收集说明

生成时间：2026-05-28

本文档说明当前项目中已收集的 ACLED 数据文件、采集范围、筛选规则和目录结构。

## 1. 目录结构

项目根目录按用途分为四类：

| 目录 | 用途 |
| --- | --- |
| `scripts/` | Python 脚本 |
| `data/` | API token、下载数据、聚合数据 |
| `docs/` | 项目说明文档 |
| `references/` | PDF、Word 等参考资料 |

当前主要文件：

| 文件 | 说明 |
| --- | --- |
| `scripts/download_acled.py` | ACLED 数据下载和本地关键词筛选脚本 |
| `scripts/sample_data.py` | ACLED API 测试脚本 |
| `data/acled_API.json` | ACLED API token 缓存，包含敏感令牌 |
| `data/Middle-East_aggregated_data_up_to_week_of-2026-05-09.xlsx` | ACLED 中东聚合数据 |
| `references/T7_T11_T15_detailed_guide.pdf` | T7/T11/T15 详细技术指南 |
| `references/topic_selection_guide.pdf` | 数理统计大作业选题分类指南 |
| `references/数理统计_完整选题手册.docx` | 数理统计完整选题手册 |

## 2. 已下载数据

下载结果保存在 `data/acled_data/` 目录下：

| 文件 | 行数 | 说明 |
| --- | ---: | --- |
| `data/acled_data/red_sea_yemen_candidate_2023_plus.csv` | 35,429 | 2023-01-01 至 2026-05-28 请求范围内的候选数据 |
| `data/acled_data/red_sea_yemen_houthi_related_2023_plus_limit30000.csv` | 22,688 | 对 2023+ 候选数据做关键词筛选后的结果，`limit=30000` |
| `data/acled_data/red_sea_yemen_candidate_2025-05-28_to_present.csv` | 18 | 2025-05-28 至 2026-05-28 请求范围内的候选数据 |
| `data/acled_data/red_sea_yemen_houthi_related_2025-05-28_to_present.csv` | 10 | 对 2025-05-28 至今候选数据做关键词筛选后的结果 |
| `data/acled_data/download_scope_metadata_limit30000.json` | - | 2023+、`limit=30000` 下载元数据 |
| `data/acled_data/download_scope_metadata_2025-05-28_to_present.json` | - | 2025-05-28 至今下载元数据 |

## 3. API 采集范围

当前 `scripts/download_acled.py` 的默认设置为收集 `2025-05-28` 至当前日期的数据。

| 参数 | 当前值 |
| --- | --- |
| `_format` | `json` |
| `event_date` | `2025-05-28|2026-05-28` |
| `event_date_where` | `BETWEEN` |
| `limit` | `30000` |
| `page` | 从 `1` 开始分页 |
| `with_total` | 未启用 |

逐个查询的 `country` 范围：

- `Yemen`
- `Saudi Arabia`
- `Oman`
- `Djibouti`
- `Eritrea`
- `Somalia`
- `Indian Ocean`
- `Red Sea`
- `Gulf of Aden`

## 4. 本地筛选规则

脚本先下载候选范围内的数据，再在本地做关键词筛选。

搜索字段：

- `actor1`
- `actor2`
- `assoc_actor_1`
- `assoc_actor_2`
- `location`
- `admin1`
- `admin2`
- `admin3`
- `notes`
- `tags`

关键词：

- `Houthi`
- `Houthis`
- `Ansar Allah`
- `Ansarallah`
- `Red Sea`
- `Gulf of Aden`
- `Aden Gulf`
- `Bab el-Mandeb`
- `Bab al-Mandab`
- `al-Hudaydah`
- `Hodeidah`
- `Hudaydah`
- `Sa'dah`
- `Saada`
- `Sanaa`
- `Sana'a`
- `Marib`
- `Ma'rib`

## 5. 字段结构

主要 CSV 文件字段一致，共 31 列：

```text
event_id_cnty
event_date
year
time_precision
disorder_type
event_type
sub_event_type
actor1
assoc_actor_1
inter1
actor2
assoc_actor_2
inter2
interaction
civilian_targeting
iso
region
country
admin1
admin2
admin3
location
latitude
longitude
geo_precision
source
source_scale
notes
fatalities
tags
timestamp
```

## 6. 数据概况

2023+ 候选数据：

| 国家/海域 | 行数 |
| --- | ---: |
| Yemen | 25,808 |
| Somalia | 9,006 |
| Indian Ocean | 516 |
| Saudi Arabia | 37 |
| Djibouti | 24 |
| Eritrea | 24 |
| Oman | 14 |

2023+ 关键词筛选数据：

| 国家/海域 | 行数 |
| --- | ---: |
| Yemen | 21,881 |
| Indian Ocean | 486 |
| Somalia | 303 |
| Saudi Arabia | 11 |
| Eritrea | 6 |
| Djibouti | 1 |

2025-05-28 至今候选数据：

| 国家/海域 | 行数 |
| --- | ---: |
| Yemen | 12 |
| Somalia | 6 |

2025-05-28 至今关键词筛选数据：

| 国家/海域 | 行数 |
| --- | ---: |
| Yemen | 10 |

## 7. 复现命令

在 WSL 的 conda `Prob` 环境中执行：

```bash
cd /mnt/e/python/prob
/home/kelvin2005/anaconda3/bin/conda run --no-capture-output -n Prob python -u scripts/download_acled.py
```

## 8. 说明与限制

- `scripts/download_acled.py` 使用 `Path(__file__)` 定位项目根目录，因此可以从项目根目录或其他工作目录运行。
- 当前脚本默认输出到 `data/acled_data/`，默认读取 token 文件 `data/acled_API.json`。
- `Red Sea` 和 `Gulf of Aden` 作为 ACLED 的 `country` 字段查询时，本次没有返回记录；相关海域事件主要来自 `Yemen`、`Indian Ocean`、`Somalia` 等候选范围中的关键词筛选。
- 筛选数据依赖关键词匹配，因此可能包含地名相关但不一定直接由胡塞武装参与的事件，也可能漏掉未在所选字段中出现关键词的相关事件。
- `data/acled_API.json` 包含访问令牌，应避免公开或提交到版本库。
