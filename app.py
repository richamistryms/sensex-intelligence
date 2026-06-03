import streamlit as st
import yfinance as yf
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="Sensex Intelligence",
    page_icon="📈",
    layout="centered"
)

# Refresh page every 30 seconds
st_autorefresh(interval=30000, key="sensex_refresh")

# ==========================================================
# STYLES
# ==========================================================

st.markdown("""
<style>
.main {
    padding-top: 1rem;
}

.metric-box {
    padding: 10px;
    border-radius: 10px;
    background-color: #f0f2f6;
}

.big-number {
    font-size: 40px;
    font-weight: bold;
}

.bias-bull {
    color: green;
    font-size: 30px;
    font-weight: bold;
}

.bias-bear {
    color: red;
    font-size: 30px;
    font-weight: bold;
}

.bias-neutral {
    color: orange;
    font-size: 30px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ==========================================================
# SENSEX DATA
# ==========================================================

@st.cache_data(ttl=60)
def get_sensex_data():

    try:

        ticker = yf.Ticker("^BSESN")

        hist = ticker.history(period="7d")

        if hist.empty:
            return None

        latest = hist.iloc[-1]
        previous = hist.iloc[-2]

        current_price = round(float(latest["Close"]), 2)

        prev_close = round(float(previous["Close"]), 2)
        prev_high = round(float(previous["High"]), 2)
        prev_low = round(float(previous["Low"]), 2)

        change = round(current_price - prev_close, 2)

        change_pct = round(
            (change / prev_close) * 100,
            2
        )

        return {
            "current": current_price,
            "prev_close": prev_close,
            "prev_high": prev_high,
            "prev_low": prev_low,
            "change": change,
            "change_pct": change_pct
        }

    except Exception as e:
        st.error(f"Market Data Error: {e}")
        return None


# ==========================================================
# PIVOT CALCULATIONS
# ==========================================================

def calculate_levels(high, low, close):

    pivot = (high + low + close) / 3

    r1 = (2 * pivot) - low
    s1 = (2 * pivot) - high

    r2 = pivot + (high - low)
    s2 = pivot - (high - low)

    return {
        "pivot": round(pivot, 2),
        "s1": round(s1, 2),
        "s2": round(s2, 2),
        "r1": round(r1, 2),
        "r2": round(r2, 2)
    }


# ==========================================================
# MARKET BIAS
# ==========================================================

def get_market_bias(price, levels):

    if price > levels["r1"]:
        return "🟢 STRONG BULLISH"

    elif price > levels["pivot"]:
        return "🟢 BULLISH"

    elif price < levels["s2"]:
        return "🔴 STRONG BEARISH"

    elif price < levels["s1"]:
        return "🔴 BEARISH"

    else:
        return "🟡 NEUTRAL"


# ==========================================================
# ALPHA VANTAGE NEWS
# ==========================================================

@st.cache_data(ttl=900)
def get_market_news():

    try:

        api_key = st.secrets["ALPHA_VANTAGE_API_KEY"]

        url = (
            "https://www.alphavantage.co/query"
            "?function=NEWS_SENTIMENT"
            "&topics=financial_markets"
            "&limit=20"
            f"&apikey={api_key}"
        )

        response = requests.get(
            url,
            timeout=20
        )

        data = response.json()

        news = []

        if "feed" in data:

            for item in data["feed"][:10]:

                news.append({
                    "title": item.get("title", ""),
                    "summary": item.get("summary", ""),
                    "sentiment": item.get(
                        "overall_sentiment_label",
                        "Neutral"
                    )
                })

        return news

    except Exception as e:

        st.error(f"News Error: {e}")

        return []


# ==========================================================
# NEWS ANALYSIS
# ==========================================================

def analyze_news(news):

    bullish = 0
    bearish = 0
    neutral = 0

    for item in news:

        sentiment = item["sentiment"]

        if "Bullish" in sentiment:
            bullish += 1

        elif "Bearish" in sentiment:
            bearish += 1

        else:
            neutral += 1

    total = bullish + bearish + neutral

    if total == 0:
        return {
            "call": "🟡 NEUTRAL",
            "bullish": 0,
            "bearish": 0,
            "neutral": 0,
            "bullish_pct": 0,
            "bearish_pct": 0
        }

    bullish_pct = round(
        bullish / total * 100
    )

    bearish_pct = round(
        bearish / total * 100
    )

    if bullish_pct > bearish_pct:
        call = "🟢 BULLISH"

    elif bearish_pct > bullish_pct:
        call = "🔴 BEARISH"

    else:
        call = "🟡 NEUTRAL"

    return {
        "call": call,
        "bullish": bullish,
        "bearish": bearish,
        "neutral": neutral,
        "bullish_pct": bullish_pct,
        "bearish_pct": bearish_pct
    }


# ==========================================================
# HEADER
# ==========================================================

st.title("📈 Sensex Intelligence")

st.caption(
    f"Updated: {datetime.now().strftime('%d-%b-%Y %H:%M:%S')}"
)

# ==========================================================
# MARKET SECTION
# ==========================================================

market = get_sensex_data()

if market is None:

    st.error(
        "Unable to fetch Sensex data."
    )

    st.stop()

levels = calculate_levels(
    market["prev_high"],
    market["prev_low"],
    market["prev_close"]
)

bias = get_market_bias(
    market["current"],
    levels
)

# ==========================================================
# LIVE SENSEX
# ==========================================================

st.markdown("## Live Sensex")

st.metric(
    label="Current Value",
    value=f"{market['current']:,.2f}",
    delta=f"{market['change']} ({market['change_pct']}%)"
)

# ==========================================================
# PREVIOUS DAY DATA
# ==========================================================

st.markdown("---")
st.subheader("Previous Day")

col1, col2, col3 = st.columns(3)

col1.metric(
    "High",
    f"{market['prev_high']:,.2f}"
)

col2.metric(
    "Low",
    f"{market['prev_low']:,.2f}"
)

col3.metric(
    "Close",
    f"{market['prev_close']:,.2f}"
)

# ==========================================================
# SUPPORT RESISTANCE
# ==========================================================

st.markdown("---")
st.subheader("Support & Resistance")

col1, col2 = st.columns(2)

with col1:
    st.success(
        f"Support 1 : {levels['s1']:,.2f}"
    )

    st.success(
        f"Support 2 : {levels['s2']:,.2f}"
    )

with col2:
    st.error(
        f"Resistance 1 : {levels['r1']:,.2f}"
    )

    st.error(
        f"Resistance 2 : {levels['r2']:,.2f}"
    )

# ==========================================================
# MARKET BIAS
# ==========================================================

st.markdown("---")
st.subheader("Market Bias")

st.markdown(
    f"### {bias}"
)

# ==========================================================
# NEWS
# ==========================================================

st.markdown("---")
st.subheader("Market Intelligence")

news = get_market_news()

analysis = analyze_news(news)

st.info(
    f"""
Overall Market Call: {analysis['call']}

Bullish Articles: {analysis['bullish']}
Bearish Articles: {analysis['bearish']}
Neutral Articles: {analysis['neutral']}

Bullish Probability: {analysis['bullish_pct']}%
Bearish Probability: {analysis['bearish_pct']}%
"""
)

# ==========================================================
# NEWS HEADLINES
# ==========================================================

st.subheader("Latest Market News")

if len(news) == 0:

    st.warning(
        "No news received from Alpha Vantage."
    )

else:

    for item in news:

        st.markdown(
            f"• {item['title']}"
        )

# ==========================================================
# SIMPLE SUMMARY
# ==========================================================

st.markdown("---")
st.subheader("15 Minute Market Summary")

if analysis["call"] == "🟢 BULLISH":

    st.success(
        """
Financial news sentiment is currently positive.

Market participants are showing
a bullish outlook based on recent
financial news flow.
"""
    )

elif analysis["call"] == "🔴 BEARISH":

    st.error(
        """
Financial news sentiment is currently negative.

Recent market developments suggest
a cautious or bearish outlook.
"""
    )

else:

    st.warning(
        """
Market sentiment is mixed.

No strong bullish or bearish trend
is visible from the latest news.
"""
    )

# ==========================================================
# FOOTER
# ==========================================================

st.markdown("---")

st.caption(
    "Sensex Intelligence Dashboard | Auto Refresh 60 Seconds | News Refresh 15 Minutes"
)