# AISHub 实时 AIS 采集说明

脚本：`scripts/collect_aishub.py`

用途：从 AISHub 获取红海、曼德海峡、亚丁湾及周边海域的近实时 AIS 快照，用于后续分析船舶 AIS 开启/关闭、AIS gap、航线变化与袭击事件的关系。

## 1. 凭据

不要把 AISHub 用户名写入代码。运行前在 WSL 中设置环境变量：

```bash
export AISHUB_USERNAME="your_aishub_username"
```

也可以运行时传入：

```bash
python scripts/collect_aishub.py --username your_aishub_username --once
```

## 2. 默认采集范围

默认 preset 为 `red-sea-gulf-aden`：

| 参数 | 值 |
| --- | ---: |
| `latmin` | 10 |
| `latmax` | 30 |
| `lonmin` | 32 |
| `lonmax` | 65 |

该范围覆盖红海、曼德海峡、亚丁湾、也门沿岸、索马里北岸、吉布提、厄立特里亚、沙特西岸以及阿拉伯海西部一部分。

可选 preset：

| preset | 范围 |
| --- | --- |
| `red-sea-gulf-aden` | 红海 + 曼德海峡 + 亚丁湾 |
| `red-sea` | 红海 |
| `bab-el-mandeb` | 曼德海峡 |
| `gulf-aden` | 亚丁湾 |

也可以手动传入 bbox：

```bash
python scripts/collect_aishub.py --latmin 10 --latmax 16 --lonmin 43 --lonmax 54 --once
```

## 3. 输出文件

脚本会生成两类数据：

| 路径 | 说明 |
| --- | --- |
| `data/aishub/raw/YYYY-MM-DD/*.json` | 每次请求返回的原始 JSON 快照 |
| `data/aishub/processed/aishub_positions.csv` | 标准化后的追加式 CSV 表 |

CSV 会按 `mmsi + time` 去重，避免重复快照不断写入同一条 AIS 位置记录。

## 4. 运行方式

单次测试：

```bash
cd /mnt/e/python/prob
/home/kelvin2005/anaconda3/bin/conda run --no-capture-output -n Prob python -u scripts/collect_aishub.py --once
```

持续采集：

```bash
cd /mnt/e/python/prob
/home/kelvin2005/anaconda3/bin/conda run --no-capture-output -n Prob python -u scripts/collect_aishub.py
```

每 5 分钟采集一次：

```bash
cd /mnt/e/python/prob
/home/kelvin2005/anaconda3/bin/conda run --no-capture-output -n Prob python -u scripts/collect_aishub.py --poll-seconds 300
```

## 5. 字段

标准化 CSV 主要字段：

```text
collected_at_utc
mmsi
time
latitude
longitude
sog
cog
heading
navstat
imo
name
callsign
type
draught
dest
eta
raw_json
```

`raw_json` 保存原始记录，方便后续补充字段或排查格式变化。

## 6. 注意事项

- AISHub 适合从现在开始做实时/近实时采集，不适合补齐过去历史 AIS。
- 脚本默认不会高于每分钟一次请求；如果 `--poll-seconds` 小于 60，会自动提升到 60。
- `data/aishub/raw/` 原始快照可能增长很快，已加入 `.gitignore`。
- 如果要长期运行，建议后续用 cron、systemd、tmux 或 Codex 自动化任务托管。
