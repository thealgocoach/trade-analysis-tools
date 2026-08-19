"""
Charts for the Best Times checker.

All figures are sized and styled to stay readable when they end up in a video
or on a phone. Nothing here needs seaborn, so the tool keeps a short list of
requirements.
"""

import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# ---------------------------------------------------------------------------
# One look for every chart
# ---------------------------------------------------------------------------
INK = '#1c2733'
MUTED = '#7c8b9a'
GRID = '#e2e8ee'
UP_COLOUR = '#1f9d76'
DOWN_COLOUR = '#c8503f'
ACCENT = '#2a6fb5'
WARN = '#c8503f'

HEAT = LinearSegmentedColormap.from_list(
    'heat', ['#f4f7fa', '#c9dcec', '#7fb2d8', '#3d7fb8', '#1b4f80'])

plt.rcParams.update({
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
    'axes.edgecolor': GRID,
    'axes.labelcolor': INK,
    'axes.titlecolor': INK,
    'axes.titlesize': 19,
    'axes.titleweight': 'bold',
    'axes.labelsize': 13,
    'axes.grid': True,
    'grid.color': GRID,
    'grid.linewidth': 0.9,
    'xtick.color': MUTED,
    'ytick.color': MUTED,
    'xtick.labelsize': 10,
    'ytick.labelsize': 11,
    'legend.frameon': False,
    'legend.fontsize': 12,
    'font.size': 12,
    'savefig.dpi': 120,
    'savefig.bbox': 'tight',
})


def _tidy(ax):
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    ax.set_axisbelow(True)


def _mark_sessions(ax, slot_labels, sessions):
    """Shade named parts of the day so the shape has context."""
    lookup = {s: i for i, s in enumerate(slot_labels)}
    for name, start, end, colour in sessions:
        if start in lookup and end in lookup:
            ax.axvspan(lookup[start] - 0.5, lookup[end] + 0.5,
                       color=colour, alpha=0.13, zorder=0, lw=0)
            mid = (lookup[start] + lookup[end]) / 2
            ax.annotate(name.upper(), xy=(mid, 0.955),
                        xycoords=('data', 'axes fraction'),
                        ha='center', va='top', fontsize=12, color=MUTED,
                        fontweight='bold', alpha=0.85)


def travel_distance(out_dir, table, hours, sessions):
    """The hero chart. How far price travels after each time of day."""
    t = table.sort_index()
    labels = t.index.astype(str).tolist()
    x = np.arange(len(t))

    fig, ax = plt.subplots(figsize=(19, 8))
    ax.fill_between(x, 0, t['UP 1 IN 4 DAYS'], color=UP_COLOUR, alpha=0.16,
                    lw=0, label='up, best day in four')
    ax.fill_between(x, 0, -t['DOWN 1 IN 4 DAYS'], color=DOWN_COLOUR, alpha=0.16,
                    lw=0, label='down, best day in four')
    ax.plot(x, t['UP HALF DAYS'], color=UP_COLOUR, lw=2.8,
            label='up, half of all days')
    ax.plot(x, -t['DOWN HALF DAYS'], color=DOWN_COLOUR, lw=2.8,
            label='down, half of all days')
    ax.axhline(0, color=INK, lw=1.1)

    _mark_sessions(ax, labels, sessions)

    best = t['UP HALF DAYS'].idxmax()
    quiet = t['UP HALF DAYS'].idxmin()
    for slot, note in ((best, 'busiest'), (quiet, 'quietest')):
        i = labels.index(str(slot))
        ax.annotate(f"{note}  {slot}\n{int(t.loc[slot, 'UP HALF DAYS'])} pts",
                    xy=(i, t.loc[slot, 'UP HALF DAYS']),
                    xytext=(i, t['UP 1 IN 4 DAYS'].max() * 0.80),
                    ha='center', fontsize=11, color=INK, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.35', fc='white',
                              ec=GRID, lw=1),
                    arrowprops=dict(arrowstyle='-', color=MUTED, lw=1.2))

    ax.set_title(f'How far price travels in the {hours} hours after each entry time')
    ax.set_ylabel('Points from entry')
    ax.set_xlabel('Entry time (broker server time)')
    ax.margins(y=0.10)
    ax.set_xticks(x[::2])
    ax.set_xticklabels(labels[::2], rotation=90)
    ax.legend(loc='lower center', ncol=4, bbox_to_anchor=(0.5, -0.30))
    _tidy(ax)
    fig.savefig(os.path.join(out_dir, '01_travel_distance.png'))
    plt.close(fig)


def ratio_by_time(out_dir, table, all_day_ratio, side, target, stop, sessions):
    """Which hours come closest to paying for themselves."""
    t = table.sort_index()
    labels = t.index.astype(str).tolist()
    x = np.arange(len(t))
    ratio = t['RATIO'].to_numpy()

    colours = [ACCENT if r >= all_day_ratio else '#b9c6d3' for r in ratio]

    fig, ax = plt.subplots(figsize=(19, 8))
    ax.bar(x, ratio, color=colours, width=0.78)
    ax.axhline(1.0, color=WARN, lw=2.2, ls='--',
               label='1.00  target arrives often enough to cover the risk')
    ax.axhline(all_day_ratio, color=INK, lw=1.8, ls=':',
               label=f'{all_day_ratio:.3f}  same test with no time filter')

    _mark_sessions(ax, labels, sessions)

    top = t['RATIO'].idxmax()
    i = labels.index(str(top))
    ax.annotate(f"{top}\n{t.loc[top, 'RATIO']:.3f}",
                xy=(i, t.loc[top, 'RATIO']), xytext=(i, max(1.05, ratio.max() * 1.06)),
                ha='center', fontsize=12, fontweight='bold', color=INK,
                arrowprops=dict(arrowstyle='-', color=MUTED, lw=1))

    ax.set_title(f'How close each entry time comes to covering its own risk\n'
                 f'{side}, target {target}, stop {stop}')
    ax.set_ylabel('RATIO   (% win divided by % win needed)')
    ax.set_xlabel('Entry time (broker server time)')
    ax.set_ylim(0, max(1.12, ratio.max() * 1.16))
    ax.set_xticks(x[::2])
    ax.set_xticklabels(labels[::2], rotation=90)
    ax.legend(loc='lower center', ncol=2, bbox_to_anchor=(0.5, -0.30))
    _tidy(ax)
    fig.savefig(os.path.join(out_dir, f'02_ratio_by_time_{side}.png'))
    plt.close(fig)


def ratio_grid(out_dir, combos, side, mode, min_rr):
    """Every target against every stop, coloured by RATIO."""
    d = combos[combos['SIDE'] == side.upper()].copy()
    if d.empty:
        return
    grid = d.pivot_table(index='_t', columns='_s', values='RATIO')
    grid = grid.sort_index(ascending=False)

    fig, ax = plt.subplots(figsize=(max(11, 0.62 * len(grid.columns)),
                                    max(7, 0.52 * len(grid.index))))
    data = grid.to_numpy(dtype=float)
    im = ax.imshow(data, cmap=HEAT, aspect='auto',
                   vmin=np.nanmin(data), vmax=np.nanmax(data))

    ax.set_xticks(range(len(grid.columns)))
    ax.set_yticks(range(len(grid.index)))
    unit = '%' if mode == 'percent' else ''
    ax.set_xticklabels([f"{c}{unit}" for c in grid.columns], rotation=0)
    ax.set_yticklabels([f"{r}{unit}" for r in grid.index])
    ax.grid(False)

    hi = np.nanmax(data)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            v = data[i, j]
            if np.isnan(v):
                continue
            strong = v > (np.nanmin(data) + hi) / 2
            ax.text(j, i, f"{v:.2f}", ha='center', va='center', fontsize=9,
                    color='white' if strong else INK,
                    fontweight='bold' if v == hi else 'normal')

    best = np.unravel_index(np.nanargmax(data), data.shape)
    ax.add_patch(plt.Rectangle((best[1] - .5, best[0] - .5), 1, 1,
                               fill=False, edgecolor=WARN, lw=3))

    ax.set_title(f'RATIO for every target and stop  ({side}, '
                 f'{"percent of price" if mode == "percent" else "points"})\n'
                 f'blank cells are below {min_rr}:1 risk to reward')
    ax.set_xlabel('Stop')
    ax.set_ylabel('Target')
    fig.colorbar(im, ax=ax, shrink=0.8, label='RATIO  (1.00 covers the risk)')
    fig.savefig(os.path.join(out_dir, f'03_ratio_grid_{mode}_{side}.png'))
    plt.close(fig)


def consistency_heatmap(out_dir, pivot, title, filename, baseline):
    """Slots down the side, periods across the top, colour is % win."""
    if pivot.empty:
        return
    data = pivot.to_numpy(dtype=float)

    fig, ax = plt.subplots(figsize=(max(9, 1.35 * data.shape[1] + 4),
                                    max(5, 0.55 * data.shape[0] + 2)))
    im = ax.imshow(data, cmap=HEAT, aspect='auto')
    ax.set_xticks(range(data.shape[1]))
    ax.set_xticklabels(pivot.columns, rotation=0, fontsize=12)
    ax.set_yticks(range(data.shape[0]))
    ax.set_yticklabels(pivot.index, fontsize=12)
    ax.grid(False)

    mid = (np.nanmin(data) + np.nanmax(data)) / 2
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            v = data[i, j]
            if np.isnan(v):
                continue
            ax.text(j, i, f"{v:.1f}", ha='center', va='center', fontsize=11,
                    color='white' if v > mid else INK,
                    fontweight='bold' if v >= baseline else 'normal')

    ax.set_title(f'{title}\nbold means above the no-filter figure of {baseline:.2f}%')
    fig.colorbar(im, ax=ax, shrink=0.85, label='% win')
    fig.savefig(os.path.join(out_dir, filename))
    plt.close(fig)


def dashboard(out_dir, travel, slot_table, all_day_ratio, combos_pts,
              combos_pct, side, target, stop, hours, headline_lines,
              sessions=()):
    """One page you can screenshot."""
    fig = plt.figure(figsize=(19, 12))
    gs = fig.add_gridspec(3, 2, height_ratios=[0.34, 1, 1], hspace=0.52,
                          wspace=0.22)

    # headline numbers
    ax0 = fig.add_subplot(gs[0, :])
    ax0.axis('off')
    ax0.text(0, 0.95, 'BEST TIMES TO INITIATE A TRADE', fontsize=25,
             fontweight='bold', color=INK, va='top')
    ax0.text(0, 0.34, '     '.join(headline_lines), fontsize=13, color=MUTED,
             va='top')

    # travel distance
    t = travel.sort_index()
    x = np.arange(len(t))
    ax1 = fig.add_subplot(gs[1, :])
    ax1.plot(x, t['UP HALF DAYS'], color=UP_COLOUR, lw=2.4, label='up')
    ax1.plot(x, -t['DOWN HALF DAYS'], color=DOWN_COLOUR, lw=2.4, label='down')
    ax1.fill_between(x, 0, t['UP HALF DAYS'], color=UP_COLOUR, alpha=0.14, lw=0)
    ax1.fill_between(x, 0, -t['DOWN HALF DAYS'], color=DOWN_COLOUR, alpha=0.14, lw=0)
    ax1.axhline(0, color=INK, lw=1)
    _mark_sessions(ax1, t.index.astype(str).tolist(), sessions)
    ax1.set_title(f'Travel distance, {hours}h after entry (half of all days reached this far)',
                  fontsize=15)
    ax1.set_ylabel('Points')
    ax1.set_xticks(x[::4])
    ax1.set_xticklabels(t.index.astype(str)[::4], rotation=90, fontsize=9)
    ax1.legend(ncol=2, loc='upper right')
    _tidy(ax1)

    # ratio by time
    st = slot_table.sort_index()
    xr = np.arange(len(st))
    ax2 = fig.add_subplot(gs[2, 0])
    colours = [ACCENT if r >= all_day_ratio else '#b9c6d3' for r in st['RATIO']]
    ax2.bar(xr, st['RATIO'], color=colours, width=0.8)
    ax2.axhline(1.0, color=WARN, lw=1.8, ls='--')
    ax2.axhline(all_day_ratio, color=INK, lw=1.4, ls=':')
    ax2.set_title(f'RATIO by entry time  ({side} {target}/{stop})', fontsize=15)
    ax2.set_ylabel('RATIO')
    ax2.set_xticks(xr[::6])
    ax2.set_xticklabels(st.index.astype(str)[::6], rotation=90, fontsize=9)
    _tidy(ax2)

    # best ratio by risk reward, both modes
    ax3 = fig.add_subplot(gs[2, 1])
    for combos, label, colour in ((combos_pts, 'points', ACCENT),
                                  (combos_pct, 'percent of price', UP_COLOUR)):
        d = combos[combos['SIDE'] == side.upper()].copy()
        if d.empty:
            continue
        # Bin risk to reward into whole steps, otherwise the line is all spikes.
        d['rr'] = np.floor(d['_t'] / d['_s']).astype(int)
        best = d.groupby('rr')['RATIO'].max()
        ax3.plot(best.index, best.values, lw=2.6, color=colour, label=label,
                 marker='o', ms=4)
    ax3.axhline(1.0, color=WARN, lw=1.8, ls='--', label='covers the risk')
    ax3.set_title('Best RATIO reachable at each risk to reward', fontsize=15)
    ax3.set_xlabel('Risk to reward (whole steps)')
    ax3.set_ylabel('Best RATIO')
    ax3.legend()
    _tidy(ax3)

    fig.savefig(os.path.join(out_dir, '00_dashboard.png'))
    plt.close(fig)
