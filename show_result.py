# import mplfinance as mpf
# import matplotlib.pyplot as plt
# import pandas as pd
# from app.core.DataHandler import DataHandler, Klines
# from app.core.MarketStructureAnalyzer import MarketStructureAnalyzer
# import asyncio
# from datetime import datetime, timezone
#
#
# def plot_candlestick_with_structure(df, start_time, end_time):
#     # Create a copy and filter the data for the specified time range
#     data = df.copy()
#
#     # Convert timestamps to datetime if they're not already
#     if not isinstance(data.index, pd.DatetimeIndex):
#         data.index = pd.to_datetime(data.index)
#
#     # Ensure the same timezone awareness
#     if data.index.tz is None:
#         data.index = data.index.tz_localize('UTC')
#
#     # Filter the data for the specified time range
#     mask = (data.index >= start_time) & (data.index <= end_time)
#     data = data.loc[mask]
#
#     # Create annotations list for structures
#     annotations = []
#     for idx, row in data.iterrows():
#         if pd.notna(row['swing_type']):
#             annotations.append(
#                 dict(
#                     x=idx,
#                     y=row['High'],
#                     text=str(row['swing_type']),
#                     showarrow=True,
#                     arrowhead=4,
#                     arrowsize=1,
#                     arrowwidth=2,
#                     arrowcolor='gray'
#                 )
#             )
#
#     # Style settings
#     mc = mpf.make_marketcolors(up='green',
#                                down='red',
#                                edge='inherit',
#                                wick='inherit',
#                                volume='in',
#                                inherit=True)
#
#     style = mpf.make_mpf_style(marketcolors=mc)
#
#     # Create the chart
#     fig, axlist = mpf.plot(data,
#                            type='candle',
#                            style=style,
#                            title='SUIUSDT swing_type (Jan 9, 7:00-14:00)',
#                            volume=False,
#                            returnfig=True,
#                            figratio=(15, 8),
#                            figscale=1.5)
#
#     # Add annotations
#     ax = axlist[0]
#     for ann in annotations:
#         ax.annotate(ann['text'],
#                     xy=(data.index.get_loc(ann['x']), ann['y']),
#                     xytext=(0, 15),
#                     textcoords='offset points',
#                     ha='center',
#                     va='bottom',
#                     fontsize=8,
#                     arrowprops=dict(arrowstyle='->'))
#
#     plt.show()
#     return fig
#
# async def main():
#     symbol = "SUIUSDT"
#     intervals = ("5m", "1h", "4h", "1d")
#     intervals = ("5m",)
#     handler = DataHandler(symbol, intervals)
#     klines: Klines = await handler.get_ohlcv_data()
#     MarketStructureAnalyzer(klines).analyze_multiple_timeframes()
#     return klines
#
# # Execute main function
# klines = asyncio.run(main())
#
# # Define the time range
# start_time = pd.Timestamp('2025-01-08 22:00:00', tz=timezone.utc)
# end_time = pd.Timestamp('2025-01-09 15:00:00', tz=timezone.utc)
#
# # Create and display the chart
# fig = plot_candlestick_with_structure(klines._5m, start_time, end_time)
# plt.show()

import mplfinance as mpf
import matplotlib.pyplot as plt
import pandas as pd
from app.core.DataHandler import DataHandler, Klines
from app.core.MarketStructureAnalyzer import MarketStructureAnalyzer
import asyncio
from datetime import datetime, timezone


def plot_candlestick_with_structure(df, start_time, end_time):
    # Create a copy and filter the data for the specified time range
    data = df.copy()

    # Convert timestamps to datetime if they're not already
    if not isinstance(data.index, pd.DatetimeIndex):
        data.index = pd.to_datetime(data.index)

    # Ensure the same timezone awareness
    if data.index.tz is None:
        data.index = data.index.tz_localize('UTC')

    # Filter the data for the specified time range
    mask = (data.index >= start_time) & (data.index <= end_time)
    data = data.loc[mask]

    # Create annotations list for structures
    annotations = []
    for idx, row in data.iterrows():
        if pd.notna(row['swing_type']):
            annotations.append(
                dict(
                    x=idx,
                    y=row['High'],
                    text=str(row['swing_type']),
                    showarrow=True,
                    arrowhead=4,
                    arrowsize=1,
                    arrowwidth=2,
                    arrowcolor='gray'
                )
            )

    # Style settings
    mc = mpf.make_marketcolors(up='green',
                               down='red',
                               edge='inherit',
                               wick='inherit',
                               volume='in',
                               inherit=True)

    style = mpf.make_mpf_style(marketcolors=mc)

    # Create the chart
    fig, axlist = mpf.plot(data,
                           type='candle',
                           style=style,
                           title='SUIUSDT swing_type (Jan 9, 7:00-14:00)',
                           volume=False,
                           returnfig=True,
                           figratio=(15, 8),
                           figscale=1.5)

    # Add annotations
    ax = axlist[0]
    for ann in annotations:
        ax.annotate(ann['text'],
                    xy=(data.index.get_loc(ann['x']), ann['y']),
                    xytext=(0, 15),
                    textcoords='offset points',
                    ha='center',
                    va='bottom',
                    fontsize=8,
                    arrowprops=dict(arrowstyle='->'))

    # Add grid and time labels
    ax.grid(True, linestyle='--', alpha=0.5)  # Add grid with dashed lines
    ax.set_xlabel('Time')  # Set label for x-axis
    ax.set_ylabel('Price')  # Set label for y-axis

    # Adjust x-axis ticks
    ax.xaxis.set_major_locator(plt.MaxNLocator(10))  # Set maximum number of ticks
    ax.xaxis.set_minor_locator(plt.MaxNLocator(50))  # Optional: minor ticks

    # Rotate x-axis labels for better readability
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    plt.show()
    return fig


async def main():
    symbol = "SUIUSDT"
    intervals = ("1m", "5m", "1h", "4h", "1d")
    # intervals = ()
    handler = DataHandler(symbol, intervals, limit=1000)
    klines: Klines = await handler.get_ohlcv_data()
    MarketStructureAnalyzer(klines).analyze_multiple_timeframes()
    return klines

# Execute main function
klines = asyncio.run(main())

# Define the time range
start_time = pd.Timestamp('2025-01-11 06:00:00', tz=timezone.utc)
end_time = pd.Timestamp('2025-01-11 20:00:00', tz=timezone.utc)

# Create and display the chart
fig = plot_candlestick_with_structure(klines._1m, start_time, end_time)
plt.show()
start_time = pd.Timestamp('2025-01-11 03:00:00', tz=timezone.utc)
fig = plot_candlestick_with_structure(klines._5m, start_time, end_time)
plt.show()