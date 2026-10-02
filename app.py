import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ta.momentum import RSIIndicator
from ta.trend import MACD
from datetime import date, timedelta


# =========================================================
# PAGE SETUP
# =========================================================

st.set_page_config(
    page_title="SPY vs USO Technical Analysis",
    layout="wide"
)

st.title("Comparative Technical Analysis Dashboard")
st.write("SPY vs. USO")


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header("Dashboard Controls")

ticker = st.sidebar.selectbox(
    "Choose an asset",
    ["SPY", "USO"]
)

end = st.sidebar.date_input(
    "End date",
    value=date.today()
)

start = st.sidebar.date_input(
    "Start date",
    value=end - timedelta(days=730)
)

short_window = st.sidebar.slider(
    "Short SMA window",
    min_value=5,
    max_value=50,
    value=20
)

long_window = st.sidebar.slider(
    "Long SMA window",
    min_value=20,
    max_value=200,
    value=50
)

show_sma = st.sidebar.checkbox(
    "Show Moving Averages",
    value=True
)

show_bollinger = st.sidebar.checkbox(
    "Show Bollinger Bands",
    value=True
)

show_rsi = st.sidebar.checkbox(
    "Show RSI",
    value=True
)

show_macd = st.sidebar.checkbox(
    "Show MACD",
    value=True
)


# =========================================================
# CHECK DATES
# =========================================================

if start >= end:

    st.error("Start date must be before the end date.")
    st.stop()


# =========================================================
# DOWNLOAD DATA
# =========================================================

data = yf.download(
    ticker,
    start=start,
    end=end + timedelta(days=1),
    interval="1d",
    auto_adjust=True,
    multi_level_index=False,
    progress=False
)

if data.empty:

    st.error("No data was downloaded. Please choose another date range.")

    st.stop()


# =========================================================
# TECHNICAL INDICATORS
# =========================================================

# Moving averages

data["SMA_Short"] = (
    data["Close"]
    .rolling(short_window)
    .mean()
)

data["SMA_Long"] = (
    data["Close"]
    .rolling(long_window)
    .mean()
)


# Bollinger Bands

bb_middle = (
    data["Close"]
    .rolling(20)
    .mean()
)

bb_std = (
    data["Close"]
    .rolling(20)
    .std()
)

data["BB_Middle"] = bb_middle

data["BB_Upper"] = (
    bb_middle + 2 * bb_std
)

data["BB_Lower"] = (
    bb_middle - 2 * bb_std
)


# RSI

rsi = RSIIndicator(
    close=data["Close"],
    window=14
)

data["RSI"] = rsi.rsi()


# MACD

macd = MACD(
    close=data["Close"],
    window_fast=12,
    window_slow=26,
    window_sign=9
)

data["MACD"] = macd.macd()

data["MACD_Signal"] = (
    macd.macd_signal()
)

data["MACD_Hist"] = (
    macd.macd_diff()
)


# =========================================================
# BUY / SELL SIGNALS
# =========================================================

data["Golden_Cross"] = (
    (data["SMA_Short"] > data["SMA_Long"]) &
    (
        data["SMA_Short"].shift(1)
        <=
        data["SMA_Long"].shift(1)
    )
)

data["Death_Cross"] = (
    (data["SMA_Short"] < data["SMA_Long"]) &
    (
        data["SMA_Short"].shift(1)
        >=
        data["SMA_Long"].shift(1)
    )
)


# Buy condition

data["Buy_Signal"] = (
    data["Golden_Cross"] |
    (data["RSI"] < 30)
)


# Sell condition

data["Sell_Signal"] = (
    data["Death_Cross"] |
    (data["RSI"] > 70)
)


# =========================================================
# CURRENT VALUES
# =========================================================

latest = data.iloc[-1]

current_price = latest["Close"]

current_rsi = latest["RSI"]

short_sma = latest["SMA_Short"]

long_sma = latest["SMA_Long"]


# =========================================================
# TREND STATUS
# =========================================================

if current_price > long_sma:

    trend_status = "Above Long SMA"

else:

    trend_status = "Below Long SMA"


# =========================================================
# SIGNAL DATES
# =========================================================

golden_dates = data.index[
    data["Golden_Cross"]
]

if len(golden_dates) > 0:

    last_golden = (
        golden_dates[-1]
        .strftime("%Y-%m-%d")
    )

else:

    last_golden = "None"


death_dates = data.index[
    data["Death_Cross"]
]

if len(death_dates) > 0:

    last_death = (
        death_dates[-1]
        .strftime("%Y-%m-%d")
    )

else:

    last_death = "None"


buy_dates = data.index[
    data["Buy_Signal"]
]

if len(buy_dates) > 0:

    last_buy = (
        buy_dates[-1]
        .strftime("%Y-%m-%d")
    )

else:

    last_buy = "None"


sell_dates = data.index[
    data["Sell_Signal"]
]

if len(sell_dates) > 0:

    last_sell = (
        sell_dates[-1]
        .strftime("%Y-%m-%d")
    )

else:

    last_sell = "None"


# =========================================================
# CURRENT MARKET SUMMARY
# =========================================================

st.subheader(
    f"{ticker} Current Market Summary"
)

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Current Price",
    f"${current_price:.2f}"
)

col2.metric(
    "RSI (14)",
    f"{current_rsi:.2f}"
)

col3.metric(
    "Price vs. Long SMA",
    trend_status
)

col4.metric(
    "Short SMA",
    f"${short_sma:.2f}"
)


col5, col6, col7 = st.columns(3)

col5.metric(
    "Long SMA",
    f"${long_sma:.2f}"
)

col6.metric(
    "Latest Buy Signal",
    last_buy
)

col7.metric(
    "Latest Sell Signal",
    last_sell
)


# =========================================================
# MAIN CHART
# =========================================================

st.subheader(
    f"{ticker} Technical Analysis"
)

fig = make_subplots(
    rows=3,
    cols=1,
    shared_xaxes=True,

    vertical_spacing=0.04,

    row_heights=[
        0.60,
        0.20,
        0.20
    ],

    subplot_titles=[
        f"{ticker} Price",
        "RSI (14)",
        "MACD (12, 26, 9)"
    ]
)


# ---------------------------------------------------------
# Candlestick
# ---------------------------------------------------------

fig.add_trace(

    go.Candlestick(

        x=data.index,

        open=data["Open"],

        high=data["High"],

        low=data["Low"],

        close=data["Close"],

        name="Price"

    ),

    row=1,
    col=1
)


# ---------------------------------------------------------
# Moving averages
# ---------------------------------------------------------

if show_sma:

    fig.add_trace(

        go.Scatter(

            x=data.index,

            y=data["SMA_Short"],

            name=f"SMA {short_window}",

            line=dict(
                color="red"
            )

        ),

        row=1,
        col=1
    )


    fig.add_trace(

        go.Scatter(

            x=data.index,

            y=data["SMA_Long"],

            name=f"SMA {long_window}",

            line=dict(
                color="green"
            )

        ),

        row=1,
        col=1
    )


# ---------------------------------------------------------
# Bollinger Bands
# ---------------------------------------------------------

if show_bollinger:

    fig.add_trace(

        go.Scatter(

            x=data.index,

            y=data["BB_Upper"],

            name="BB Upper",

            line=dict(
                dash="dash"
            )

        ),

        row=1,
        col=1
    )


    fig.add_trace(

        go.Scatter(

            x=data.index,

            y=data["BB_Lower"],

            name="BB Lower",

            line=dict(
                dash="dash"
            )

        ),

        row=1,
        col=1
    )


# =========================================================
# RSI
# =========================================================

if show_rsi:

    fig.add_trace(

        go.Scatter(

            x=data.index,

            y=data["RSI"],

            name="RSI",

            line=dict(
                color="orange"
            )

        ),

        row=2,
        col=1
    )


    fig.add_hline(

        y=70,

        line_dash="dash",

        row=2,
        col=1
    )


    fig.add_hline(

        y=30,

        line_dash="dash",

        row=2,
        col=1
    )


# =========================================================
# MACD
# =========================================================

if show_macd:

    fig.add_trace(

        go.Scatter(

            x=data.index,

            y=data["MACD"],

            name="MACD",

            line=dict(
                color="cyan"
            )

        ),

        row=3,
        col=1
    )


    fig.add_trace(

        go.Scatter(

            x=data.index,

            y=data["MACD_Signal"],

            name="Signal",

            line=dict(
                color="yellow"
            )

        ),

        row=3,
        col=1
    )


    fig.add_trace(

        go.Bar(

            x=data.index,

            y=data["MACD_Hist"],

            name="Histogram",

            opacity=0.5

        ),

        row=3,
        col=1
    )


# =========================================================
# CHART FORMAT
# =========================================================

fig.update_layout(

    template="plotly_dark",

    height=900,

    xaxis_rangeslider_visible=False,

    hovermode="x unified",

    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="left",
        x=0
    )
)


fig.update_yaxes(

    title_text="Price",

    row=1,
    col=1
)


fig.update_yaxes(

    title_text="RSI",

    range=[0, 100],

    row=2,
    col=1
)


fig.update_yaxes(

    title_text="MACD",

    row=3,
    col=1
)


fig.update_xaxes(

    title_text="Date",

    row=3,
    col=1
)


st.plotly_chart(

    fig,

    use_container_width=True
)


# =========================================================
# CURRENT INTERPRETATION
# =========================================================

st.subheader(
    "Current Interpretation"
)


if current_rsi < 30:

    rsi_comment = (
        "RSI is below 30, indicating an "
        "oversold condition."
    )

elif current_rsi > 70:

    rsi_comment = (
        "RSI is above 70, indicating an "
        "overbought condition."
    )

else:

    rsi_comment = (
        "RSI is between 30 and 70, so there "
        "is no current overbought or oversold condition."
    )


if current_price > long_sma:

    trend_comment = (
        f"The current price is above the "
        f"{long_window}-day SMA."
    )

else:

    trend_comment = (
        f"The current price is below the "
        f"{long_window}-day SMA."
    )


st.markdown(
    f"""
**Trend:** {trend_comment}

**RSI:** {rsi_comment}

**Latest Golden Cross:** {last_golden}

**Latest Death Cross:** {last_death}

**Latest Buy Signal:** {last_buy}

**Latest Sell Signal:** {last_sell}
"""
)


# =========================================================
# SPY VS USO COMPARISON
# PART 3 EXTENSION
# =========================================================

st.subheader(
    "SPY vs. USO Performance Comparison"
)

comparison = yf.download(

    ["SPY", "USO"],

    start=start,

    end=end + timedelta(days=1),

    interval="1d",

    auto_adjust=True,

    multi_level_index=False,

    progress=False
)


if not comparison.empty:

    spy_close = comparison["Close"]["SPY"]

    uso_close = comparison["Close"]["USO"]

    spy_normalized = (
        spy_close / spy_close.iloc[0] * 100
    )

    uso_normalized = (
        uso_close / uso_close.iloc[0] * 100
    )


    comparison_fig = go.Figure()


    comparison_fig.add_trace(

        go.Scatter(

            x=spy_normalized.index,

            y=spy_normalized,

            name="SPY",

            line=dict(
                color="white"
            )

        )
    )


    comparison_fig.add_trace(

        go.Scatter(

            x=uso_normalized.index,

            y=uso_normalized,

            name="USO",

            line=dict(
                color="orange"
            )

        )
    )


    comparison_fig.update_layout(

        template="plotly_dark",

        height=500,

        title="Normalized Performance: SPY vs. USO",

        xaxis_title="Date",

        yaxis_title="Normalized Price (Start = 100)",

        xaxis_rangeslider_visible=False,

        hovermode="x unified"
    )


    st.plotly_chart(

        comparison_fig,

        use_container_width=True
    )


# =========================================================
# DATA DOWNLOAD
# =========================================================

st.subheader("Download Data")

csv_data = data.to_csv().encode("utf-8")

st.download_button(

    label="Download Technical Analysis Data",

    data=csv_data,

    file_name=f"{ticker}_technical_analysis.csv",

    mime="text/csv"
)
