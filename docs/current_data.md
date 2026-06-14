# 当前数据与项目可行性分析

生成时间：2026-05-29

本文档总结当前项目已经收集的数据、可支持的统计分析问题，以及暂时无法完成或需要补充数据的部分。

## 1. 当前已有数据

### 1.1 ACLED 胡塞/红海相关事件数据

主要文件：

| 文件 | 行数 | 时间范围 | 说明 |
| --- | ---: | --- | --- |
| `data/acled_data/red_sea_yemen_candidate_2023_plus.csv` | 35,429 | 2023-01-01 至 2025-05-28 | 也门、索马里、印度洋及周边候选事件 |
| `data/acled_data/red_sea_yemen_houthi_related_2023_plus_limit30000.csv` | 22,688 | 2023-01-01 至 2025-05-28 | 关键词筛选后的胡塞/红海/亚丁湾相关事件 |
| `data/acled_data/red_sea_yemen_candidate_2025-05-28_to_present.csv` | 18 | 2025-05-28 | 2025-05-28 至当前请求范围的候选事件 |
| `data/acled_data/red_sea_yemen_houthi_related_2025-05-28_to_present.csv` | 10 | 2025-05-28 | 近期关键词筛选事件 |

ACLED 关键词筛选字段：

```text
actor1
actor2
assoc_actor_1
assoc_actor_2
location
admin1
admin2
admin3
notes
tags
```

关键词包括：

```text
Houthi
Houthis
Ansar Allah
Ansarallah
Red Sea
Gulf of Aden
Aden Gulf
Bab el-Mandeb
Bab al-Mandab
al-Hudaydah
Hodeidah
Hudaydah
Sa'dah
Saada
Sanaa
Sana'a
Marib
Ma'rib
```

2023+ 关键词筛选数据的国家/海域分布：

| 国家/海域 | 行数 |
| --- | ---: |
| Yemen | 21,881 |
| Indian Ocean | 486 |
| Somalia | 303 |
| Saudi Arabia | 11 |
| Eritrea | 6 |
| Djibouti | 1 |

2023+ 关键词筛选数据的事件类型分布：

| 事件类型 | 行数 |
| --- | ---: |
| Protests | 12,632 |
| Battles | 4,743 |
| Explosions/Remote violence | 2,611 |
| Strategic developments | 1,518 |
| Violence against civilians | 1,165 |
| Riots | 19 |

### 1.2 PortWatch / PortStraitWatch 通行指标

主要文件：

| 文件 | 行数 | 时间范围 | 说明 |
| --- | ---: | --- | --- |
| `data/portwatch/portwatch_chokepoints_long.csv` | 2,901 | 2023-10-01 至 2026-05-24 | 长表，每日每个 chokepoint 一行 |
| `data/portwatch/portwatch_chokepoints_wide.csv` | 967 | 2023-10-01 至 2026-05-24 | 宽表，每日一行 |
| `data/portwatch/portwatch_red_sea_analysis.csv` | 967 | 2023-10-01 至 2026-05-24 | 分析表，包含绕航指数等派生变量 |

覆盖的 chokepoints：

| portid | 通道 | 行数 |
| --- | --- | ---: |
| `chokepoint1` | Suez Canal | 967 |
| `chokepoint4` | Bab el-Mandeb Strait | 967 |
| `chokepoint7` | Cape of Good Hope | 967 |

主要原始指标：

```text
n_container
n_dry_bulk
n_general_cargo
n_roro
n_tanker
n_cargo
n_total
capacity_container
capacity_dry_bulk
capacity_general_cargo
capacity_roro
capacity_tanker
capacity_cargo
capacity
```

主要派生指标：

```text
rerouting_index_total = cape_good_hope_n_total / suez_n_total
rerouting_index_capacity = cape_good_hope_capacity / suez_capacity
suez_share_total = suez_n_total / (suez_n_total + cape_good_hope_n_total)
bab_to_suez_total_ratio = bab_el_mandeb_n_total / suez_n_total
```

通行量概况：

| 通道 | 日均通行量 | 最小值 | 最大值 |
| --- | ---: | ---: | ---: |
| Bab el-Mandeb Strait | 36.63 | 12 | 95 |
| Suez Canal | 42.11 | 10 | 95 |
| Cape of Good Hope | 84.53 | 13 | 204 |

绕航相关指标概况：

| 指标 | 均值 | 中位数 | 最小值 | 最大值 |
| --- | ---: | ---: | ---: | ---: |
| `rerouting_index_total` | 2.193 | 2.213 | 0.432 | 7.400 |
| `suez_share_total` | 0.337 | 0.311 | 0.119 | 0.698 |

### 1.3 实时 AIS 采集脚本

脚本：

```text
scripts/collect_aishub.py
```

说明文档：

```text
docs/aishub_collection.md
```

当前状态：

- 脚本已经实现。
- 默认采集范围覆盖红海、曼德海峡、亚丁湾。
- 由于目前无法注册 AISHub 账号，尚未实际采集实时 AIS 数据。

## 2. 当前数据能够支持的研究问题

当前数据已经足够支持一个完整的聚合层面统计项目。

推荐主问题：

```text
胡塞武装袭击事件是否显著改变红海关键航道的通行量与绕航行为？
```

可进一步拆成：

1. 胡塞相关袭击事件是否导致 Bab el-Mandeb 通行量下降？
2. 胡塞相关袭击事件是否导致 Suez Canal 通行量下降？
3. 胡塞相关袭击事件是否导致 Cape of Good Hope 通行量上升？
4. 红海危机后，`Cape / Suez` 绕航指数是否显著上升？
5. 不同类型事件，例如 `Explosions/Remote violence`、`Battles`，对通行量影响是否不同？
6. 攻击事件是否存在滞后效应，例如 1 日、7 日、14 日后通行量变化？

## 3. 可以采用的统计方法

### 3.1 日度事件研究

以典型事件或袭击升级日为中心，构造事件窗口：

```text
[-30, +30]
[-14, +14]
[-7, +7]
```

观察：

```text
bab_el_mandeb_n_total
suez_n_total
cape_good_hope_n_total
rerouting_index_total
suez_share_total
```

在事件前后的变化。

### 3.2 中断时间序列

选定红海危机关键节点，例如 2023-11-19 Galaxy Leader 劫持事件，建立：

```text
Y_t = β0 + β1 * trend_t + β2 * post_t + β3 * post_trend_t + ε_t
```

其中 `Y_t` 可以是：

```text
bab_el_mandeb_n_total
suez_n_total
cape_good_hope_n_total
rerouting_index_total
```

### 3.3 日度回归与滞后效应

构造 ACLED 日度事件数：

```text
attack_count_t
explosion_count_t
battle_count_t
fatalities_t
```

再与 PortWatch 日度指标合并：

```text
Y_t = β0 + β1 * attack_count_t + β2 * attack_count_{t-1:t-7}
      + weekday FE + month FE + trend + ε_t
```

可以用 Newey-West 标准误处理时间序列自相关。

### 3.4 稳健性检验

可做：

- 使用 `n_total` 和 `capacity` 两类因变量。
- 分别分析 Bab el-Mandeb、Suez、Cape。
- 将日度数据聚合为周度数据，减少噪声。
- 使用不同事件类型构造攻击强度。
- 排除纯抗议类事件，只保留暴力/袭击相关事件。

## 4. 暂时不适合完成的研究问题

当前数据不适合严谨回答：

```text
AIS 开启情况是否影响单船遇袭概率？
```

原因：

1. 缺少历史 AIS 单船轨迹数据。
2. 缺少未遇袭船舶的 AIS 状态作为对照组。
3. ACLED 是事件级数据，PortWatch 是聚合通行指标，二者无法直接识别具体船舶。
4. 当前 AISHub 实时采集尚未开始，且即使开始，也只能覆盖未来时间段。

因此，如果继续使用当前数据，研究结论应限定在：

```text
胡塞袭击与航运通行量、绕航行为的统计关联
```

而不是：

```text
AIS 开关对单船遇袭风险的因果影响
```

## 5. 项目可行性结论

当前项目可以完成，但建议调整为聚合层面研究。

推荐最终题目：

```text
胡塞武装袭击对红海关键航道通行量与绕航行为的统计分析
```

推荐核心数据组合：

```text
ACLED 胡塞/红海事件数据
+
PortWatch Suez Canal / Bab el-Mandeb / Cape of Good Hope 日度通行指标
```

推荐核心因变量：

```text
bab_el_mandeb_n_total
suez_n_total
cape_good_hope_n_total
rerouting_index_total
suez_share_total
```

推荐核心解释变量：

```text
attack_count_acled
explosion_count_acled
battle_count_acled
fatalities_acled
post_red_sea_crisis
```

## 6. 下一步建议

1. 从 ACLED 筛选数据中构造日度事件表。
2. 过滤出更贴近海上安全的事件类型，例如：

```text
Explosions/Remote violence
Battles
Violence against civilians
Strategic developments
```

3. 将 ACLED 日度事件表与 PortWatch `portwatch_red_sea_analysis.csv` 按日期合并。
4. 绘制时间序列图：

```text
attack_count_t
bab_el_mandeb_n_total
suez_n_total
cape_good_hope_n_total
rerouting_index_total
```

5. 进行事件研究或中断时间序列建模。
6. 将无法获得历史 AIS 的限制写入研究局限，并把实时 AIS 采集作为扩展方向。
