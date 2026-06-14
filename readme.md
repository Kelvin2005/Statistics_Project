## 复现说明

在仓库根目录，使用 `conda` 构建运行环境：

```bash
conda env update -f environment.yml
conda activate Prob
```

生成分析结果和图片：

```bash
python scripts/run_analysis_real.py
python scripts/plot_time_series.py
python scripts/run_red_sea_causal_break_analysis.py
```