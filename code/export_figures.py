
"""Rebuild manuscript figures and export the exact plotted observations."""
from pathlib import Path
from datetime import datetime
from calendar import monthrange
import csv
import json
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FuncFormatter

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "manuscript/figures"
QA = ROOT / "audit/figure-qa"
SOURCE = FIG / "source_data"
for directory in (FIG, QA, SOURCE):
    directory.mkdir(parents=True, exist_ok=True)

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Liberation Sans", "Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 8.5,
    "axes.labelsize": 8.5,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "axes.spines.right": False,
    "axes.spines.top": False,
    "axes.linewidth": 0.6,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "pdf.fonttype": 42,
    "svg.fonttype": "none",
})
width_mm = 165
height_mm = 100
COLORS={'QQQ':'#555555','RegimeRule':'#0072B2','BoydSimple':'#D55E00'}
with (ROOT / "outputs/monthly_paths_weights.csv").open(encoding="utf-8-sig") as handle:
    records = list(csv.DictReader(handle))
labels = {
    "QQQ": ("QQQ: Buy and hold", "-"),
    "RegimeRule": ("R: State rule", "--"),
    "BoydSimple": ("M: Optimizer", "-."),
}
paths = {}
export_rows = []
for key in labels:
    selected = [row for row in records if row["strategy"] == key]
    assert len(selected) == 321
    dates = [datetime(1999, 12, 31)]
    for row in selected:
        year, month = map(int, row["return_month"].split("-"))
        dates.append(datetime(year, month, monthrange(year, month)[1]))
    wealth = np.r_[100_000.0, [float(row["nav"]) for row in selected]]
    if not np.isfinite(wealth).all() or np.any(wealth <= 0):
        raise ValueError("Log wealth requires finite, strictly positive observations.")
    drawdown = 100 * (wealth / np.maximum.accumulate(wealth) - 1)
    paths[key] = dates, wealth, drawdown
    for date, value, loss in zip(dates, wealth, drawdown):
        export_rows.append({
            "date": date.strftime("%Y-%m-%d"),
            "strategy": key,
            "wealth_usd": float(value),
            "drawdown_percent": float(loss),
        })
with (SOURCE / "wealth_drawdown.csv").open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(export_rows[0]))
    writer.writeheader()
    writer.writerows(export_rows)

contracts = {}
def export(fig, ax, name, contract):
    fig.canvas.draw()
    # Single plot area per figure. Inter-panel alignment is not applicable.
    bbox = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
    alignment = {
        "verdict": "NOT APPLICABLE",
        "reason": "One rendered plot area; no multi-panel comparison.",
        "plot_area_inches": list(bbox.bounds),
        "figure_width_mm": width_mm,
        "figure_height_mm": height_mm,
    }
    (QA / f"{name}.alignment.json").write_text(json.dumps(alignment, indent=2))
    fig.savefig(FIG / f"{name}.pdf", metadata={"Author": "Yudian Pan"})
    fig.savefig(FIG / f"{name}.svg")
    fig.savefig(FIG / f"{name}.png", dpi=600)
    fig.savefig(FIG / f"{name}.tiff", dpi=600, pil_kwargs={"compression": "tiff_lzw"})
    contracts[name] = contract
    plt.close(fig)

for kind in ("wealth", "drawdown"):
    fig, ax = plt.subplots(figsize=(width_mm / 25.4, height_mm / 25.4))
    fig.subplots_adjust(left=0.145, right=0.975, bottom=0.17, top=0.84)
    for key, (label, linestyle) in labels.items():
        dates, wealth, drawdown = paths[key]
        values = wealth if kind == "wealth" else drawdown
        ax.plot(dates, values, label=label, linestyle=linestyle, linewidth=1.05, color=COLORS[key])
    ax.set_xlabel("Month")
    if kind == "wealth":
        ax.set_yscale("log")
        ax.set_ylim(15000, 2300000)
        ax.yaxis.set_major_locator(FixedLocator([20000, 50000, 100000, 250000, 500000, 1000000, 2000000]))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:,.0f}"))
        ax.minorticks_off()
        ax.set_ylabel("Portfolio value (USD; logarithmic scale)")
        claim = "Compounded wealth advantages depend on the historical market path."
    else:
        ax.set_ylim(-85, 3)
        ax.set_yticks([-80, -60, -40, -20, 0])
        ax.set_ylabel("Drawdown from prior month-end high (%)")
        claim = "Both dynamic methods reduce the largest month-end losses in this sample."
    ax.set_xlim(datetime(1999, 12, 31), datetime(2027, 3, 1))
    handles, texts = ax.get_legend_handles_labels()
    fig.legend(handles, texts, loc="upper center", bbox_to_anchor=(0.56, 0.97),
               ncol=3, frameon=False, handlelength=2.8, columnspacing=1.2)
    export(fig, ax, kind, {
        "claim": claim,
        "role": "Primary historical comparison" if kind == "wealth" else "Loss-path comparison",
        "backend": "Python / Matplotlib",
        "archetype": "Single quantitative plot",
        "source": "source_data/wealth_drawdown.csv",
        "input_rows": len(records),
        "selected_return_rows": 963,
        "exported_valuation_rows": 966,
        "selection_reason": "Primary methods R and M plus their QQQ benchmark. Other method results remain in the manuscript tables and outputs.",
        "n": "321 monthly returns per strategy; one historical path.",
        "uncertainty": "None on individual realized paths; process uncertainty is reported separately.",
        "transform": "Wealth is plotted on a log axis without smoothing; drawdown uses all prior month-end highs.",
        "interpolation": "Line segments join adjacent monthly observations; no values are inferred between them.",
    })

with (ROOT / "outputs/bootstrap_pipeline_draws.csv").open(encoding="utf-8-sig") as handle:
    draws = list(csv.DictReader(handle))
height_mm = 75
fig, ax = plt.subplots(figsize=(width_mm / 25.4, height_mm / 25.4))
# Reserve the first default style for the QQQ reference used in the other figures.
# This empty artist draws no observation and is not included in a legend.
ax.plot([], [], label="_nolegend_")
fig.subplots_adjust(left=0.24, right=0.965, bottom=0.22, top=0.9)
intervals = []
for position, key in enumerate(("RegimeRule", "BoydSimple")):
    values = np.array([100 * float(row["cagr_difference"]) for row in draws if row["strategy"] == key])
    assert len(values) == 100 and np.isfinite(values).all()
    lower, center, upper = np.quantile(values, [0.025, 0.5, 0.975])
    ax.errorbar(center, position, xerr=np.array([[center-lower], [upper-center]]),
                fmt="o", markersize=4, capsize=3, linewidth=1.0, capthick=0.8, color=COLORS[key])
    intervals.append({"strategy": key, "replications": 100, "median_pp": center,
                      "lower_2_5_percentile_pp": lower, "upper_97_5_percentile_pp": upper})
ax.axvline(0, linestyle=":", linewidth=0.65)
ax.set_yticks([0, 1], ["R: State rule", "M: Optimizer"])
ax.set_ylim(-0.65, 1.65)
ax.invert_yaxis()
ax.set_xlabel("CAGR difference versus QQQ (percentage points)")
ax.set_xlim(-10, 8)
with (SOURCE / "bootstrap_growth_intervals.csv").open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(intervals[0]))
    writer.writeheader()
    writer.writerows(intervals)
with (SOURCE / "bootstrap_growth_draws.csv").open("w", newline="", encoding="utf-8") as handle:
    fields = ["rep", "strategy", "cagr_difference"]
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    writer.writerows({k: row[k] for k in fields} for row in draws)
export(fig, ax, "bootstrap_growth", {
    "claim": "Growth-difference ranges span zero when prices and strategy paths are reconstructed.",
    "role": "Uncertainty and adverse evidence",
    "backend": "Python / Matplotlib",
    "archetype": "Single interval plot",
    "source": "source_data/bootstrap_growth_draws.csv",
    "input_rows": len(draws),
    "used_rows": len(draws),
    "n": "100 paired process-reconstruction replications for each of R and M.",
    "center": "Median",
    "interval": "Empirical 2.5th and 97.5th percentiles of 100 reconstructed paths.",
    "test": "Descriptive resampling range; not a calibrated future interval or significance test.",
    "comparison": "Each reconstructed strategy versus QQQ on the same resampled asset-return path.",
    "multiple_comparison": "No multiplicity claim is made for these descriptive ranges.",
})
with (ROOT/'outputs/rolling_start_metrics.csv').open(encoding='utf-8-sig')as f:
    rolling=list(csv.DictReader(f))
height_mm=90
fig,ax=plt.subplots(figsize=(width_mm/25.4,height_mm/25.4))
fig.subplots_adjust(left=.14,right=.975,bottom=.19,top=.84)
selected=[]
for key in ['RegimeRule','BoydSimple']:
    rs=[r for r in rolling if r['strategy']==key and r['years']=='10'];selected+=rs
    ax.plot([int(r['start'][:4])for r in rs],[100*float(r['cagr_difference'])for r in rs],linestyle=labels[key][1],marker='o'if key=='RegimeRule'else's',markersize=3.4,color=COLORS[key],linewidth=1.1,label=labels[key][0])
ax.axhline(0,color='#555555',linestyle=':',linewidth=.8)
ax.set_xticks(list(range(2000,2017,2)));ax.set_xlabel('January investment start year (10-year windows)')
ax.set_ylabel('CAGR difference versus QQQ (pp)')
fig.legend(*ax.get_legend_handles_labels(),loc='upper center',ncol=2,frameon=False,bbox_to_anchor=(.55,.985))
with (SOURCE/'rolling_growth.csv').open('w',newline='')as f:
    w=csv.DictWriter(f,fieldnames=selected[0].keys());w.writeheader();w.writerows(selected)
export(fig,ax,'rolling_growth',{'claim':'The full-history growth advantage depends on investment start date.','role':'Start-date sensitivity','backend':'Python / Matplotlib','archetype':'Single quantitative plot','source':'source_data/rolling_growth.csv','input_rows':len(rolling),'used_rows':len(selected),'selection_reason':'Show all completed ten-year January starts; all five-year starts remain in the companion table and CSV.','n':'17 overlapping windows per strategy; no independence assumption.','transform':'Difference of separately computed CAGRs, in percentage points.','uncertainty':'Each point is a historical-window result, not a replicate or confidence interval.','interpolation':'Straight segments link adjacent start-year observations; no smoothing.'})
with (ROOT/'outputs/hindsight_static_grid.csv').open(encoding='utf-8-sig')as f:grid=list(csv.DictReader(f))
fig,ax=plt.subplots(figsize=(width_mm/25.4,height_mm/25.4));fig.subplots_adjust(left=.14,right=.975,bottom=.19,top=.84)
ax.scatter([100*float(r['vol'])for r in grid],[100*float(r['cagr'])for r in grid],s=5,c='#A6A6A6',alpha=.55,label='Static grid (1,001)',linewidths=0)
front=sorted([r for r in grid if r['pareto_cagr_vol']=='True'],key=lambda x:float(x['vol']))
ax.plot([100*float(r['vol'])for r in front],[100*float(r['cagr'])for r in front],color='#333333',linestyle=':',linewidth=.9)
with (ROOT/'outputs/metrics.csv').open(encoding='utf-8-sig')as f:met=list(csv.DictReader(f))
source=[dict(kind='static',**r)for r in grid]
for key,mark in [('RegimeRule','o'),('BoydSimple','s')]:
    r=next(r for r in met if r['strategy']==key and r['start']=='2000-01'and r['end']=='2026-09')
    ax.scatter(100*float(r['vol']),100*float(r['cagr']),s=28,color=COLORS[key],marker=mark,label=labels[key][0]);source.append(dict(kind=key,cagr=r['cagr'],vol=r['vol']))
ax.set_xlabel('Annualized monthly volatility (%)');ax.set_ylabel('CAGR (%)')
fig.legend(*ax.get_legend_handles_labels(),loc='upper center',ncol=3,frameon=False,bbox_to_anchor=(.55,.985),columnspacing=1.0)
fields=list(dict.fromkeys(k for r in source for k in r))
with (SOURCE/'hindsight_frontier.csv').open('w',newline='')as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(source)
export(fig,ax,'hindsight_frontier',{'claim':'Observed growth-risk rankings depend on the feasible set and investor objective.','role':'Descriptive feasible-set diagnostic','backend':'Python / Matplotlib','archetype':'Single quantitative plot','source':'source_data/hindsight_frontier.csv','input_rows':len(grid),'used_rows':len(grid),'n':'1,001 10-percentage-point grid allocations; one 321-month history.','transform':'CAGR and annualized sample volatility. Dotted boundary joins non-dominated grid observations.','uncertainty':'No sampling interval; grid selected and ranked with full hindsight.','feasible_set_warning':'Static grid permits 100% gold and 100% reserve, unlike M caps; not an ex-ante efficiency comparison.'})
(QA / "figure_contracts.json").write_text(json.dumps(contracts, indent=2))
print("Exported five vector figures with exact source data and figure contracts.")
