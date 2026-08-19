"""
============================================================================
  BEST TIMES TO INITIATE A TRADE  -  CHECKER v1.3
============================================================================

  WHAT IT DOES
      Looks at every time of day and tells you how far price usually travels
      after that time, and which direction travels further.

      Then it lets you ask "if I had used a 200 point target and a 55 point
      stop, how often would the target have arrived first" for hundreds of
      target and stop combinations, at every time of day.

  WHAT IT IS NOT
      Not a strategy. Not a backtest. Not a signal.
      It tells you WHERE TO LOOK. What you do after that is your decision.

  HOW TO USE IT
      1. Put your M1 history CSV in the same folder as this file.
      2. Change anything you want in the SETTINGS block below.
      3. Run it.
      4. Read analysis_results/summary_report.txt

  YOUR CSV MUST LOOK LIKE THIS (no header row):
      2025.07.18,02:48,21400.50,21405.75,21398.25,21402.00,143
      date,time,open,high,low,close,volume

============================================================================
"""

import os
import glob
import time as _time

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import charts

# ############################################################################
#
#   SETTINGS  -  everything you would want to change is in this block.
#                You should never need to look below it.
#
# ############################################################################

# ---------------------------------------------------------------------------
# HOW LONG TO WATCH
# ---------------------------------------------------------------------------
# After each entry time, how many hours do we watch price for?
# Change this to 4, 8, 12, 24, whatever you want to test.
HOLDING_HOURS = 12

# How often do we test an entry? '15min', '30min', '1h', '5min'.
ENTRY_EVERY = '15min'

# ---------------------------------------------------------------------------
# YOUR TRADING COSTS
# ---------------------------------------------------------------------------
# Enter the spread exactly as MT4 reports it in the symbol specification.
# For NAS100 that is usually around 150.
SPREAD_IN_MT4_POINTS = 150

# One MT4 point, in the units your CSV price column uses.
#   CSV price reads 21400.50  ->  POINT_SIZE = 0.01
#   CSV price reads 21400.5   ->  POINT_SIZE = 0.1
#   CSV price reads 21400     ->  POINT_SIZE = 1.0
POINT_SIZE = 0.01

# Extra allowance for slippage, in MT4 points. 0 if you do not want any.
SLIPPAGE_IN_MT4_POINTS = 0

# ---------------------------------------------------------------------------
# WHAT TARGETS AND STOPS TO TEST  (in price units, e.g. index points)
# ---------------------------------------------------------------------------
# Because of how this tool is built, testing 300 combinations costs the same
# as testing 9. Be generous.
TARGETS_IN_POINTS = list(range(50, 401, 25))     # 50, 75, 100 ... 400
STOPS_IN_POINTS = list(range(15, 101, 5))        # 15, 20, 25 ... 100

# Ignore any pairing below this risk to reward. A 50 point target with a 70
# point stop scores well on paper because it is close to a coin flip, but you
# would be risking more than you stand to make. 2.0 means "at least 2:1".
MIN_RISK_REWARD = 2.0

# ---------------------------------------------------------------------------
# SAME THING AS PERCENTAGES OF PRICE
# ---------------------------------------------------------------------------
# 200 points was a 2.8% move when the NAS was 7,000 and is a 0.9% move at
# 21,000. If your history spans years, the percentage view is the fair one.
TARGETS_IN_PERCENT = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0]
STOPS_IN_PERCENT = [0.05, 0.10, 0.15, 0.20, 0.25, 0.35, 0.50]

# ---------------------------------------------------------------------------
# WHICH COMBINATION TO BREAK DOWN BY TIME OF DAY
# ---------------------------------------------------------------------------
# None = let the tool pick the best scoring one from the table.
# Or set them yourself, e.g. FOCUS_TARGET = 200 / FOCUS_STOP = 55
FOCUS_TARGET = None
FOCUS_STOP = None

# Which side to break down: 'long', 'short', or 'both'.
FOCUS_SIDE = 'both'

# ---------------------------------------------------------------------------
# QUALITY CONTROL
# ---------------------------------------------------------------------------
# A time slot needs at least this share of the busiest slot's day count to be
# ranked. Stops one lucky day at 23:15 topping your table.
# 0.80 means "at least 80% as many days as the busiest slot".
MIN_SHARE_OF_BUSIEST_SLOT = 0.80

# How many rows to print in each ranked table.
ROWS_TO_SHOW = 25

# Parts of the day to shade on the charts, so the shape has context.
# Set to [] if you do not want them. Times are your broker's server time.
SESSIONS = [
    ('Asia',      '01:00', '08:00', '#2a6fb5'),
    ('Europe',    '09:00', '16:15', '#1f9d76'),
    ('US',        '16:30', '23:00', '#d98b2b'),
]

CSV_ENCODING = 'ISO-8859-1'

# ############################################################################
#   END OF SETTINGS
# ############################################################################


WEEKDAY_ORDER = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',
                 'Saturday', 'Sunday']


# ===========================================================================
#  STEP 1  -  measure each day once
# ===========================================================================

def measure_all_days(highs, lows, entry_open, start_pos, end_pos):
    """
    Walk the watch window after every entry, once, and write down:

      max_up / max_down
          The furthest price travelled in each direction. This is the travel
          distance report.

      the "ladder"
          Every time price sets a new best in your favour, we note how far it
          had gone against you up to that moment. So a ladder might read:
                reached +40, worst against you was 12
                reached +90, worst against you was 12
                reached +160, worst against you was 31
          Once we have that, ANY target and stop question is answered by
          reading the ladder. No recalculating. That is why you can test
          hundreds of combinations for free.
    """
    n = len(entry_open)
    max_up = np.zeros(n)
    max_down = np.zeros(n)

    long_reach, long_against = [], []
    short_reach, short_against = [], []
    long_start = np.zeros(n + 1, dtype=np.int64)
    short_start = np.zeros(n + 1, dtype=np.int64)

    report_every = max(1, n // 20)
    NEG = -np.inf

    for k in range(n):
        if k % report_every == 0:
            print(f"    measuring... {k * 100 // n}%", end='\r')

        a, b = start_pos[k], end_pos[k]
        long_start[k], short_start[k] = len(long_reach), len(short_reach)
        if b <= a:
            long_reach.append(np.empty(0, np.float32))
            long_against.append(np.empty(0, np.float32))
            short_reach.append(np.empty(0, np.float32))
            short_against.append(np.empty(0, np.float32))
            continue

        entry = entry_open[k]
        up = highs[a:b] - entry      # how far above entry, bar by bar
        dn = entry - lows[a:b]       # how far below entry, bar by bar

        # Running best so far, in each direction. One numpy call each.
        run_up = np.maximum.accumulate(up)
        run_dn = np.maximum.accumulate(dn)

        max_up[k] = run_up[-1]
        max_down[k] = run_dn[-1]

        # LONG ladder: a rung wherever the up-move sets a new record.
        rungs = np.flatnonzero(np.diff(run_up, prepend=NEG) > 0)
        long_reach.append(run_up[rungs].astype(np.float32))
        long_against.append(run_dn[rungs].astype(np.float32))
        long_start[k + 1] = long_start[k] + len(rungs)

        # SHORT ladder: same thing with the directions swapped.
        rungs = np.flatnonzero(np.diff(run_dn, prepend=NEG) > 0)
        short_reach.append(run_dn[rungs].astype(np.float32))
        short_against.append(run_up[rungs].astype(np.float32))
        short_start[k + 1] = short_start[k] + len(rungs)

    long_start = np.concatenate(([0], np.cumsum([len(a) for a in long_reach])))
    short_start = np.concatenate(([0], np.cumsum([len(a) for a in short_reach])))
    print("    measuring... done      ")

    return {
        'max_up': max_up,
        'max_down': max_down,
        'long': (np.concatenate(long_reach) if long_reach else np.empty(0, np.float32),
                 np.concatenate(long_against) if long_against else np.empty(0, np.float32),
                 long_start),
        'short': (np.concatenate(short_reach) if short_reach else np.empty(0, np.float32),
                  np.concatenate(short_against) if short_against else np.empty(0, np.float32),
                  short_start),
    }


# ===========================================================================
#  STEP 2  -  answer a target/stop question from the ladder
# ===========================================================================

def test_combination(ladder, max_against, target, stop):
    """
    target and stop can each be one number (points) or one number per day
    (which is how percentage mode works, since a percentage of price is a
    different number of points every day).

    Returns an array: 1 = target arrived first
                     -1 = stop was hit first
                      0 = neither happened before the cutoff

    All days are answered in one shot. The ladders sit end to end in one long
    array, so we shift each day's rungs into its own numeric band, which makes
    the whole array increasing and lets one search answer every day at once.
    """
    reach, against, starts = ladder
    n = len(starts) - 1
    out = np.zeros(n, dtype=np.int8)
    if len(reach) == 0:
        return out

    target = np.broadcast_to(np.asarray(target, dtype=np.float64), (n,)).astype(np.float64)
    stop = np.broadcast_to(np.asarray(stop, dtype=np.float64), (n,)).astype(np.float64)

    band = float(max(reach.max(), target.max())) * 2.0 + 1000.0

    seg_id = np.repeat(np.arange(n), np.diff(starts))
    shifted = reach.astype(np.float64) + seg_id * band
    queries = target + np.arange(n) * band

    pos = np.searchsorted(shifted, queries, side='left')
    reached = pos < starts[1:]                 # a rung at or above the target exists

    out_idx = np.where(reached, np.minimum(pos, len(against) - 1), 0)
    adverse_at_target = against[out_idx]

    win = reached & (adverse_at_target < stop)
    loss_on_the_way = reached & ~win
    never_reached = ~reached
    loss_without_target = never_reached & (max_against >= stop)

    out[win] = 1
    out[loss_on_the_way] = -1
    out[loss_without_target] = -1
    return out


# ===========================================================================
#  REPORT PIECES
# ===========================================================================

def travel_distance_table(slots, max_up, max_down, entry_open, min_days):
    """Section 1. How far price travels from each time of day."""
    df = pd.DataFrame({
        'slot': slots,
        'up': max_up,
        'down': max_down,
        'price': entry_open,
    })
    g = df.groupby('slot', observed=True)

    out = pd.DataFrame({
        'DAYS': g.size(),
        'UP HALF DAYS': g['up'].median().round(0),
        'UP 1 IN 4 DAYS': g['up'].quantile(0.75).round(0),
        'DOWN HALF DAYS': g['down'].median().round(0),
        'DOWN 1 IN 4 DAYS': g['down'].quantile(0.75).round(0),
    })

    # The same distances written as a percentage of price, so the figures stay
    # comparable across years when the index itself has moved a long way.
    # Derived from the points columns above, so the two can never disagree.
    typical_price = g['price'].median()
    out['UP HALF %'] = (out['UP HALF DAYS'] / typical_price * 100).round(2)
    out['DOWN HALF %'] = (out['DOWN HALF DAYS'] / typical_price * 100).round(2)

    out['RUNS FURTHER'] = np.where(
        out['DOWN HALF DAYS'] > out['UP HALF DAYS'], 'DOWN',
        np.where(out['UP HALF DAYS'] > out['DOWN HALF DAYS'], 'UP', 'even'))

    out['ENOUGH DAYS'] = np.where(out['DAYS'] >= min_days, 'yes', 'NO')
    return out


def combination_table(measured, cost, targets, stops, mode, entry_open):
    """
    Section 2. Every target and stop combination, all times of day together.

    % WIN         out of 100 tries, how often the target arrived first
    % WIN NEEDED  how often it would have to arrive first to cover the risk
    RATIO         % WIN divided by % WIN NEEDED. Bigger is better.
                  Below 1 means the target did not arrive often enough.
    """
    rows = []
    for side in ('long', 'short'):
        ladder = measured[side]
        max_against = measured['max_down'] if side == 'long' else measured['max_up']

        for t in targets:
            for s in stops:
                if mode == 'percent':
                    t_pts = entry_open * t / 100.0
                    s_pts = entry_open * s / 100.0
                    t_eff = t_pts + cost
                    s_eff = s_pts - cost
                    rr = t / s
                    label_t, label_s = f"{t}%", f"{s}%"
                    needed = s / (t + s) * 100
                else:
                    t_eff = t + cost
                    s_eff = s - cost
                    rr = t / s
                    label_t, label_s = t, s
                    needed = s / (t + s) * 100

                if np.any(np.asarray(s_eff) <= 0) or rr < MIN_RISK_REWARD:
                    continue

                res = test_combination(ladder, max_against, t_eff, s_eff)
                wins = int((res == 1).sum())
                losses = int((res == -1).sum())
                neither = int((res == 0).sum())
                tries = wins + losses + neither
                pct_win = wins / tries * 100 if tries else 0.0

                rows.append({
                    'SIDE': side.upper(),
                    'TARGET': label_t,
                    'STOP': label_s,
                    'R:R': f"{rr:.1f}:1",
                    'TRIES': tries,
                    'TARGET FIRST': wins,
                    'STOP FIRST': losses,
                    'NEITHER': neither,
                    '% WIN': round(pct_win, 2),
                    '% WIN NEEDED': round(needed, 2),
                    'RATIO': round(pct_win / needed, 3) if needed else np.nan,
                    '_t': t, '_s': s,
                })

    return pd.DataFrame(rows).sort_values('RATIO', ascending=False)


def slot_breakdown(measured, slots, side, target_eff, stop_eff, min_days, needed):
    """Section 3. The chosen combination, broken down by time of day."""
    ladder = measured[side]
    max_against = measured['max_down'] if side == 'long' else measured['max_up']
    res = test_combination(ladder, max_against, target_eff, stop_eff)

    df = pd.DataFrame({'slot': slots, 'r': res})
    g = df.groupby('slot', observed=True)['r']

    out = pd.DataFrame({
        'DAYS': g.size(),
        'TARGET FIRST': g.apply(lambda s: int((s == 1).sum())),
        'STOP FIRST': g.apply(lambda s: int((s == -1).sum())),
        'NEITHER': g.apply(lambda s: int((s == 0).sum())),
    })
    out['% WIN'] = (out['TARGET FIRST'] / out['DAYS'] * 100).round(2)
    out['% WIN NEEDED'] = round(needed, 2)
    out['RATIO'] = (out['% WIN'] / needed).round(3)
    out = out[out['DAYS'] >= min_days]

    all_day_pct = (res == 1).sum() / len(res) * 100
    return out.sort_values('RATIO', ascending=False), all_day_pct, res


def consistency(slots, period, res, keep_slots):
    """Same slots, split by year / half of month / weekday."""
    df = pd.DataFrame({'slot': slots, 'period': period, 'r': res})
    df = df[df['slot'].isin(keep_slots)]
    piv = df.pivot_table(index='slot', columns='period', observed=True,
                         values='r',
                         aggfunc=lambda s: round((s == 1).mean() * 100, 2))
    if set(piv.columns) & set(WEEKDAY_ORDER):
        order = [d for d in WEEKDAY_ORDER if d in piv.columns]
        piv = piv[order]
    return piv


# ===========================================================================
#  MAIN
# ===========================================================================

def main():
    t_start = _time.perf_counter()
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(here, 'analysis_results')
    os.makedirs(out_dir, exist_ok=True)

    cost = (SPREAD_IN_MT4_POINTS + SLIPPAGE_IN_MT4_POINTS) * POINT_SIZE

    candidates = [f for f in glob.glob(os.path.join(here, '*.csv'))
                  if 'analysis' not in os.path.basename(f).lower()]
    if not candidates:
        raise FileNotFoundError(f"Put your M1 history CSV next to this file. Looked in {here}")
    csv_path = candidates[0]

    lines = []

    def say(text=''):
        print(text)
        lines.append(str(text))

    say("=" * 100)
    say("  BEST TIMES TO INITIATE A TRADE  -  v1.3")
    say("=" * 100)
    say(f"  Data file        : {os.path.basename(csv_path)}")
    say(f"  Watch window     : {HOLDING_HOURS} hours after entry")
    say(f"  Entry tested     : every {ENTRY_EVERY}")
    say(f"  Cost per trade   : {SPREAD_IN_MT4_POINTS} MT4 points "
        f"+ {SLIPPAGE_IN_MT4_POINTS} slippage = {cost:.2f} in price units")
    say()

    # ---- load ----
    print("Loading price data...")
    df = pd.read_csv(csv_path, header=None,
                     names=['Date', 'Time', 'Open', 'High', 'Low', 'Close', 'Volume'],
                     encoding=CSV_ENCODING)
    df['DateTime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
    df = df.set_index('DateTime').drop(columns=['Date', 'Time']).sort_index()

    entries = df.resample(ENTRY_EVERY).first().dropna()
    total_days = df.index.normalize().nunique()

    say(f"  Price range      : {df['Low'].min():,.2f} to {df['High'].max():,.2f}")
    say(f"  Entries tested   : {len(entries):,} across {total_days:,} days")
    say()

    highs = df['High'].to_numpy(np.float64)
    lows = df['Low'].to_numpy(np.float64)
    bar_times = df.index.to_numpy()

    et = entries.index.to_numpy()
    entry_open = entries['Open'].to_numpy(np.float64)
    start_pos = np.searchsorted(bar_times, et, 'left')
    end_pos = np.searchsorted(bar_times, et + np.timedelta64(HOLDING_HOURS, 'h'), 'right')

    idx = entries.index
    slots = pd.Categorical(idx.strftime('%H:%M'))
    years = idx.year
    month_half = np.where(idx.day <= 15, '1st half', '2nd half')
    weekdays = idx.day_name()

    # ---- measure once ----
    print("Measuring every day (this is the slow part, and it only happens once)...")
    measured = measure_all_days(highs, lows, entry_open, start_pos, end_pos)
    say(f"  Measuring took   : {_time.perf_counter() - t_start:.1f} seconds")
    say()

    day_counts = pd.Series(slots).value_counts()
    min_days = int(day_counts.max() * MIN_SHARE_OF_BUSIEST_SLOT)

    # =======================================================================
    say("=" * 100)
    say("  SECTION 1   HOW FAR PRICE TRAVELS AFTER EACH TIME OF DAY")
    say("=" * 100)
    say("  This is the main question this tool exists to answer.")
    say()
    say(f"  For each time of day, we looked at the {HOLDING_HOURS} hours that followed,")
    say("  on every day in your file, and measured how far price got.")
    say()
    say("    DAYS             how many days in your file had a bar at this time")
    say("    UP HALF DAYS     on half the days, price rose at least this far")
    say("    UP 1 IN 4 DAYS   on one day in four, price rose at least this far")
    say("    DOWN ...         the same, measured downward")
    say("    UP/DOWN HALF %   the HALF DAYS figure as a percentage of price")
    say("    RUNS FURTHER     which direction went further on the average day")
    say()
    say("  Read it like this: a time slot with a big number is capable of producing")
    say("  the move you want. A slot with a small number is not, no matter what")
    say("  target and stop you pick.")
    say()

    travel = travel_distance_table(slots, measured['max_up'], measured['max_down'],
                                  entry_open, min_days)
    ranked_travel = travel[travel['ENOUGH DAYS'] == 'yes'].sort_values(
        ['UP HALF DAYS', 'DOWN HALF DAYS'], ascending=False)

    show_cols = [c for c in ranked_travel.columns if c != 'ENOUGH DAYS']
    say("  FURTHEST TRAVELLING TIMES")
    say(ranked_travel[show_cols].head(ROWS_TO_SHOW).to_string())
    say()
    say("  QUIETEST TIMES")
    say(ranked_travel[show_cols].tail(10).to_string())
    say()

    dropped = travel[travel['ENOUGH DAYS'] == 'NO']
    if len(dropped):
        say(f"  Left out of the ranking, too few days (need {min_days}):")
        for slot, row in dropped.iterrows():
            say(f"    {slot}   {int(row['DAYS'])} days")
        say("  These are almost always the daily break or rollover. Check your")
        say("  broker's trading hours.")
        say()

    # =======================================================================
    for mode, targets, stops, unit in (
            ('points', TARGETS_IN_POINTS, STOPS_IN_POINTS, 'points'),
            ('percent', TARGETS_IN_PERCENT, STOPS_IN_PERCENT, '% of price')):

        print(f"Testing every target and stop combination in {unit}...")
        combos = combination_table(measured, cost, targets, stops, mode, entry_open)

        say("=" * 100)
        say(f"  SECTION 2{'A' if mode == 'points' else 'B'}   "
            f"TARGET AND STOP COMBINATIONS, IN {unit.upper()}")
        say("=" * 100)
        say("  No time filter here. Every time of day pooled together, so you can")
        say("  see which target and stop pairing is worth exploring at all.")
        say()
        say("    TARGET FIRST   the target arrived before the stop")
        say("    STOP FIRST     the stop was hit before the target")
        say(f"    NEITHER        neither happened inside {HOLDING_HOURS} hours")
        say("    % WIN          out of 100 tries, the target arrived first this often")
        say("    % WIN NEEDED   how often it would need to arrive first to cover the risk")
        say("    RATIO          % WIN divided by % WIN NEEDED")
        say()
        say("  RATIO is the column to sort by. It is the only number that lets you")
        say("  compare a tight stop against a wide one fairly, because each pairing")
        say("  is judged against its own bar rather than against the others.")
        say("  Bigger is better. Under 1 means the target did not arrive often enough")
        say("  to pay for the losses.")
        say()

        show = combos.drop(columns=['_t', '_s'])

        say(f"  Only pairings of at least {MIN_RISK_REWARD}:1 risk to reward are shown.")
        say("  A RATIO near 1.00 means the target arrived about as often as it needed")
        say("  to and no more, which is what a market with no edge in it looks like.")
        say("  You are looking for pairings that sit clearly above the rest.")
        say()
        say("  BEST RATIO AT EACH RISK TO REWARD LEVEL")
        band = combos.copy()
        band['RR'] = (band['_t'] / band['_s']).round(1)
        best_band = (band.groupby(['SIDE', 'RR'])
                        .agg(**{'TARGET': ('TARGET', 'first'),
                                'STOP': ('STOP', 'first'),
                                '% WIN': ('% WIN', 'first'),
                                '% WIN NEEDED': ('% WIN NEEDED', 'first'),
                                'RATIO': ('RATIO', 'max')})
                        .reset_index().sort_values(['SIDE', 'RR']))
        say(best_band.to_string(index=False))
        say()
        say(f"  BEST {ROWS_TO_SHOW} BY RATIO")
        say(show.head(ROWS_TO_SHOW).to_string(index=False))
        say()
        say("  WORST 10 BY RATIO")
        say(show.tail(10).to_string(index=False))
        say()

        combos.drop(columns=['_t', '_s']).to_csv(
            os.path.join(out_dir, f'combinations_{mode}.csv'), index=False)

        if mode == 'points':
            best_points = combos.iloc[0]
            combos_points = combos
            charts.ratio_grid(out_dir, combos, 'long', mode, MIN_RISK_REWARD)
            charts.ratio_grid(out_dir, combos, 'short', mode, MIN_RISK_REWARD)
        else:
            combos_percent = combos
            charts.ratio_grid(out_dir, combos, 'long', mode, MIN_RISK_REWARD)
            charts.ratio_grid(out_dir, combos, 'short', mode, MIN_RISK_REWARD)

    # =======================================================================
    if FOCUS_TARGET is not None and FOCUS_STOP is not None:
        focus_t, focus_s = FOCUS_TARGET, FOCUS_STOP
        focus_sides = ['long', 'short'] if FOCUS_SIDE == 'both' else [FOCUS_SIDE]
    else:
        focus_t, focus_s = best_points['_t'], best_points['_s']
        focus_sides = ['long', 'short'] if FOCUS_SIDE == 'both' else [FOCUS_SIDE]

    for side in focus_sides:
        needed = focus_s / (focus_t + focus_s) * 100
        table, all_day, res = slot_breakdown(
            measured, slots, side, focus_t + cost, focus_s - cost, min_days, needed)

        say("=" * 100)
        say(f"  SECTION 3   TIME OF DAY BREAKDOWN   "
            f"TARGET {focus_t} / STOP {focus_s} / {side.upper()}")
        say("=" * 100)
        say("  Now the same question, one time of day at a time.")
        say()
        say(table.head(ROWS_TO_SHOW).to_string())
        say()
        say(f"  Same figure with no time filter at all ....... {all_day:.2f}% win")
        say(f"  What it would need just to cover the risk .... {needed:.2f}% win")
        say()
        say(f"  Best RATIO by time of day ..................... "
            f"{table['RATIO'].max():.3f} at {table['RATIO'].idxmax()}")
        say(f"  Same RATIO with no time filter ................ {all_day / needed:.3f}")
        say()
        say("  That last pair of numbers is the point of the whole tool. If filtering")
        say("  by time of day does not move the RATIO, the clock is not the thing to")
        say("  filter on. If it does move it, you have somewhere to start.")
        say()

        table.to_csv(os.path.join(
            out_dir, f'time_of_day_T{focus_t}_S{focus_s}_{side}.csv'))

        keep = table.head(10).index.tolist()
        for title, period in (("YEAR BY YEAR", years),
                              ("FIRST vs SECOND HALF OF THE MONTH", month_half),
                              ("DAY OF THE WEEK", weekdays)):
            piv = consistency(slots, period, res, keep)
            say("-" * 100)
            say(f"  {title}   ({side}, target {focus_t}, stop {focus_s})   "
                f"figures are % win")
            say("-" * 100)
            say(piv.to_string())
            say()

        say("  If a time slot only looks good in one or two years, it is probably")
        say("  the market being unusually volatile that year rather than anything")
        say("  about the clock. The slots that hold up across most years and most")
        say("  weekdays are the ones worth building around.")
        say()

        # ---- charts ----
        all_day_ratio = all_day / needed
        charts.ratio_by_time(out_dir, table, all_day_ratio, side,
                             focus_t, focus_s, SESSIONS)
        for title, period, fname in (
                ("Year by year", years, f'04_consistency_year_{side}.png'),
                ("Day of the week", weekdays, f'05_consistency_weekday_{side}.png')):
            piv = consistency(slots, period, res, keep)
            charts.consistency_heatmap(
                out_dir, piv,
                f'{title}   ({side}, target {focus_t}, stop {focus_s})',
                fname, all_day)

        if side == focus_sides[0]:
            charts.dashboard(
                out_dir, travel[travel['ENOUGH DAYS'] == 'yes'], table,
                all_day_ratio, combos_points, combos_percent, side,
                focus_t, focus_s, HOLDING_HOURS,
                [f"{len(entries):,} entries", f"{total_days:,} days",
                 f"{HOLDING_HOURS}h window", f"cost {cost:.2f}",
                 f"best RATIO all day {all_day_ratio:.3f}",
                 f"best RATIO by time {table['RATIO'].max():.3f} at {table['RATIO'].idxmax()}"],
                sessions=SESSIONS)

    charts.travel_distance(out_dir, travel[travel['ENOUGH DAYS'] == 'yes'],
                           HOLDING_HOURS, SESSIONS)

    travel.to_csv(os.path.join(out_dir, 'travel_distance_by_time.csv'))

    # ---- candidate times, ready for the Set File Manager chain ----
    top = travel[travel['ENOUGH DAYS'] == 'yes'].nlargest(
        20, 'UP HALF DAYS').sort_index().index.astype(str).tolist()
    with open(os.path.join(out_dir, 'candidate_times.txt'), 'w', encoding='utf-8') as f:
        f.write(",".join(top))

    say("=" * 100)
    say("  WHAT TO DO WITH THIS")
    say("=" * 100)
    say("  1. Section 1 tells you which hours can even produce the size of move")
    say("     you are after. Ignore the quiet ones.")
    say("  2. Section 2 tells you which target and stop pairing is worth a look.")
    say("     Sort by RATIO.")
    say("  3. Section 3 tells you whether a particular hour beats no filter at all,")
    say("     and whether it holds up across years and weekdays.")
    say("  4. candidate_times.txt holds the busiest times, comma separated, ready")
    say("     to paste into the Set File Manager chain.")
    say()
    say("  NONE OF THIS IS A TRADE SIGNAL. Watch out for times sitting on top of")
    say("  scheduled news, where the spread widens well beyond the figure used here.")
    say(f"  Total run time: {_time.perf_counter() - t_start:.1f} seconds")
    say("=" * 100)

    with open(os.path.join(out_dir, 'summary_report.txt'), 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

    print(f"\nEverything written to {out_dir}")


if __name__ == '__main__':
    main()