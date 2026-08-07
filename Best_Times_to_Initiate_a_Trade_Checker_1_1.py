import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
from collections import Counter
import os
import glob

# --- Parameters ---
HOLDING_PERIOD_HOURS = 8

# --- Main Simulation Function ---
def run_simulation(df, entry_points, profit_target, stop_loss):
    """
    Runs the trade simulation and returns a list of successful trades,
    each with its start time and direction ('long' or 'short').
    """
    successful_trades_details = []
    
    for entry_time, entry_row in tqdm(entry_points.iterrows(), total=len(entry_points), desc=f"Testing TP:${profit_target} SL:${stop_loss}", leave=False):
        entry_price = entry_row['Open']
        end_time = entry_time + pd.Timedelta(hours=HOLDING_PERIOD_HOURS)
        trade_window = df.loc[entry_time:end_time]

        if trade_window.empty:
            continue

        # Long trade simulation
        sl_long, tp_long = entry_price - stop_loss, entry_price + profit_target
        tp_hits_long = trade_window[trade_window['High'] >= tp_long]
        sl_hits_long = trade_window[trade_window['Low'] <= sl_long]
        first_tp_time_long = tp_hits_long.index.min() if not tp_hits_long.empty else pd.NaT
        first_sl_time_long = sl_hits_long.index.min() if not sl_hits_long.empty else pd.NaT

        if pd.notna(first_tp_time_long) and (pd.isna(first_sl_time_long) or first_tp_time_long < first_sl_time_long):
            successful_trades_details.append({'time': entry_time.time(), 'direction': 'long'})
            continue

        # Short trade simulation
        sl_short, tp_short = entry_price + stop_loss, entry_price - profit_target
        tp_hits_short = trade_window[trade_window['Low'] <= tp_short]
        sl_hits_short = trade_window[trade_window['High'] >= sl_short]
        first_tp_time_short = tp_hits_short.index.min() if not tp_hits_short.empty else pd.NaT
        first_sl_time_short = sl_hits_short.index.min() if not sl_hits_short.empty else pd.NaT
        
        if pd.notna(first_tp_time_short) and (pd.isna(first_sl_time_short) or first_tp_time_short < first_sl_time_short):
            successful_trades_details.append({'time': entry_time.time(), 'direction': 'short'})

    return successful_trades_details

# --- Script Start ---
try:
    # --- NEW: Automatically find CSV file ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_files = glob.glob(os.path.join(script_dir, '*.csv'))
    if not csv_files:
        raise FileNotFoundError("Error: No CSV file found in the current directory.")
    
    input_file = csv_files[0]
    print(f"Found and using data file: {input_file}")

    # --- NEW: Create an output directory ---
    output_dir = os.path.join(script_dir, "analysis_results")
    os.makedirs(output_dir, exist_ok=True)
    print(f"Results will be saved in the '{output_dir}' folder.")

    print("\nLoading data...")
    df = pd.read_csv(input_file, header=None, names=['Date', 'Time', 'Open', 'High', 'Low', 'Close', 'Volume'], encoding='ISO-8859-1')
    df['DateTime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
    df.set_index('DateTime', inplace=True)
    df.drop(['Date', 'Time'], axis=1, inplace=True)

    print("Resampling for 15-minute entry points...")
    entry_points = df.resample('15min').first().dropna()
    
    total_days = df.index.normalize().nunique()
    print("-" * 50)
    print(f"Data Scope: Testing {len(entry_points)} potential trades over {total_days} unique days.")
    print("-" * 50)

    # --- Define Parameter Ranges ---
    stop_loss_range = range(25, 56, 50)
    profit_target_range = range(200, 351, 150)
    
    all_results = []
    best_result = {'params': None, 'best_score': -1, 'details': None}

    # --- Run Main Loop ---
    for pt in profit_target_range:
        for sl in stop_loss_range:
            trade_details = run_simulation(df, entry_points, profit_target=pt, stop_loss=sl)
            num_success = len(trade_details)
            
            risk_reward_ratio = pt / sl
            performance_score = num_success * risk_reward_ratio
            
            all_results.append({
                'Profit Target': pt, 'Stop Loss': sl, 'Successful Trades': num_success,
                'R:R Ratio': round(risk_reward_ratio, 2), 'Performance Score': round(performance_score)
            })
            
            if performance_score > best_result['best_score']:
                best_result['params'] = (pt, sl)
                best_result['best_score'] = performance_score
                best_result['details'] = trade_details

            # --- PLOT FOR EVERY COMBINATION ---
            if num_success > 0:
                start_times = [trade['time'] for trade in trade_details]
                time_counts = Counter(start_times)
                plot_times_sorted = sorted(time_counts.keys(), key=lambda t: t.hour * 60 + t.minute)
                plot_counts = [time_counts[t] for t in plot_times_sorted]
                time_labels = [t.strftime('%H:%M') for t in plot_times_sorted]

                plt.figure(figsize=(20, 10))
                sns.barplot(x=time_labels, y=plot_counts, hue=time_labels, palette='tab20', legend=False)
                
                plt.title(f'Successful Trade Initiation Times (TP:${pt}, SL:${sl})', fontsize=20)
                plt.xlabel('Start Time of Trade', fontsize=14)
                plt.ylabel('Number of Occurrences', fontsize=14)
                plt.xticks(rotation=90, fontsize=14)
                plt.yticks(fontsize=12)
                
                plt.tight_layout()
                # --- NEW: Save plot to the output directory ---
                plot_filename = os.path.join(output_dir, f'strategy_times_TP{pt}_SL{sl}.png')
                plt.savefig(plot_filename)
                plt.close()

    # --- Display and Save Full Results Table ---
    results_df = pd.DataFrame(all_results)
    summary_header = "\n" + "="*80 + "\n" + " " * 28 + "PARAMETER TEST SUMMARY\n" + "="*80
    summary_body = results_df.sort_values(by='Performance Score', ascending=False).to_string(index=False)
    summary_footer = "\n" + "="*80
    
    print(summary_header)
    print(summary_body)
    print(summary_footer)

    # --- Create Heatmap of PERFORMANCE SCORE ---
    pivot_table = results_df.pivot(index='Profit Target', columns='Stop Loss', values='Performance Score')
    plt.figure(figsize=(10, 8))
    sns.heatmap(pivot_table, annot=True, fmt=".0f", cmap="viridis", linewidths=.5)
    
    plt.title('Heatmap of Performance Score (Wins x Risk/Reward Ratio)', fontsize=16)
    plt.xlabel('Stop Loss ($)', fontsize=12)
    plt.ylabel('Profit Target ($)', fontsize=12)
    
    # --- NEW: Save heatmap to the output directory ---
    heatmap_filename = os.path.join(output_dir, 'strategy_performance_heatmap.png')
    plt.savefig(heatmap_filename)
    print(f"\nPerformance heatmap '{heatmap_filename}' has been generated.")

    # --- Detailed Analysis Text for the BEST Performing Strategy ---
    best_strategy_summary = ""
    if best_result['params']:
        best_pt, best_sl = best_result['params']
        trade_count = len(best_result['details'])
        
        best_strategy_summary += "\n" + "="*60 + "\n"
        best_strategy_summary += "          🏆 BEST PERFORMING STRATEGY ANALYSIS 🏆\n"
        best_strategy_summary += "               (Based on Highest Performance Score)\n"
        best_strategy_summary += "="*60 + "\n"
        best_strategy_summary += f"Optimal Parameters: TP = ${best_pt}, SL = ${best_sl}\n"
        best_strategy_summary += f"Performance Score: {best_result['best_score']:.0f}\n"
        best_strategy_summary += f"Total Successful Trades: {trade_count}\n"
        
        directions = [trade['direction'] for trade in best_result['details']]
        long_wins = directions.count('long')
        short_wins = directions.count('short')
        best_strategy_summary += f"\nDirectional Breakdown:\n"
        best_strategy_summary += f"  - Long Trades:  {long_wins} wins ({long_wins / trade_count:.2%})\n"
        best_strategy_summary += f"  - Short Trades: {short_wins} wins ({short_wins / trade_count:.2%})\n"

        start_times = [trade['time'] for trade in best_result['details']]
        time_counts = Counter(start_times)
        
        best_strategy_summary += "\n--- 🕒 Top 15 Most Successful Trade Initiation Times ---\n"
        sorted_times = sorted(time_counts.items(), key=lambda item: (-item[1], item[0]))
        for i, (time, count) in enumerate(sorted_times[:15]):
            best_strategy_summary += f"  {i+1:2}. {time.strftime('%H:%M')}  -  {count} successful trades\n"
        best_strategy_summary += "="*60 + "\n"
        best_strategy_summary += f"\nNote: The detailed plot for this best strategy is named 'strategy_times_TP{best_pt}_SL{best_sl}.png'\n"
        
        print(best_strategy_summary)

    # --- NEW: Save all text output to a summary file ---
    summary_filename = os.path.join(output_dir, 'summary_report.txt')
    with open(summary_filename, 'w', encoding='utf-8') as f:
        f.write(f"Analysis Report for: {input_file}\n")
        f.write(f"Data Scope: {len(entry_points)} potential trades over {total_days} unique days.\n")
        f.write(summary_header)
        f.write(summary_body)
        f.write(summary_footer)
        f.write(best_strategy_summary)
    
    print(f"Full text summary saved to '{summary_filename}'")


except Exception as e:
    print(f"\nAn error occurred: {e}")
