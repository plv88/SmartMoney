
# Smart Money Trading Analytics System

This project is a comprehensive system for analyzing and optimizing trading strategies based on the Smart Money trading concept. It combines advanced market structure analysis, liquidity tracking, and machine learning to enhance decision-making and profitability.

## Key Features
- **Market Structure Analysis**: Identifies trends, swing points, and structural shifts using algorithmic tools.
- **Liquidity Mapping**: Tracks key liquidity zones (e.g., order blocks, imbalances) to predict price movements.
- **Data Enrichment**: Integrates OHLCV data with calculated metrics (e.g., momentum, VWAP, volume trends).
- **Machine Learning Integration**: Leverages historical trading data and enriched features to train models for predicting optimal trade setups.
- **Modular Architecture**: Core components include data handling, market structure analysis, and debug tools for seamless data processing.

## How to Use

### 1. Install Dependencies
Ensure you have Python 3.8+ installed. Install the required dependencies:
```bash
pip install -r requirements.txt
```

### 2. Set Up Data Retrieval
- Edit the `DataHandler` class in `DataHandler.py` to configure your trading symbol and desired intervals.
- Supported intervals include `1m`, `5m`, `15m`, `1h`, `4h`, `1d`, etc.

### 3. Run the Analysis
Use the `debug.py` or `main.py` script as an entry point:
```bash
python main.py
```
```bash
python debug.py
```
This script retrieves OHLCV data, applies market structure analysis, and outputs enriched DataFrames.

### 4. Modify Configurations
Adjust parameters in `MarketStructureAnalyzer` (e.g., momentum, VWAP thresholds) to suit your trading strategy.

### 5. Explore Results
The system outputs enriched DataFrames with key metrics such as:
- **Trend**: Current market trend (`uptrend`, `downtrend`).
- **Swing Type**: Highs and lows (`HH`, `HL`, `LH`, `LL`).
- **Volume State**: High/low volume signals.
- **VWAP Analysis**: Insights on overbought/oversold conditions.

### 6. Extend with ML Models
For advanced predictions, integrate machine learning models using the enriched features. Historical data can be processed to train and fine-tune models for predicting optimal trades.

## Example Workflow
- Define the trading symbol and intervals:
  ```python
  symbol = "BTCUSDT"
  intervals = ("5m", "1h", "4h", "1d")
  ```
- Run the script and analyze results. Data will be enriched with calculated metrics and market structure insights.

---

Feel free to extend or modify the system to suit your trading needs!
