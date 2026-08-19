# Best Times to Initiate a Trade Checker

**Walkthrough and more tools:** [algocoach.com/tools](https://algocoach.com/tools)

Pick a target distance and a stop distance. This tool scans your historical minute data and reports, for every 15 minute slot in the trading day, how often price travelled your target distance before it travelled your stop distance. It can test hundreds of target and stop pairings at once, in either fixed points or as a percentage of price, and breaks the result down by time of day.

Current version: **1.3**. Version 1.1 is also kept in this folder, see Versions below.

## What's in this folder

| File | What it is |
| --- | --- |
| `Best_Times_to_Initiate_a_Trade_Checker_1_3.py` | The current version of the tool. |
| `charts.py` | Chart drawing used by version 1.3. Keep it in the same folder as the script. |
| `Best_Times_to_Initiate_a_Trade_Checker_1_1.py` | The original version, kept for anyone following the version 1.1 walkthrough. |
| `NDX100sample.csv` | Sample data so either version runs out of the box. |
| `requirements.txt` | The packages the scripts need. |

**About the sample data:** it is about three months of NDX100 minute history. That is enough to prove the script runs and nowhere near enough to conclude anything from. Every 15 minute slot gets roughly ninety observations, which is exactly the noise problem described in the limitations below. The walkthrough videos use a much longer private dataset, which is why the output there looks nothing like a sample run. Use your own longer history for anything real.

## Versions

| Version | Walkthrough | What changed |
| --- | --- | --- |
| 1.3 (current) | Not published yet | Added a percentage-of-price mode alongside fixed points, replaced the win-only score with a RATIO that weighs wins against what was needed to break even, added a travel-distance breakdown by time of day, excludes thin time slots automatically, and added year, month-half, and weekday consistency views. |
| 1.1 | [On the site](https://algocoach.com/tools) | The original. Fixed point targets only, a win-only performance score. |

If you followed the version 1.1 walkthrough, `Best_Times_to_Initiate_a_Trade_Checker_1_1.py` is still here and still runs exactly as shown.

## Requirements

Python 3.11 or newer, VS Code, and the packages in `requirements.txt`.

If you don't already have Python, get it from [python.org](https://www.python.org/downloads/). Either the Python install manager or the standalone installer works. If you take the standalone installer, tick **Add python.exe to PATH** during the install. Then open a new terminal and check it:

```
python --version
```

A version number means you're set. If nothing comes back, or the Microsoft Store opens instead, Python isn't on your PATH and nothing below this point will work.

## Setup

Download the repo (green **Code** button on the repo home page, then **Download ZIP**) and unzip it somewhere you can find, for example `C:\AlgoCoach\tools`.

Open the `best-times-checker` folder in VS Code, open a terminal, and create an isolated environment so you don't disturb any other Python on your machine:

**Windows**

```
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks the activate step, run this once and then retry:

```
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

**macOS and Linux**

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

In VS Code, press `Ctrl+Shift+P`, choose **Python: Select Interpreter**, and pick the one showing `.venv`.

**A note on folder layout:** the walkthrough videos keep several tools under one parent folder with a shared environment, so the folder names on screen won't match yours. The steps above are the simpler single tool version. Either layout works.

## Running it

```
python Best_Times_to_Initiate_a_Trade_Checker_1_3.py
```

Run `Best_Times_to_Initiate_a_Trade_Checker_1_1.py` instead if that is the version your walkthrough covers. Version 1.3 needs `charts.py` sitting next to it in the same folder.

The script looks for CSV files sitting in the same folder as the script itself, so it finds `NDX100sample.csv` with no configuration. Charts and a plain text summary are written to an `analysis_results` folder beside the script. Both versions write to that same folder name, so running one after the other overwrites the previous run's output. Move or rename `analysis_results` first if you want to keep it.

To use your own data, export minute history from your platform to CSV and drop it in beside the script, matching the column layout of `NDX100sample.csv`. **Delete or move `NDX100sample.csv` when you do.** The script uses the first CSV it finds in the folder, so leaving both in place can mean it runs on the sample instead of your data.

Version 1.3 keeps all of its settings in one block near the top of the file, labelled `SETTINGS`, including the target and stop ranges to test, your spread and slippage, and which hours of the day to shade on the charts. Change what you want there and run it again.

## Getting more data

- **Your own broker's MT4/5 platform.** Free, and it's the right data for this tool, because the output is in broker server time.
- **[Dukascopy historical data](https://www.dukascopy.com/swiss/english/marketwatch/historical/).** Free, and covers indices as well as forex. Tickstory will pull it into usable files for you.
- **TickDataSuite.** Paid, with a 14 day trial. This is what I use.

## Reading the output, and one thing to be careful about

**Times are broker server time, not your local time.** This matters more than anything else in the output. On my broker the European session ends around 14:00 to 16:30 server time and the US session opens at 16:30. Yours may be offset by hours. Check your platform's market watch clock before you read anything into a specific hour.

The tool tells you how often a move of a certain size happened after a certain time of day. Version 1.3 factors in the spread and slippage you enter in the settings block. That is a plausibility check on an idea, nothing more. It does not know about commission, scheduled news, or the fact that the instrument you are testing may have moved a long way in price over the sample period.

## Known limitations in version 1.1

I would rather tell you these than have you find them the hard way.

1. **Fixed point targets are not comparable across long samples.** If you run seven years of an index that tripled in price, a fixed target that was a big move in year one is a small move in year seven. Early years will look dead regardless of time of day. Fixed by the percentage mode in version 1.3.
2. **The performance score only counts the wins.** It weights how often the target was reached, without accounting for how often the stop was hit first. Read the raw counts, not the score. Fixed by the RATIO in version 1.3.
3. **Slots with very few observations rank highly on noise alone.** A slot with a handful of observations can top the table by luck. Check the count column before you believe a row. Fixed by the automatic thin-slot exclusion in version 1.3.
4. **Your broker's daily break shows up as missing data.** Slots around the platform's daily maintenance window will be thin or empty. That is the data, not the market. Still true in version 1.3.

**Patched after filming:** the script used to crash before writing `summary_report.txt`, because two emoji in the console summary can't be printed on a Windows console using its default encoding. That raised an error which the script's own error handling caught and reported instead of finishing. The emoji have been removed from the printed text so the run completes and the summary file gets written. Nothing else about the script changed, and the walkthrough video still matches what you see on screen.

## Known limitations in version 1.3

1. **Your broker's daily break shows up as missing data.** Slots around the platform's daily maintenance window will be thin or empty, and version 1.3 will list them separately as left out of the ranking rather than silently dropping them, but the underlying gap is still the data, not the market.
2. **Commission and scheduled news are not in the cost figure.** The settings block accounts for spread and slippage, nothing else. Widen your own margin around known news times.
3. **A RATIO above 1 is a plausibility check, not a result.** It means the target arrived first often enough to have covered the risk historically. It says nothing about what happens next.

## What this is not

It is not a strategy, a signal, an indicator, or an entry system. It does not backtest anything. It measures how price behaved historically after a given time of day, and historical behaviour is not a forecast.

## Disclaimer

This tool is for educational and informational purposes only. I am not a financial advisor, and nothing here is financial, investment, or trading advice. Trading forex, futures, indices, and CFDs carries a substantial risk of loss and is not suitable for everyone. My results are my own and do not guarantee or predict your results, and past performance is not indicative of future performance. You are solely responsible for your own trading decisions. FTMO, MetaQuotes, and other referenced brands are the property of their respective owners; references reflect my own experience and do not imply endorsement or affiliation.

## License

MIT. Use it, change it, ship it. See the [LICENSE](../LICENSE) in the repo root.
