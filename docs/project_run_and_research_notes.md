# 项目运行与研究记录

本文汇总当前代码的运行方法、脚本参数接口、研究问题、研究方法、研究流程、预期结论和参考资料。当前阶段不再拉取新数据，分析基于仓库中已有 CSV 文件完成。

## 运行方法

进入项目目录并激活 Conda 环境：

```bash
cd /mnt/e/python/prob
conda activate Prob
```

运行本地分析脚本：

```bash
MPLBACKEND=Agg python scripts/run_analysis_real.py
```

`MPLBACKEND=Agg` 用于无图形界面的终端环境，避免 `plt.show()` 阻塞或显示报错。脚本会读取：

- `data/acled_data/red_sea_yemen_houthi_related_2023_plus_limit30000.csv`
- `data/portwatch/portwatch_red_sea_analysis.csv`

当前阶段不要运行以下数据获取脚本：

```bash
python scripts/download_acled.py
python scripts/download_portwatch.py
python scripts/collect_aishub.py
python scripts/sample_data.py
```

## 脚本参数接口

`scripts/run_analysis_real.py` 无命令行参数，直接读取本地数据并输出 VAR 与 OLS/Newey-West 回归结果。

`scripts/download_portwatch.py` 提供下载参数，但当前不建议运行：

```bash
python scripts/download_portwatch.py \
  --start-date 2023-01-01 \
  --end-date 2026-05-09 \
  --chokepoints chokepoint1 chokepoint4 chokepoint7 \
  --batch-size 1000 \
  --delay-seconds 1.0 \
  --max-retries 8
```

主要参数包括起止日期、航道 ID、每次请求记录数、请求间隔和失败重试次数。

`scripts/collect_aishub.py` 用于 AIS 实时采集，也不建议在当前阶段运行：

```bash
python scripts/collect_aishub.py --username <AISHUB_USERNAME> --preset red-sea-gulf-aden --once
```

主要参数包括 `--username`、`--preset`、经纬度范围、`--interval`、`--poll-seconds`、`--once`、`--output-csv` 和 `--raw-dir`。

`scripts/download_acled.py` 无命令行参数，日期、输出路径和关键词范围写在脚本常量中。

## 目标问题

项目研究红海地区胡塞武装相关安全事件是否、以及如何影响主要航道通行量和船舶绕航行为。具体问题包括：

1. 胡塞相关袭击事件增加后，曼德海峡通行量是否下降。
2. 同一冲击是否推动船舶转向好望角航线。
3. 集装箱船、干散货船、油轮等不同船型对安全冲击的敏感程度是否不同。

## 研究方法

第一类方法是 VAR 向量自回归模型。变量包括 `attack_count`、`bab_el_mandeb_n_total` 和 `cape_good_hope_n_total`。脚本使用 AIC 在最多 3 周滞后内选择模型，并通过 IRF 脉冲响应函数观察袭击冲击后未来 8 周航道通行量的动态变化。

第二类方法是分船型双对数 OLS 回归，并使用 Newey-West/HAC 稳健标准误修正时间序列中的异方差和自相关问题。模型形式为：

```text
ln(ship_flow + 1) = const + beta1 * ln(attacks + 1) + beta2 * lag_ln_attacks + error
```

## 研究流程

1. 读取 ACLED 胡塞相关事件数据。
2. 过滤事件类型，仅保留爆炸/远程暴力、战斗、针对平民暴力、战略发展等安全冲击事件。
3. 将事件按日期聚合为每日袭击次数。
4. 读取 PortWatch 航道通行数据。
5. 按日期合并 ACLED 与 PortWatch。
6. 将日度数据聚合为周度数据，以降低日度噪声并体现航运决策滞后。
7. 建立 VAR 模型，分析总体航道动态响应。
8. 建立分船型 OLS 模型，比较不同船型弹性差异。
9. 输出模型摘要和回归结果。

## 预期结论

当前结果更适合表述为“初步证据”。红海安全冲击与航道通行变化存在动态关系，但不是简单的同期线性关系。VAR 结果显示，好望角通行量对袭击冲击存在滞后响应迹象，说明绕航可能需要一定决策和执行时间。曼德海峡通行量更多受自身历史通行量影响，袭击变量的直接影响在当前模型中不够稳定。

分船型回归中，集装箱船、干散货船、油轮的袭击变量系数均未达到显著水平，且 R² 较低。因此当前数据更适合支持“安全冲击可能影响总体航线结构”的判断，不宜强行得出“某一船型显著更敏感”的结论。

## 参考资料

1. Notteboom, T., Haralambides, H., & Cullinane, K. (2024). *The Red Sea Crisis: ramifications for vessel operations, shipping networks, and maritime supply chains*. https://ideas.repec.org/a/pal/marecl/v26y2024i1d10.1057_s41278-024-00287-z.html
2. UNCTAD. (2024). *Navigating troubled waters: Impact to global trade of disruption of shipping routes in the Red Sea, Black Sea and Panama Canal*. https://unctad.org/publication/navigating-troubled-waters-impact-global-trade-disruption-shipping-routes-red-sea-black
3. UNCTAD. (2024). *Review of Maritime Transport 2024*. https://unctad.org/publication/review-maritime-transport-2024
4. IMF Blog. (2024). *Red Sea Attacks Disrupt Global Trade*. https://www.imf.org/en/blogs/articles/2024/03/07/red-sea-attacks-disrupt-global-trade
5. World Bank Blog. (2024). *Navigating troubled waters: The Red Sea shipping crisis and its global repercussions*. https://blogs.worldbank.org/en/developmenttalk/navigating-troubled-waters--the-red-sea-shipping-crisis-and-its-
6. IMF & University of Oxford. (2023). *PortWatch platform launch*. https://www.imf.org/en/news/articles/2023/11/13/pr23390-imf-university-of-oxford-launch-portwatch-platform-monitor-simulate-trade-disruptions
7. IMF Working Paper. (2025). *Nowcasting Global Trade from Space*. https://www.elibrary.imf.org/view/journals/001/2025/093/article-A001-en.xml
8. ACLED. *ACLED Codebook*. https://acleddata.com/methodology/acled-codebook
9. Raleigh, C., Linke, A., Hegre, H., & Karlsen, J. (2010). *Introducing ACLED: An Armed Conflict Location and Event Dataset*. https://journals.sagepub.com/doi/abs/10.1177/0022343310378914
10. U.S. EIA. (2024). *Red Sea disruptions increase oil flows around Cape of Good Hope*. https://www.eia.gov/todayinenergy/detail.php?id=62263
11. Sims, C. A. (1980). *Macroeconomics and Reality*. https://www.scirp.org/reference/referencespapers?referenceid=3544397
12. Lütkepohl, H. (2005). *New Introduction to Multiple Time Series Analysis*. https://www.stata.com/bookstore/multiple-time-series-analysis/
13. Newey, W. K., & West, K. D. (1987). *A Simple, Positive Semi-Definite, Heteroskedasticity and Autocorrelation Consistent Covariance Matrix*. https://econpapers.repec.org/paper/nbrnberte/0055.htm
14. *Red Sea crisis impacts on maritime shipping networks*. Heliyon, 2024. https://pubmed.ncbi.nlm.nih.gov/39624292/
15. *Geopolitical disruptions and maritime transitions: Environmental and economic costs of rerouting*. https://www.sciencedirect.com/science/article/pii/S0965856425003702
