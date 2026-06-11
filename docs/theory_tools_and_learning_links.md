# 理论工具解释与学习链接

本文档配套 `docs/red_sea_houthi_shipping_paper.md`，用于说明论文中使用的理论机制、统计工具、适用原因、局限和学习资料。

## 1. 航运路线选择与风险成本机制

### 用在论文中的作用

论文不是简单假设“有袭击就一定少通行”，而是使用“风险调整后的航线成本”解释航运企业为什么可能绕行好望角。

一个简化表达是：

```text
期望总成本 = 正常运营成本 + 时间延误成本 + 风险溢价 + 保险成本 + 预期损失
```

红海至苏伊士运河航线通常距离更短，正常运营成本较低；好望角航线距离更长，燃油和时间成本较高。但当红海袭击事件增加时，风险溢价、保险成本和预期损失上升。若风险调整后的红海航线总成本超过好望角航线，船舶就可能绕航。

### 能解释什么

- 为什么影响可能不是同期发生，而是滞后出现。
- 为什么好望角通行量是绕航行为的重要观察变量。
- 为什么曼德海峡通行量不一定机械下降，因为部分船舶可能继续通行。

### 局限

当前项目没有保险费率、运价、燃油成本和单船航线选择数据，因此这一机制主要作为理论解释框架，不能在本文中完整估计每一项成本。

### 学习链接

- UNCTAD 红海、黑海和巴拿马运河航运中断评估：  
  https://unctad.org/publication/navigating-troubled-waters-impact-global-trade-disruption-shipping-routes-red-sea-black
- IMF 关于红海袭击与全球贸易的分析：  
  https://www.imf.org/en/blogs/articles/2024/03/07/red-sea-attacks-disrupt-global-trade
- EIA 关于红海中断后好望角能源运输增加的说明：  
  https://www.eia.gov/todayinenergy/detail.php?id=62263

## 2. ACLED 事件数据与事件类型筛选

### 用在论文中的作用

ACLED 提供政治暴力和冲突事件的事件级记录。论文用它构造每周安全事件数量 `attack_count`。为了让解释变量更接近海事安全冲击，论文排除了 `Protests` 和 `Riots`，保留：

```text
Explosions/Remote violence
Battles
Violence against civilians
Strategic developments
```

### 为什么这样筛选

`Protests` 数量很大，但与海上航运安全冲击的直接关系较弱。如果全部纳入，解释变量可能混入较多政治表达和社会动员噪声。保留暴力和战略发展类事件，可以让 `attack_count` 更接近“安全风险信号”。

### 局限

- 关键词筛选可能误纳入与航运无关的事件。
- 也可能漏掉没有命中关键词但实际相关的事件。
- ACLED 是事件数据，不是船舶轨迹数据，无法识别某艘船是否因为某个事件改变航线。

### 学习链接

- ACLED Codebook：  
  https://acleddata.com/knowledge-base/codebook/
- ACLED 事件类型说明：  
  https://acleddata.com/faq/what-types-events-does-acled-code

## 3. PortWatch / PortStraitWatch 航道通行指标

### 用在论文中的作用

PortWatch 提供关键港口和 chokepoint 的高频通行指标。论文使用三个通道：

| 通道 | 作用 |
| --- | --- |
| Suez Canal | 红海航线进入欧洲方向的核心通道 |
| Bab el-Mandeb Strait | 红海南端关键通道，与胡塞袭击地理上最接近 |
| Cape of Good Hope | 绕航替代路径 |

论文使用 `cape_good_hope_n_total / suez_n_total` 构造绕航指数，用来观察好望角相对于苏伊士通行量的变化。

### 能验证什么

PortWatch 能验证聚合通行量是否变化，但不能验证单船行为。也就是说，它适合回答“总体航道结构是否变化”，不适合回答“某艘船是否因为关闭 AIS 而遇袭”。

### 学习链接

- IMF 与 Oxford PortWatch 发布说明：  
  https://www.imf.org/en/news/articles/2023/11/13/pr23390-imf-university-oxford-launch-portwatch-platform-monitor-simulate-trade-disruptions
- PortWatch 平台：  
  https://portwatch.imf.org/

## 4. 向量自回归模型 VAR

### 基本思想

VAR 用来分析多个时间序列之间的动态关系。它不把某个变量固定为唯一因变量，而是把系统中的每个变量都看成由自身滞后项和其他变量滞后项共同解释。

论文中的三变量系统是：

```text
X_t = [attack_count_t, bab_el_mandeb_n_total_t, cape_good_hope_n_total_t]'
```

VAR(p) 形式为：

```text
X_t = c + A_1 X_{t-1} + A_2 X_{t-2} + ... + A_p X_{t-p} + u_t
```

### 为什么适合本文

红海安全事件和航道通行量都具有时间序列特征。船舶绕航也可能滞后发生。VAR 可以观察：

- 袭击事件是否有持续性。
- 曼德海峡通行量是否主要受自身历史水平影响。
- 好望角通行量是否对袭击事件滞后项有响应。

### 论文中如何解释

VAR 结果应解释为动态相关关系，而不是严格因果关系。若某个袭击滞后项显著，只能说明过去袭击事件对当前通行量有统计预测力，不能单独证明袭击是唯一原因。

### 重要前提

标准 VAR 通常要求时间序列是平稳的，即均值、方差和自相关结构不随时间系统漂移。本文使用周度水平变量做探索性分析，因此在论文中应明确这是动态相关分析。若要进一步提高严谨性，可以补做单位根检验、差分 VAR、协整检验或 VECM。

### 学习链接

- statsmodels VAR 官方文档：  
  https://www.statsmodels.org/dev/vector_ar.html
- statsmodels 稳定版 VAR 文档：  
  https://www.statsmodels.org/v0.13.5/vector_ar.html
- Sims (1980) VAR 经典文献条目：  
  https://www.scirp.org/reference/referencespapers?referenceid=3544397

## 5. 脉冲响应函数 IRF

### 基本思想

脉冲响应函数用于观察一个变量受到一次冲击后，系统中其他变量在未来若干期如何变化。论文中使用它来观察：

```text
袭击事件增加一个标准差后，未来 8 周曼德海峡和好望角通行量如何响应。
```

### 为什么适合本文

如果航运企业需要几周时间调整航线，那么冲击响应就不应只看同期，而应观察后续多周路径。IRF 正好用于展示这种动态响应。

### 解释注意

正交化 IRF 的结果会受到变量排序和残差协方差分解方式影响。因此，论文中应重点解释方向、滞后模式和现实机制，不应把每个响应值当成精确因果效应。

### 学习链接

- statsmodels VAR 中的 Impulse Response Analysis：  
  https://www.statsmodels.org/dev/vector_ar.html
- statsmodels VARMAX impulse responses 说明：  
  https://www.statsmodels.org/dev/generated/statsmodels.tsa.statespace.varmax.VARMAX.impulse_responses.html

## 6. 线性回归与分段趋势

### 基本思想

OLS 回归用于估计解释变量和因变量之间的平均线性关系。本文不使用 OLS 来研究船型敏感性，而是把它作为中断时间序列和 Chow 结构突变检验的基础工具。中断时间序列中的分段趋势可写为：

```text
Y_t = beta_0 + beta_1 time_t + beta_2 post_t
      + beta_3 time_after_t + weekday_FE + error_t
```

### 为什么这样设定

- `time_t` 捕捉断点前的原有趋势。
- `post_t` 捕捉 2023 年 11 月 19 日后的即时水平变化。
- `time_after_t` 捕捉断点后的趋势变化。
- `weekday_FE` 控制日度数据中可能存在的星期效应。

### 本文中的作用

线性分段回归帮助论文回答一个更可验证的问题：危机升级节点之后，航道通行结构是否偏离原有趋势。它不尝试回答单船风险、AIS 开关或船型敏感性问题。

### 学习链接

- Penn State STAT 501 回归课程：  
  https://online.stat.psu.edu/stat501/
- Penn State STAT 501 数据变换与对数变换：  
  https://online.stat.psu.edu/stat501/Lesson09
- statsmodels OLS 文档：  
  https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLS.html

## 7. 事件研究

### 基本思想

事件研究把某个清楚发生的外生事件设为 `t = 0`，比较事件前后的结果变量路径。本文把 2023 年 11 月 19 日 Galaxy Leader 劫持事件设为红海危机升级节点，观察断点前 49 天和断点后 180 天内各航道通行指标的变化。

### 用在论文中的原因

事件研究能直观展示“变化何时开始”。本文结果显示，断点后前 30 天变化不大，但 31-90 天之后，曼德海峡和苏伊士通行量明显下降，好望角通行量和绕航指数明显上升。这与航运路线调整需要时间的理论机制一致。

### 解释注意

事件研究本身主要是描述性准实验方法。若没有对照组，它不能完全排除其他同期冲击。因此本文把它与中断时间序列和结构突变检验配合使用。

### 学习链接

- Event studies and causal inference 综述入口：  
  https://mixtape.scunning.com/09-difference_in_differences
- World Bank Impact Evaluation in Practice 资源：  
  https://openknowledge.worldbank.org/entities/publication/1a2e6c37-5815-5028-8b31-5a747ccbe357

## 8. 中断时间序列 ITS

### 基本思想

中断时间序列适合评估某个明确时间点发生的政策、灾害或冲击。基本分段回归形式是：

```text
Y_t = beta_0 + beta_1 time_t + beta_2 post_t
      + beta_3 time_after_t + controls + error_t
```

其中 `beta_2` 表示断点后的即时水平变化，`beta_3` 表示断点后的趋势变化。

### 用在论文中的原因

红海危机升级不是随机实验，但 2023 年 11 月 19 日是清楚可定位的外部事件。ITS 可以检验断点后航运通行量是否偏离原有趋势。本文结果显示，好望角通行量和绕航指数的断点后斜率显著上升，苏伊士和曼德海峡通行量的断点后斜率显著下降。

### 解释注意

ITS 的关键假设是：如果没有断点事件，结果变量会继续沿断点前趋势变化。本文断点前窗口只有 49 天，因此应表述为探索性准因果证据，而不是最终强因果结论。

### 学习链接

- Interrupted time series regression tutorial：  
  https://pmc.ncbi.nlm.nih.gov/articles/PMC5407170/
- Methods for evaluating causality in observational studies：  
  https://pmc.ncbi.nlm.nih.gov/articles/PMC7081045/

## 9. Chow 结构突变检验

### 基本思想

Chow 检验用于判断某个已知断点前后，线性模型的系数是否可以视为同一组参数。直观地说，它比较“全样本一条回归线”与“断点前后一人一条回归线”的拟合差异。

### 用在论文中的原因

本文已经知道 2023 年 11 月 19 日是外部升级节点，因此可以检验航运指标在这个断点前后是否存在结构性变化。结果显示，好望角通行量和苏伊士通行占比的结构突变证据更明显。

### 解释注意

Chow 检验要求断点预先给定，不能先看数据再挑最显著日期。本文断点来自 Galaxy Leader 劫持这一外部事件，因此比数据挖掘式断点更稳。

### 学习链接

- Chow Test for Structural Breaks 说明：  
  https://communities.sas.com/t5/SAS-Code-Examples/Chow-Test-for-Structural-Breaks/ta-p/887904
- 结构突变概念说明：  
  https://metricgate.com/docs/chow-test-structural-break/

## 10. Newey-West / HAC 稳健标准误

### 基本思想

普通 OLS 标准误假设误差项没有异方差和自相关。但时间序列数据中，残差常常会相关，例如本周航运量与上周航运量存在联系。Newey-West 标准误用于在存在异方差和自相关时，修正回归系数的标准误。

### 用在论文中的原因

论文的中断时间序列使用日度通行数据。如果直接使用普通标准误，显著性检验可能过于乐观。因此脚本中使用：

```python
model.fit(cov_type="HAC", cov_kwds={"maxlags": 14})
```

这表示使用 HAC 稳健标准误，并允许最多 14 天的残差自相关。

### 注意事项

Newey-West 修正的是标准误，不会改变 OLS 系数本身。它让 p 值和置信区间更适合时间序列数据，但不能解决遗漏变量、反向因果或模型设定错误。

### 学习链接

- statsmodels HAC 协方差文档：  
  https://www.statsmodels.org/stable/generated/statsmodels.stats.sandwich_covariance.cov_hac.html
- Stata Newey-West 说明，适合理解概念：  
  https://www.stata.com/manuals/tsnewey.pdf
- Newey-West 原始论文信息：  
  https://www.resea.org/10.2307/1913610

## 11. AIC 信息准则

### 基本思想

AIC 用来在多个模型之间选择较合适的复杂度。它平衡两个目标：

```text
拟合更好，但不要使用过多参数。
```

在 VAR 模型中，滞后阶数越高，模型可以捕捉更长的动态关系，但参数也会更多。论文用 AIC 在最多 3 周滞后内选择最佳滞后阶数，最终选择 3 周。

### 学习链接

- statsmodels VAR 模型选择说明：  
  https://www.statsmodels.org/dev/vector_ar.html
- Penn State STAT 501 模型构建部分：  
  https://online.stat.psu.edu/stat501/

## 12. 论文答辩时的简短说法

如果被问“你的论文到底验证了什么”，可以这样回答：

```text
本文验证的是胡塞相关安全事件与红海航运通行结构之间的聚合层面动态关联。ACLED 提供安全事件时间序列，PortWatch 提供航道通行时间序列。VAR 用于检验安全事件和航道通行量之间的滞后动态关系，IRF 用于展示冲击后的响应路径；事件研究、ITS 和 Chow 检验围绕 2023 年 11 月 19 日升级节点检验断点前后航运结构是否变化。由于缺少历史 AIS 单船轨迹、保险、运价和船东决策数据，本文主动放弃单船遇袭风险、AIS 开关影响和船型敏感性问题。
```

如果被问“为什么不研究船型或 AIS”，可以这样回答：

```text
当前数据是 ACLED 事件级数据和 PortWatch 聚合航道通行数据，无法识别具体船舶、船东、AIS 状态或单船航线选择。把这些问题写成研究问题会超出数据能力。因此论文只保留能够被现有数据验证的聚合航道结构变化。
```
