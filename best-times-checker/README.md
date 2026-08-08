# Best Times to Initiate a Trade Checker

**Walkthrough and more tools:** [algocoach.com/tools](https://algocoach.com/tools)

Pick a target distance and a stop distance. This tool scans your historical minute data and reports, for every 15 minute slot in the trading day, how often price travelled your target distance before it travelled your stop distance.

Version 1.1.

## What's in this folder

| File | What it is |
| --- | --- |
| `Best_Times_to_Initiate_a_Trade_Checker_1_1.py` | The tool. |
| `NAS100sample.csv` | Sample data so it runs out of the box. |
| `requirements.txt` | The packages it needs. |

**About the sample data:** it is about six weeks of NAS100 minute history. That is enough to prove the script runs and nowhere near enough to conclude anything from. Every 15 minute slot gets roughly thirty observations, which is exactly the noise problem described in the limitations below. Use your own longer history for anything real.

## Requirements

Python 3.11 or newer, and the packages in `requirements.txt`.

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

## Running it

```
python Best_Times_to_Initiate_a_Trade_Checker_1_1.py
```

The script looks for CSV files sitting in the same folder as the script itself, so it finds `NAS100sample.csv` with no configuration. Charts and a plain text summary are written to that same folder.

To use your own data, export minute history from your platform to CSV and drop it in beside the script, matching the column layout of `NAS100sample.csv`. The target distance, stop distance, and other settings are plain variables near the top of the file. Change them and run it again.

## Reading the output, and one thing to be careful about

**Times are broker server time, not your local time.** This matters more than anything else in the output. On my broker the European session ends around 14:00 to 16:30 server time and the US session opens at 16:30. Yours may be offset by hours. Check your platform's market watch clock before you read anything into a specific hour.

The tool tells you how often a move of a certain size happened after a certain time of day. That is a plausibility check on an idea, nothing more. It does not know about spread, slippage, commission, news, or the fact that the instrument you are testing may have tripled in price over the sample period.

## Known limitations in version 1.1

I would rather tell you these than have you find them the hard way.

1. **Fixed point targets are not comparable across long samples.** If you run seven years of an index that tripled in price, a fixed target that was a big move in year one is a small move in year seven. Early years will look dead regardless of time of day. Percentage or volatility normalized targets are the fix and are planned.
2. **The performance score only counts the wins.** It weights how often the target was reached, without accounting for how often the stop was hit first. Read the raw counts, not the score.
3. **Slots with very few observations rank highly on noise alone.** A slot with a handful of observations can top the table by luck. Check the count column before you believe a row.
4. **Your broker's daily break shows up as missing data.** Slots around the platform's daily maintenance window will be thin or empty. That is the data, not the market.

## What this is not

It is not a strategy, a signal, an indicator, or an entry system. It does not backtest anything. It measures how price behaved historically after a given time of day, and historical behaviour is not a forecast.

## Disclaimer

This tool is for educational and informational purposes only. I am not a financial advisor, and nothing here is financial, investment, or trading advice. Trading forex, futures, indices, and CFDs carries a substantial risk of loss and is not suitable for everyone. My results are my own and do not guarantee or predict your results, and past performance is not indicative of future performance. You are solely responsible for your own trading decisions. FTMO, MetaQuotes, and other referenced brands are the property of their respective owners; references reflect my own experience and do not imply endorsement or affiliation.

## License

MIT. Use it, change it, ship it. See the [LICENSE](../LICENSE) in the repo root.
