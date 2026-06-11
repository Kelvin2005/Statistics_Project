from pathlib import Path
import warnings

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PLOT_DIR = PROJECT_ROOT / "plot"
ACLED_PATH = PROJECT_ROOT / "data" / "acled_data" / "red_sea_yemen_houthi_related_2023_plus_limit30000.csv"
PORTWATCH_PATH = PROJECT_ROOT / "data" / "portwatch" / "portwatch_red_sea_analysis.csv"
CHINESE_FONT = FontProperties(fname="/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf")

VIOLENT_TYPES = [
    "Explosions/Remote violence",
    "Battles",
    "Violence against civilians",
    "Strategic developments",
]

CHOKEPOINT_COLUMNS = {
    "Suez Canal": "suez_n_total",
    "Bab el-Mandeb Strait": "bab_el_mandeb_n_total",
    "Cape of Good Hope": "cape_good_hope_n_total",
}


def configure_plot_style() -> None:
    warnings.filterwarnings("ignore", message="Glyph .* missing from font")
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.dpi"] = 120


def plot_acled_location_events(top_n: int = 6) -> Path:
    df = pd.read_csv(ACLED_PATH, parse_dates=["event_date"])
    df = df[df["event_type"].isin(VIOLENT_TYPES)].copy()

    locations = df["location"].value_counts().head(top_n).index.tolist()
    weekly = (
        df[df["location"].isin(locations)]
        .assign(week=lambda frame: frame["event_date"].dt.to_period("W").dt.start_time)
        .groupby(["week", "location"])
        .size()
        .unstack(fill_value=0)
        .sort_index()
    )

    fig, ax = plt.subplots(figsize=(13, 7))
    weekly.plot(ax=ax, linewidth=1.8)
    ax.set_title("重点地点安全事件周度数量变化", fontproperties=CHINESE_FONT)
    ax.set_xlabel("日期", fontproperties=CHINESE_FONT)
    ax.set_ylabel("事件数量", fontproperties=CHINESE_FONT)
    ax.grid(True, alpha=0.3)
    legend = ax.legend(title="地点", ncol=2)
    legend.get_title().set_fontproperties(CHINESE_FONT)
    fig.tight_layout()

    output_path = PLOT_DIR / "acled_top_locations_weekly_events.png"
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_portwatch_ship_counts() -> Path:
    df = pd.read_csv(PORTWATCH_PATH, parse_dates=["date"])
    weekly = (
        df.set_index("date")[list(CHOKEPOINT_COLUMNS.values())]
        .resample("W")
        .sum()
        .rename(columns={value: key for key, value in CHOKEPOINT_COLUMNS.items()})
    )

    fig, ax = plt.subplots(figsize=(13, 7))
    weekly.plot(ax=ax, linewidth=2.0)
    ax.set_title("主要航道通航船只数量周度变化", fontproperties=CHINESE_FONT)
    ax.set_xlabel("日期", fontproperties=CHINESE_FONT)
    ax.set_ylabel("通航船只数量", fontproperties=CHINESE_FONT)
    ax.grid(True, alpha=0.3)
    legend = ax.legend(title="航道位置")
    legend.get_title().set_fontproperties(CHINESE_FONT)
    fig.tight_layout()

    output_path = PLOT_DIR / "portwatch_chokepoints_weekly_ship_counts.png"
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output_path


def main() -> None:
    PLOT_DIR.mkdir(exist_ok=True)
    configure_plot_style()
    acled_output = plot_acled_location_events()
    portwatch_output = plot_portwatch_ship_counts()
    print(f"Saved ACLED plot: {acled_output}")
    print(f"Saved PortWatch plot: {portwatch_output}")


if __name__ == "__main__":
    main()
