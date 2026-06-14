from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ACLED_PATH = PROJECT_ROOT / "data" / "acled_data" / "red_sea_yemen_houthi_related_2023_plus_limit30000.csv"
PORTWATCH_PATH = PROJECT_ROOT / "data" / "portwatch" / "portwatch_red_sea_analysis.csv"
PLOT_DIR = PROJECT_ROOT / "plot"
RESULTS_DIR = PROJECT_ROOT / "docs" / "analysis_results"
RESULTS_MD = RESULTS_DIR / "red_sea_causal_break_results.md"

EVENT_DATE = pd.Timestamp("2023-11-19")
PRE_WINDOW_DAYS = 49
POST_WINDOW_DAYS = 180
HAC_LAGS = 14


def chinese_font() -> FontProperties:
    candidates = [
        Path("/mnt/c/Windows/Fonts/simsun.ttc"),
        Path("/mnt/c/Windows/Fonts/simhei.ttf"),
        Path("/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf"),
        Path("C:/Windows/Fonts/simsun.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return FontProperties(fname=str(candidate))
    return FontProperties(family="sans-serif")


CHINESE_FONT = chinese_font()

VIOLENT_TYPES = [
    "Explosions/Remote violence",
    "Battles",
    "Violence against civilians",
    "Strategic developments",
]

OUTCOME_SPECS = {
    "ln_bab_el_mandeb_n_total": {
        "source": "bab_el_mandeb_n_total",
        "label": "ln(曼德海峡通行量+1)",
        "plot_label": "曼德海峡通行量相对基准变化(%)",
        "kind": "log_count",
    },
    "ln_suez_n_total": {
        "source": "suez_n_total",
        "label": "ln(苏伊士运河通行量+1)",
        "plot_label": "苏伊士运河通行量相对基准变化(%)",
        "kind": "log_count",
    },
    "ln_cape_good_hope_n_total": {
        "source": "cape_good_hope_n_total",
        "label": "ln(好望角通行量+1)",
        "plot_label": "好望角通行量相对基准变化(%)",
        "kind": "log_count",
    },
    "rerouting_index_total": {
        "source": "rerouting_index_total",
        "label": "好望角/苏伊士绕航指数",
        "plot_label": "绕航指数相对基准变化",
        "kind": "level",
    },
    "suez_share_total": {
        "source": "suez_share_total",
        "label": "苏伊士通行占比",
        "plot_label": "苏伊士占比相对基准变化",
        "kind": "level",
    },
}


@dataclass
class ModelResult:
    outcome: str
    label: str
    window: str
    level_coef: float
    level_p: float
    slope_coef: float
    slope_p: float
    nobs: int
    r2: float


@dataclass
class ChowResult:
    outcome: str
    label: str
    window: str
    f_stat: float
    p_value: float
    n_pre: int
    n_post: int


def configure_plots() -> None:
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.dpi"] = 130


def load_master_data() -> pd.DataFrame:
    acled = pd.read_csv(ACLED_PATH, parse_dates=["event_date"])
    acled = acled[acled["event_type"].isin(VIOLENT_TYPES)].copy()
    attacks_daily = (
        acled.groupby("event_date")
        .agg(attack_count=("event_id_cnty", "size"), fatalities=("fatalities", "sum"))
        .reset_index()
        .rename(columns={"event_date": "date"})
    )

    portwatch = pd.read_csv(PORTWATCH_PATH, parse_dates=["date"])
    master = pd.merge(portwatch, attacks_daily, on="date", how="left")
    master["attack_count"] = master["attack_count"].fillna(0)
    master["fatalities"] = master["fatalities"].fillna(0)

    for outcome, spec in OUTCOME_SPECS.items():
        source = spec["source"]
        if spec["kind"] == "log_count":
            master[outcome] = np.log(master[source] + 1)
        else:
            master[outcome] = master[source]

    master = master.sort_values("date").reset_index(drop=True)
    master["event_time"] = (master["date"] - EVENT_DATE).dt.days
    master["post"] = (master["date"] >= EVENT_DATE).astype(int)
    master["time"] = np.arange(len(master))
    event_index = master.loc[master["date"] >= EVENT_DATE, "time"].min()
    master["time_after"] = np.where(master["post"].eq(1), master["time"] - event_index + 1, 0)
    master["weekday"] = master["date"].dt.dayofweek
    return master


def analysis_window(master: pd.DataFrame, post_days: int = POST_WINDOW_DAYS) -> pd.DataFrame:
    return master[
        (master["date"] >= EVENT_DATE - pd.Timedelta(days=PRE_WINDOW_DAYS))
        & (master["date"] <= EVENT_DATE + pd.Timedelta(days=post_days))
    ].copy()


def fit_its(df: pd.DataFrame, outcome: str) -> sm.regression.linear_model.RegressionResultsWrapper:
    weekday_dummies = pd.get_dummies(df["weekday"], prefix="weekday", drop_first=True, dtype=float)
    x = pd.concat(
        [
            df[["time", "post", "time_after"]].astype(float).reset_index(drop=True),
            weekday_dummies.reset_index(drop=True),
        ],
        axis=1,
    )
    x = sm.add_constant(x)
    y = df[outcome].astype(float).reset_index(drop=True)
    return sm.OLS(y, x).fit(cov_type="HAC", cov_kwds={"maxlags": HAC_LAGS})


def fit_counterfactual(df: pd.DataFrame, outcome: str) -> pd.DataFrame:
    model = fit_its(df, outcome)
    weekday_dummies = pd.get_dummies(df["weekday"], prefix="weekday", drop_first=True, dtype=float)
    x = pd.concat(
        [
            df[["time", "post", "time_after"]].astype(float).reset_index(drop=True),
            weekday_dummies.reset_index(drop=True),
        ],
        axis=1,
    )
    x = sm.add_constant(x)
    fitted = model.predict(x)

    counter_x = x.copy()
    counter_x["post"] = 0.0
    counter_x["time_after"] = 0.0
    counterfactual = model.predict(counter_x)

    out = df[["date", "event_time", outcome]].copy().reset_index(drop=True)
    out["fitted"] = fitted
    out["counterfactual"] = counterfactual
    return out


def run_its_models(master: pd.DataFrame) -> tuple[list[ModelResult], list[ModelResult]]:
    primary = analysis_window(master, POST_WINDOW_DAYS)
    full = master[master["date"] >= EVENT_DATE - pd.Timedelta(days=PRE_WINDOW_DAYS)].copy()

    primary_results: list[ModelResult] = []
    full_results: list[ModelResult] = []
    for outcome, spec in OUTCOME_SPECS.items():
        for frame, label, sink in [
            (primary, f"[-{PRE_WINDOW_DAYS}, +{POST_WINDOW_DAYS}] days", primary_results),
            (full, f"[-{PRE_WINDOW_DAYS}, full post]", full_results),
        ]:
            model = fit_its(frame, outcome)
            sink.append(
                ModelResult(
                    outcome=outcome,
                    label=spec["label"],
                    window=label,
                    level_coef=float(model.params["post"]),
                    level_p=float(model.pvalues["post"]),
                    slope_coef=float(model.params["time_after"]),
                    slope_p=float(model.pvalues["time_after"]),
                    nobs=int(model.nobs),
                    r2=float(model.rsquared),
                )
            )
    return primary_results, full_results


def chow_test(df: pd.DataFrame, outcome: str) -> ChowResult:
    def design(frame: pd.DataFrame) -> pd.DataFrame:
        weekday_dummies = pd.get_dummies(frame["weekday"], prefix="weekday", drop_first=True, dtype=float)
        x = pd.concat([frame[["time"]].astype(float).reset_index(drop=True), weekday_dummies.reset_index(drop=True)], axis=1)
        return sm.add_constant(x)

    pre = df[df["date"] < EVENT_DATE].copy()
    post = df[df["date"] >= EVENT_DATE].copy()
    pooled_model = sm.OLS(df[outcome].astype(float).reset_index(drop=True), design(df)).fit()
    pre_model = sm.OLS(pre[outcome].astype(float).reset_index(drop=True), design(pre)).fit()
    post_model = sm.OLS(post[outcome].astype(float).reset_index(drop=True), design(post)).fit()

    ssr_pooled = float(np.sum(pooled_model.resid**2))
    ssr_pre = float(np.sum(pre_model.resid**2))
    ssr_post = float(np.sum(post_model.resid**2))
    k = int(pooled_model.df_model + 1)
    n_pre = len(pre)
    n_post = len(post)
    numerator = (ssr_pooled - (ssr_pre + ssr_post)) / k
    denominator = (ssr_pre + ssr_post) / (n_pre + n_post - 2 * k)
    f_stat = numerator / denominator
    p_value = stats.f.sf(f_stat, k, n_pre + n_post - 2 * k)
    return ChowResult(
        outcome=outcome,
        label=OUTCOME_SPECS[outcome]["label"],
        window=f"[-{PRE_WINDOW_DAYS}, +{POST_WINDOW_DAYS}] days",
        f_stat=float(f_stat),
        p_value=float(p_value),
        n_pre=n_pre,
        n_post=n_post,
    )


def run_chow_tests(master: pd.DataFrame) -> list[ChowResult]:
    window = analysis_window(master, POST_WINDOW_DAYS)
    return [chow_test(window, outcome) for outcome in OUTCOME_SPECS]


def event_study_summary(master: pd.DataFrame) -> pd.DataFrame:
    window = analysis_window(master, POST_WINDOW_DAYS)
    baseline = window[(window["event_time"] >= -PRE_WINDOW_DAYS) & (window["event_time"] <= -1)]
    rows = []
    periods = {
        "pre_baseline": (-PRE_WINDOW_DAYS, -1),
        "post_0_30": (0, 30),
        "post_31_90": (31, 90),
        "post_91_180": (91, 180),
    }
    for outcome, spec in OUTCOME_SPECS.items():
        base_mean = baseline[outcome].mean()
        for period, (start, end) in periods.items():
            sub = window[(window["event_time"] >= start) & (window["event_time"] <= end)]
            mean_value = sub[outcome].mean()
            if spec["kind"] == "log_count":
                change = 100 * (np.exp(mean_value - base_mean) - 1)
                unit = "percent"
            else:
                change = mean_value - base_mean
                unit = "level"
            rows.append(
                {
                    "outcome": outcome,
                    "label": spec["label"],
                    "period": period,
                    "mean": mean_value,
                    "baseline_mean": base_mean,
                    "change_vs_baseline": change,
                    "unit": unit,
                    "nobs": len(sub),
                }
            )
    return pd.DataFrame(rows)


def plot_event_study(master: pd.DataFrame) -> Path:
    window = analysis_window(master, POST_WINDOW_DAYS)
    baseline = window[(window["event_time"] >= -PRE_WINDOW_DAYS) & (window["event_time"] <= -1)]
    plot_outcomes = [
        "ln_bab_el_mandeb_n_total",
        "ln_suez_n_total",
        "ln_cape_good_hope_n_total",
        "rerouting_index_total",
    ]
    fig, axes = plt.subplots(2, 2, figsize=(13, 8), sharex=True)
    axes = axes.ravel()
    for ax, outcome in zip(axes, plot_outcomes):
        spec = OUTCOME_SPECS[outcome]
        daily = window[["event_time", outcome]].copy()
        baseline_mean = baseline[outcome].mean()
        if spec["kind"] == "log_count":
            daily["effect"] = 100 * (np.exp(daily[outcome] - baseline_mean) - 1)
            ax.axhline(0, color="black", linewidth=0.8)
        else:
            daily["effect"] = daily[outcome] - baseline_mean
            ax.axhline(0, color="black", linewidth=0.8)
        smooth = daily.set_index("event_time")["effect"].rolling(7, center=True, min_periods=3).mean()
        ax.plot(daily["event_time"], daily["effect"], alpha=0.25, linewidth=0.9)
        ax.plot(smooth.index, smooth.values, linewidth=2.0)
        ax.axvline(0, color="crimson", linestyle="--", linewidth=1.2)
        ax.set_title(spec["plot_label"], fontproperties=CHINESE_FONT)
        ax.grid(True, alpha=0.25)
    fig.supxlabel("相对 2023-11-19 的天数", fontproperties=CHINESE_FONT)
    fig.suptitle("红海危机升级节点事件研究：相对断点前基准变化", fontproperties=CHINESE_FONT, fontsize=14)
    fig.tight_layout()
    output = PLOT_DIR / "red_sea_event_study_2023_11_19.png"
    fig.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output


def plot_its(master: pd.DataFrame) -> Path:
    window = analysis_window(master, POST_WINDOW_DAYS)
    plot_outcomes = [
        "ln_suez_n_total",
        "ln_cape_good_hope_n_total",
        "rerouting_index_total",
    ]
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    for ax, outcome in zip(axes, plot_outcomes):
        spec = OUTCOME_SPECS[outcome]
        fitted = fit_counterfactual(window, outcome)
        ax.plot(fitted["date"], fitted[outcome], color="0.55", alpha=0.55, linewidth=1.0, label="观测值")
        ax.plot(fitted["date"], fitted["fitted"], color="#1f77b4", linewidth=2.0, label="ITS拟合")
        ax.plot(fitted["date"], fitted["counterfactual"], color="#d62728", linestyle="--", linewidth=1.8, label="无升级反事实趋势")
        ax.axvline(EVENT_DATE, color="crimson", linestyle=":", linewidth=1.3)
        ax.set_title(spec["label"], fontproperties=CHINESE_FONT)
        ax.grid(True, alpha=0.25)
        ax.legend(prop=CHINESE_FONT, loc="best")
    fig.suptitle("中断时间序列：2023-11-19 断点前后水平与斜率变化", fontproperties=CHINESE_FONT, fontsize=14)
    fig.tight_layout()
    output = PLOT_DIR / "red_sea_interrupted_time_series_2023_11_19.png"
    fig.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output


def plot_structural_break(master: pd.DataFrame) -> Path:
    window = analysis_window(master, POST_WINDOW_DAYS)
    outcomes = ["ln_suez_n_total", "ln_cape_good_hope_n_total", "rerouting_index_total"]
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    for ax, outcome in zip(axes, outcomes):
        spec = OUTCOME_SPECS[outcome]
        pre = window[window["date"] < EVENT_DATE]
        post = window[window["date"] >= EVENT_DATE]
        for frame, color, label in [(pre, "#2ca02c", "断点前线性趋势"), (post, "#ff7f0e", "断点后线性趋势")]:
            x = sm.add_constant(frame[["time"]].astype(float))
            model = sm.OLS(frame[outcome].astype(float), x).fit()
            ax.plot(frame["date"], frame[outcome], color="0.75", alpha=0.5, linewidth=0.8)
            ax.plot(frame["date"], model.predict(x), color=color, linewidth=2.0, label=label)
        ax.axvline(EVENT_DATE, color="crimson", linestyle=":", linewidth=1.3)
        ax.set_title(spec["label"], fontproperties=CHINESE_FONT)
        ax.grid(True, alpha=0.25)
        ax.legend(prop=CHINESE_FONT, loc="best")
    fig.suptitle("结构突变诊断：断点前后趋势分段拟合", fontproperties=CHINESE_FONT, fontsize=14)
    fig.tight_layout()
    output = PLOT_DIR / "red_sea_structural_break_2023_11_19.png"
    fig.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output


def to_markdown_table(df: pd.DataFrame, float_cols: list[str]) -> str:
    out = df.copy()
    for col in float_cols:
        out[col] = out[col].map(lambda value: f"{value:.4f}")
    columns = list(out.columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for _, row in out.iterrows():
        values = [str(row[column]) for column in columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def write_results(
    event_summary: pd.DataFrame,
    primary_results: list[ModelResult],
    full_results: list[ModelResult],
    chow_results: list[ChowResult],
    plots: list[Path],
) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    its_primary = pd.DataFrame([r.__dict__ for r in primary_results])
    its_full = pd.DataFrame([r.__dict__ for r in full_results])
    chow = pd.DataFrame([r.__dict__ for r in chow_results])

    lines = [
        "# 2023-11-19 红海危机升级节点因果识别补充结果",
        "",
        f"断点日期：{EVENT_DATE.date()}，对应 Galaxy Leader 劫持和胡塞武装对商业船舶袭击升级节点。",
        "",
        "## 1. 事件研究窗口均值变化",
        "",
        "变化值以断点前 49 天为基准。对数通行量转换为百分比变化，比例类变量保留水平差。",
        "",
        to_markdown_table(
            event_summary[
                [
                    "label",
                    "period",
                    "change_vs_baseline",
                    "unit",
                    "nobs",
                ]
            ],
            ["change_vs_baseline"],
        ),
        "",
        "## 2. 中断时间序列结果",
        "",
        "模型：`Y_t = beta0 + beta1*time + beta2*post + beta3*time_after + weekday FE + error`，标准误使用 HAC/Newey-West，最大滞后 14 天。",
        "",
        "### 主窗口：断点前 49 天至断点后 180 天",
        "",
        to_markdown_table(
            its_primary[
                [
                    "label",
                    "level_coef",
                    "level_p",
                    "slope_coef",
                    "slope_p",
                    "nobs",
                    "r2",
                ]
            ],
            ["level_coef", "level_p", "slope_coef", "slope_p", "r2"],
        ),
        "",
        "### 敏感性窗口：断点前 49 天至样本结束",
        "",
        to_markdown_table(
            its_full[
                [
                    "label",
                    "level_coef",
                    "level_p",
                    "slope_coef",
                    "slope_p",
                    "nobs",
                    "r2",
                ]
            ],
            ["level_coef", "level_p", "slope_coef", "slope_p", "r2"],
        ),
        "",
        "## 3. Chow 结构突变检验",
        "",
        "检验断点前后 `Y_t ~ time + weekday FE` 的系数是否整体相同。低 p 值表示断点前后关系存在结构性差异。",
        "",
        to_markdown_table(
            chow[["label", "f_stat", "p_value", "n_pre", "n_post"]],
            ["f_stat", "p_value"],
        ),
        "",
        "## 4. 输出图表",
        "",
    ]
    for plot in plots:
        lines.append(f"- `{plot.relative_to(PROJECT_ROOT)}`")
    lines.extend(
        [
            "",
            "## 5. 解释边界",
            "",
            "本补充分析把 2023-11-19 作为外生冲击断点，能比 VAR 更清楚地比较断点前后趋势变化。由于 PortWatch 当前样本从 2023-10-01 开始，断点前窗口只有 49 天，因此结果应解释为准实验式的探索性证据。若要进一步增强因果识别，需要更长前置期、对照航线或运价/保险等机制变量。",
            "",
        ]
    )
    RESULTS_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    PLOT_DIR.mkdir(exist_ok=True)
    configure_plots()
    master = load_master_data()

    event_summary = event_study_summary(master)
    primary_results, full_results = run_its_models(master)
    chow_results = run_chow_tests(master)
    plots = [
        plot_event_study(master),
        plot_its(master),
        plot_structural_break(master),
    ]
    write_results(event_summary, primary_results, full_results, chow_results, plots)

    print(f"Saved results: {RESULTS_MD}")
    for plot in plots:
        print(f"Saved plot: {plot}")


if __name__ == "__main__":
    main()
