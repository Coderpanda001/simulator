import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import datetime

available_stocks = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NFLX', 'NVDA']
initial_balance = 1000

# Generate consistent prices per run (can change seed each time to simulate new day)
np.random.seed(42)
random_prices = {stock: round(np.random.uniform(100, 500), 2) for stock in available_stocks}

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

def fetch_stock_price(ticker):
    return random_prices.get(ticker, 0.0)

def main():
    st.title("📊 Offline Paper Trading Simulator (Random Price)")

    initialize_session_state()

    tabs = st.tabs(["Portfolio", "Transactions", "Trade", "Performance", "Watchlist", "Load Money", "Info"])

    with tabs[0]:
        st.subheader("💼 Your Portfolio")
        st.write(f"💰 Cash Balance: ${st.session_state.cash_balance:.2f}")
        df = pd.DataFrame.from_dict(st.session_state.portfolio, orient='index', columns=['Shares'])
        df['Price'] = df.index.map(fetch_stock_price)
        df['Total'] = df['Shares'] * df['Price']
        st.dataframe(df)
        fig = px.pie(df[df['Total'] > 0], names=df[df['Total'] > 0].index, values='Total', title="Holdings")
        st.plotly_chart(fig)

    with tabs[1]:
        st.subheader("📜 Transaction History")
        if st.session_state.transaction_history:
            hist = pd.DataFrame(st.session_state.transaction_history)
            st.dataframe(hist)
        else:
            st.info("No transactions yet.")

    with tabs[2]:
        st.subheader("🛒 Trade Stocks")
        stock = st.selectbox("Select stock to trade:", available_stocks)
        price = fetch_stock_price(stock)
        st.write(f"📈 Price of {stock}: ${price}")
        qty = st.number_input("Quantity:", min_value=1, step=1)
        col1, col2 = st.columns(2)

        if col1.button("Buy"):
            cost = qty * price
            if st.session_state.cash_balance >= cost:
                st.session_state.portfolio[stock] += qty
                st.session_state.cash_balance -= cost
                st.success(f"Bought {qty} shares of {stock} for ${cost:.2f}")
                st.session_state.transaction_history.append({
                    'Date': datetime.datetime.now(),
                    'Stock': stock,
                    'Type': 'Buy',
                    'Quantity': qty,
                    'Price': price,
                    'Total': cost
                })
                update_performance()
            else:
                st.error("Not enough balance.")

        if col2.button("Sell"):
            if st.session_state.portfolio[stock] >= qty:
                rev = qty * price
                st.session_state.portfolio[stock] -= qty
                st.session_state.cash_balance += rev
                st.success(f"Sold {qty} shares of {stock} for ${rev:.2f}")
                st.session_state.transaction_history.append({
                    'Date': datetime.datetime.now(),
                    'Stock': stock,
                    'Type': 'Sell',
                    'Quantity': qty,
                    'Price': price,
                    'Total': rev
                })
                update_performance()
            else:
                st.error("Not enough stock to sell.")

    with tabs[3]:
        st.subheader("📈 Performance")
        if st.session_state.performance:
            df = pd.DataFrame(st.session_state.performance)
            fig = px.line(df, x='Date', y='Total Value', title='Portfolio Over Time')
            st.plotly_chart(fig)

    with tabs[4]:
        st.subheader("⭐ Watchlist")
        add_stock = st.selectbox("Add to watchlist:", available_stocks)
        if st.button("Add to Watchlist"):
            if add_stock not in st.session_state.watchlist:
                st.session_state.watchlist.append(add_stock)
                st.success(f"{add_stock} added to watchlist")
        if st.session_state.watchlist:
            st.write("Your Watchlist:")
            for s in st.session_state.watchlist:
                st.write(f"{s}: ${fetch_stock_price(s)}")
            remove_stock = st.selectbox("Remove from watchlist:", st.session_state.watchlist)
            if st.button("Remove from Watchlist"):
                st.session_state.watchlist.remove(remove_stock)
                st.success(f"{remove_stock} removed.")

    with tabs[5]:
        st.subheader("💳 Load Money")
        txid = st.text_input("Enter transaction ID:")
        if len(txid) >= 8:
            amt = st.number_input("Enter amount to load (20-50):", min_value=20, max_value=50)
            if st.button("Load Money"):
                bonus = amt * amt
                st.session_state.cash_balance += bonus
                st.success(f"${bonus} added to your balance.")

    with tabs[6]:
        st.subheader("ℹ️ Info")
        st.markdown("""
        - ✅ This is a **fully offline paper trading** simulator  
        - 📈 Prices are randomly generated when app loads  
        - 🛒 Trade, build a portfolio, monitor performance  
        - 💳 Load money using mock method  
        - 🔐 Safe for demos, schools, and offline learning
        """)

def update_performance():
    total_val = sum(st.session_state.portfolio[s] * fetch_stock_price(s) for s in available_stocks) + st.session_state.cash_balance
    st.session_state.performance.append({'Date': datetime.datetime.now(), 'Total Value': total_val})

if __name__ == "__main__":
    main()