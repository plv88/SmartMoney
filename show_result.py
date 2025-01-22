import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from app.core.DataHandler import DataHandler, Klines
from app.core.MarketStructureAnalyzer import MarketStructureAnalyzer
from app.core.LiquidityAnalyzer import LiquidityAnalyzer
import asyncio


def plot_candlestick_with_structure(df, start_time=None, end_time=None, show_plot=True):
    # Create a copy and filter the data for the specified time range
    data = df.copy()

    # Конвертируем индекс в datetime если нужно
    if not isinstance(data.index, pd.DatetimeIndex):
        if isinstance(data.index[0], (int, float)):
            data.index = pd.to_datetime(data.index, unit='ms')
        else:
            data.index = pd.to_datetime(data.index)

    # Filter the data for the specified time range
    if start_time is not None and end_time is not None:
        if isinstance(start_time, str):
            start_time = pd.to_datetime(start_time)
        if isinstance(end_time, str):
            end_time = pd.to_datetime(end_time)
        mask = (data.index >= start_time) & (data.index <= end_time)
        data = data.loc[mask]

    # Создаем фигуру
    fig = go.Figure()

    # Добавляем свечной график
    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name='OHLC'
        )
    )

    # Добавляем структурные точки и линии
    for idx, row in data.iterrows():
        if pd.notna(row['swing_type']):
            # Добавляем аннотации для структурных точек
            fig.add_annotation(
                x=idx,
                y=row['High'],
                text=str(row['swing_type']),
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor='gray'
            )

            # Добавляем линии ликвидности
            if row.get('has_bsl', False):
                # Получаем все точки после текущей
                mask = data.index >= idx
                fig.add_trace(
                    go.Scatter(
                        x=data.index[mask],
                        y=[row['High']] * mask.sum(),
                        mode='lines',
                        line=dict(color='blue', dash='dash'),
                        name='BSL' if 'BSL' not in [trace.name for trace in fig.data] else None,
                        showlegend='BSL' not in [trace.name for trace in fig.data]
                    )
                )

            if row.get('has_ssl', False):
                # Получаем все точки после текущей
                mask = data.index >= idx
                fig.add_trace(
                    go.Scatter(
                        x=data.index[mask],
                        y=[row['Low']] * mask.sum(),
                        mode='lines',
                        line=dict(color='red', dash='dash'),
                        name='SSL' if 'SSL' not in [trace.name for trace in fig.data] else None,
                        showlegend='SSL' not in [trace.name for trace in fig.data]
                    )
                )

    # Настраиваем внешний вид
    fig.update_layout(
        title='SUIUSDT swing_type with Liquidity Levels',
        yaxis_title='Price',
        xaxis_title='Time',
        template='plotly_white',
        xaxis_rangeslider_visible=False,  # Отключаем ползунок внизу
        height=800,  # Увеличиваем высоту графика
        margin=dict(t=30, l=10, r=10, b=10)  # Уменьшаем отступы
    )

    # Настраиваем оси
    fig.update_xaxes(
        rangeslider_visible=False,
        showgrid=True,
        gridwidth=1,
        gridcolor='lightgrey',
        showline=True,
        linewidth=1,
        linecolor='black'
    )

    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='lightgrey',
        showline=True,
        linewidth=1,
        linecolor='black',
        side='right'  # Размещаем ось Y справа
    )

    if show_plot:
        fig.show()

    return fig


async def main():
    symbol = "SUIUSDT"
    intervals = ("5m", "1h", "4h", '1d')
    # intervals = ()
    handler = DataHandler(symbol, intervals, limit=500)
    klines: Klines = await handler.get_ohlcv_data()
    df_m = MarketStructureAnalyzer(klines._1h).main()
    df_l = LiquidityAnalyzer(df_m).main()

    return df_l

# Execute main function
klines = asyncio.run(main())



# Create and display the chart
# fig = plot_candlestick_with_structure(klines, start_time, end_time)
fig = plot_candlestick_with_structure(klines)
# start_time = pd.Timestamp('2025-01-15 03:00:00', tz=timezone.utc)
# fig = plot_candlestick_with_structure(klines, start_time, end_time)
# plt.show()