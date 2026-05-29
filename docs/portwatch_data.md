# PortWatch 通行指标数据说明

脚本：`scripts/download_portwatch.py`

用途：下载 IMF PortWatch / PortStraitWatch 的日度 chokepoint 通行指标，用于分析胡塞武装袭击与红海航运通行量、绕航行为之间的关系。

## 1. 数据源

ArcGIS FeatureServer：

```text
https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query
```

## 2. 默认采集 chokepoints

| portid | 名称 | 用途 |
| --- | --- | --- |
| `chokepoint1` | Suez Canal | 红海航线通行量 |
| `chokepoint4` | Bab el-Mandeb Strait | 与胡塞袭击最直接相关的通道 |
| `chokepoint7` | Cape of Good Hope | 绕航替代路径 |

## 3. 输出文件

| 文件 | 说明 |
| --- | --- |
| `data/portwatch/portwatch_chokepoints_long.csv` | 长表：每行是一个日期和一个 chokepoint |
| `data/portwatch/portwatch_chokepoints_wide.csv` | 宽表：每行是一个日期，列为各 chokepoint 指标 |
| `data/portwatch/portwatch_red_sea_analysis.csv` | 宽表基础上加入绕航和占比指标 |
| `data/portwatch/download_metadata.json` | 下载参数和范围 |

## 4. 主要字段

船舶数量：

```text
n_container
n_dry_bulk
n_general_cargo
n_roro
n_tanker
n_cargo
n_total
```

通过运力/货量相关指标：

```text
capacity_container
capacity_dry_bulk
capacity_general_cargo
capacity_roro
capacity_tanker
capacity_cargo
capacity
```

派生分析指标：

```text
rerouting_index_total = cape_good_hope_n_total / suez_n_total
rerouting_index_capacity = cape_good_hope_capacity / suez_capacity
suez_share_total = suez_n_total / (suez_n_total + cape_good_hope_n_total)
bab_to_suez_total_ratio = bab_el_mandeb_n_total / suez_n_total
```

## 5. 运行命令

下载全部可用日期：

```bash
cd /mnt/e/python/prob
/home/kelvin2005/anaconda3/bin/conda run --no-capture-output -n Prob python -u scripts/download_portwatch.py
```

只下载红海危机相关时期，例如 2023-10-01 至今：

```bash
cd /mnt/e/python/prob
/home/kelvin2005/anaconda3/bin/conda run --no-capture-output -n Prob python -u scripts/download_portwatch.py --start-date 2023-10-01 --batch-size 500 --delay-seconds 1
```

指定结束日期：

```bash
/home/kelvin2005/anaconda3/bin/conda run --no-capture-output -n Prob python -u scripts/download_portwatch.py --start-date 2023-10-01 --end-date 2026-05-29
```

说明：ArcGIS 服务偶尔会出现 SSL EOF，因此实测更稳定的参数是 `--batch-size 500 --delay-seconds 1`。

## 7. 当前已下载结果

已下载 `2023-10-01` 至 `2026-05-24` 的数据：

| chokepoint | 行数 |
| --- | ---: |
| Suez Canal | 967 |
| Bab el-Mandeb Strait | 967 |
| Cape of Good Hope | 967 |

总行数：2,901。

## 6. 与 ACLED 合并

建议按日合并：

```text
date
attack_count_acled
bab_el_mandeb_n_total
suez_n_total
cape_good_hope_n_total
rerouting_index_total
suez_share_total
```

可用于：

- 事件研究
- 中断时间序列
- 日度或周度回归
- 攻击事件数与通行量变化的相关分析
