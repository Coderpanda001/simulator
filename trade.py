import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import datetime
import numpy as np

# Stocks to use
available_stocks = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NFLX', 'NVDA']
initial_balance = 1000

# Initialize session state
def initialize_session_state():
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = {stock: 0 for stock in available_stocks}
    if 'cash_balance' not in st.session_state:
        st.session_state.cash_balance = initial_balance
    if 'transaction_history' not in st.session_state:
        st.session_state.transaction_history = []
    if 'performance' not in st.session_state:
        st.session_state.performance = []
    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = []

# Robust stock price fetch
def fetch_stock_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="2d")
        if hist.empty or 'Close' not in hist:
            st.warning(f"⚠️ No price data for {ticker}")
            return 0.0
        return hist['Close'].iloc[-1]
    except Exception as e:
        st.error(f"Error fetching {ticker}: {e}")
        return 0.0

def fetch_stock_details(ticker):
    try:
        return yf.Ticker(ticker).info
    except:
        return {}

def fetch_stock_history(ticker, period='1mo'):
    try:
        return yf.Ticker(ticker).history(period=period)
    except:
        return pd.DataFrame()

def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = delta.where(delta > 0, 0).rolling(window).mean()
    loss = -delta.where(delta < 0, 0).rolling(window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def main():
    st.title('📈 Advanced Paper Trading Simulator')
    initialize_session_state()

    # Sidebar - Search and show stock info
    st.sidebar.header('🔍 Stock Info')
    search = st.sidebar.text_input("Enter Stock Ticker (e.g., AAPL):", value="AAPL")
    if search:
        info = fetch_stock_details(search)
        if info:
            try:
                st.sidebar.write(f"**{info['shortName']} ({search})**")
                st.sidebar.write(f"📈 Price: ${info['currentPrice']}")
                st.sidebar.write(f"💼 Sector: {info.get('sector', 'N/A')}")
                st.sidebar.write(f"🏢 Industry: {info.get('industry', 'N/A')}")
                st.sidebar.write(info.get("longBusinessSummary", "No summary available"))

                history = fetch_stock_history(search, '6mo')
                if not history.empty:
                    history['RSI'] = calculate_rsi(history['Close'])
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=history.index, y=history['Close'], name='Close'))
                    fig.add_trace(go.Scatter(x=history.index, y=history['RSI'], name='RSI'))
                    fig.update_layout(title=f'{search} Chart & RSI')
                    st.sidebar.plotly_chart(fig)
            except:
                st.sidebar.warning("Could not load stock details.")

    # Tabs
    tabs = st.tabs(["Portfolio", "Transactions", "Performance", "Trade", "Analytics", "Watchlist", "Load Money", "Info"])

    with tabs[0]:
        st.subheader("📊 Portfolio")
        st.write(f"💰 Cash Balance: ${st.session_state.cash_balance:.2f}")
        df = pd.DataFrame.from_dict(st.session_state.portfolio, orient='index', columns=['Shares'])
        df['Price'] = df.index.map(fetch_stock_price)
        df['Total'] = df['Shares'] * df['Price']
        st.dataframe(df)
        fig = px.pie(df[df['Total'] > 0], names=df[df['Total'] > 0].index, values='Total', title="Holding Distribution")
        st.plotly_chart(fig)

    with tabs[1]:
        st.subheader("📄 Transaction History")
        if st.session_state.transaction_history:
            hist = pd.DataFrame(st.session_state.transaction_history)
            st.dataframe(hist)
            fig = px.line(hist, x='Date', y='Total', color='Type', title="Transaction History")
            st.plotly_chart(fig)
        else:
            st.info("No transactions yet.")

    with tabs[2]:
        st.subheader("📈 Portfolio Performance")
        if st.session_state.performance:
            perf = pd.DataFrame(st.session_state.performance)
            fig = px.line(perf, x='Date', y='Total Value', title='Performance Over Time')
            st.plotly_chart(fig)

        total_val = sum(st.session_state.portfolio[stock] * fetch_stock_price(stock) for stock in available_stocks) + st.session_state.cash_balance
        st.write(f"Total Value: ${total_val:.2f}")

    with tabs[3]:
        st.subheader("💼 Trade Stocks")
        stock = st.selectbox("Select stock:", available_stocks)
        price = fetch_stock_price(stock)
        st.write(f"Price of {stock}: ${price:.2f}")
        qty = st.number_input("Quantity:", min_value=1, step=1)

        if st.button("Buy"):
            cost = qty * price
            if st.session_state.cash_balance >= cost:
                st.session_state.portfolio[stock] += qty
                st.session_state.cash_balance -= cost
                st.success(f"Bought {qty} of {stock} for ${cost:.2f}")
                st.session_state.transaction_history.append({
                    'Date': datetime.datetime.now(),
                    'Stock': stock,
                    'Type': 'Buy',
                    'Quantity': qty,
                    'Price': price,
                    'Total': cost
                })
                total_val = sum(st.session_state.portfolio[s] * fetch_stock_price(s) for s in available_stocks) + st.session_state.cash_balance
                st.session_state.performance.append({'Date': datetime.datetime.now(), 'Total Value': total_val})
            else:
                st.error("Not enough balance.")

        if st.button("Sell"):
            if st.session_state.portfolio[stock] >= qty:
                rev = qty * price
                st.session_state.portfolio[stock] -= qty
                st.session_state.cash_balance += rev
                st.success(f"Sold {qty} of {stock} for ${rev:.2f}")
                st.session_state.transaction_history.append({
                    'Date': datetime.datetime.now(),
                    'Stock': stock,
                    'Type': 'Sell',
                    'Quantity': qty,
                    'Price': price,
                    'Total': rev
                })
                total_val = sum(st.session_state.portfolio[s] * fetch_stock_price(s) for s in available_stocks) + st.session_state.cash_balance
                st.session_state.performance.append({'Date': datetime.datetime.now(), 'Total Value': total_val})
            else:
                st.error("You don’t own enough to sell.")

    with tabs[4]:
        st.subheader("📊 Risk Analytics")
        risk_data = []
        for s in available_stocks:
            hist = fetch_stock_history(s, '1y')
            if not hist.empty:
                returns = hist['Close'].pct_change().dropna()
                volatility = returns.std()
                risk_data.append({'Stock': s, 'Volatility': volatility})
        st.dataframe(pd.DataFrame(risk_data))

    with tabs[5]:
        st.subheader("⭐ Watchlist")
        to_add = st.selectbox("Add to watchlist:", available_stocks)
        if st.button("Add"):
            if to_add not in st.session_state.watchlist:
                st.session_state.watchlist.append(to_add)
        if st.session_state.watchlist:
            st.write("Watchlist:", st.session_state.watchlist)
            for w in st.session_state.watchlist:
                hist = fetch_stock_history(w, '1mo')
                if not hist.empty:
                    fig = go.Figure(data=[go.Candlestick(x=hist.index,
                                                         open=hist['Open'],
                                                         high=hist['High'],
                                                         low=hist['Low'],
                                                         close=hist['Close'])])
                    fig.update_layout(title=f'{w} Chart')
                    st.plotly_chart(fig)

    with tabs[6]:
        st.subheader("💳 Load Money")
        st.image("QR.jpg", width=200, caption="Scan to Pay (fake)")
        txid = st.text_input("Enter Transaction ID:")
        if len(txid) >= 8:
            amount = st.number_input("Amount to Load:", min_value=20, max_value=50)
            if st.button("Load"):
                bonus = amount * amount
                st.session_state.cash_balance += bonus
                st.success(f"Added ${bonus} to your account!")

    with tabs[7]:
        st.subheader("ℹ️ How to Use")
        st.markdown("""
        - Go to **Trade** and buy/sell stocks  
        - View holdings in **Portfolio**  
        - Track changes in **Transactions** and **Performance**  
        - Add favorites in **Watchlist**  
        - Use **Load Money** if you run out  
        - Enjoy paper trading!
        """)

if __name__ == '__main__':
    main()