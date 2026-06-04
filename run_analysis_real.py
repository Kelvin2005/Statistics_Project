import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.tsa.api import VAR

# ==============================================================================
# 1. 真实数据读取与对齐管道 (Data Pipeline)
# ==============================================================================
print("正在读取并清洗真实的 ACLED 遇袭数据与 PortWatch 航道指标...")

# 读取 ACLED 数据（根据你的最新截图，文件位于 data/acled_data/ 下）
acled_path = 'data/acled_data/red_sea_yemen_houthi_related_2023_plus_limit30000.csv'
df_acled = pd.read_csv(acled_path, parse_dates=['event_date'])

# 过滤掉抗议事件(Protests)，只保留直接海事安全冲击事件
violent_types = ['Explosions/Remote violence', 'Battles', 'Violence against civilians', 'Strategic developments']
df_acled_violent = df_acled[df_acled['event_type'].isin(violent_types)]

# 聚合为日度袭击事件数
df_attacks_daily = df_acled_violent.groupby('event_date').agg(
    attack_count=('event_id_cnty', 'size')
).reset_index()
df_attacks_daily.rename(columns={'event_date': 'date'}, inplace=True)

# 读取 PortWatch 分析宽表（包含派生指标）
pw_path = 'data/portwatch/portwatch_red_sea_analysis.csv'
df_pw = pd.read_csv(pw_path, parse_dates=['date'])

# 合并两张真实表格，以 PortWatch 的连续日期为基准
df_master = pd.merge(df_pw, df_attacks_daily, on='date', how='left')
df_master['attack_count'] = df_master['attack_count'].fillna(0)

# 设定日期索引，并按周(W)聚合，以消除日度随机噪声并捕捉合理的决策时滞
df_master.set_index('date', inplace=True)
df_weekly = df_master.resample('W').agg({
    'attack_count': 'sum',
    'bab_el_mandeb_n_total': 'sum',
    'cape_good_hope_n_total': 'sum',
    'suez_n_total': 'sum',
    'rerouting_index_total': 'mean',
    # 提取方案三所需的分类船型通行量
    'bab_el_mandeb_n_container': 'sum',
    'bab_el_mandeb_n_dry_bulk': 'sum',
    'bab_el_mandeb_n_tanker': 'sum'
})

print(f"数据融合成功！共处理 {len(df_weekly)} 周的宏观联立时序数据。\n")


# ==============================================================================
# 2. 方案一：向量自回归 (VAR) 与脉冲响应函数 (IRF)
# ==============================================================================
print("--- 正在执行方案一：向量自回归模型 (VAR) ---")

# 提取 VAR 系统变量（袭击数、曼德海峡通行量、好望角通行量）
var_data = df_weekly[['attack_count', 'bab_el_mandeb_n_total', 'cape_good_hope_n_total']].dropna()

# 拟合 VAR 模型，让系统根据 AIC 信息准则自动选择最佳的滞后周数
var_model = VAR(var_data)
var_results = var_model.fit(maxlags=3, ic='aic')
print(f"系统自动选择的最佳滞后阶数 (Lag): {var_results.k_ar} 周")
print(var_results.summary())

# 运行正交化脉冲响应，模拟袭击爆发一个标准差后，未来 8 周内各大航道的变化轨迹
irf = var_results.irf(8)

# 绘制冲击反应图
fig = irf.plot(impulse='attack_count', orthogonalized=True)
fig.set_size_inches(12, 8)
plt.suptitle('胡塞武装袭击对航道通行量的动态脉冲响应 (真实数据拟合)', fontsize=14, y=1.02)
plt.grid(True)
plt.show()


# ==============================================================================
# 3. 方案三：分船型多元双对数回归 (OLS + Newey-West)
# ==============================================================================
print("\n--- 正在执行方案三：分船型条件弹性分析 (OLS + Newey-West) ---")

# 为防止 log(0) 报错，采用宏观经济学标准处理：对数化时加上 1
df_weekly['ln_attacks'] = np.log(df_weekly['attack_count'] + 1)
df_weekly['ln_container'] = np.log(df_weekly['bab_el_mandeb_n_container'] + 1)
df_weekly['ln_dry_bulk'] = np.log(df_weekly['bab_el_mandeb_n_dry_bulk'] + 1)
df_weekly['ln_tanker'] = np.log(df_weekly['bab_el_mandeb_n_tanker'] + 1)

# 构建引入当期和滞后一期袭击数的解释变量矩阵（并加入常数项）
df_weekly['ln_attacks_lag1'] = df_weekly['ln_attacks'].shift(1)
X = sm.add_constant(df_weekly[['ln_attacks', 'ln_attacks_lag1']]).loc[df_weekly.index[1:]]

ship_types = {
    '集装箱船 (Container)': df_weekly['ln_container'].loc[df_weekly.index[1:]],
    '干散货船 (Dry Bulk)': df_weekly['ln_dry_bulk'].loc[df_weekly.index[1:]],
    '原油/成品油轮 (Tanker)': df_weekly['ln_tanker'].loc[df_weekly.index[1:]]
}

for name, y in ship_types.items():
    print(f"\n==================== {name} 弹性回归报告 ====================")
    # 使用 Newey-West (HAC) 稳健标准误修正，克服时间序列的自相关问题
    ols_model = sm.OLS(y, X, missing='drop')
    ols_results = ols_model.fit(cov_type='HAC', cov_kwds={'maxlags': 2})
    print(ols_results.summary())