import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import datetime
import numpy as np

available_stocks = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NFLX', 'NVDA']
initial_balance = 1000

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
    try:
        stock = yf.Ticker(ticker)
        return stock.history(period="1d")['Close'].iloc[-1]
    except:
        return 0.0

def fetch_stock_details(ticker):
    return yf.Ticker(ticker).info

def fetch_stock_history(ticker, period='1mo'):
    return yf.Ticker(ticker).history(period=period)

def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = delta.where(delta > 0, 0).rolling(window=window).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def main():
    st.title('📈 Advanced Paper Trading Simulator')
    initialize_session_state()

    st.sidebar.header('🔍 Stock Search')
    search_stock = st.sidebar.text_input('Enter stock ticker (e.g., AAPL):', value='AAPL')
    
    if search_stock:
        try:
            stock_info = fetch_stock_details(search_stock)
            st.sidebar.write(f"**{stock_info['shortName']} ({search_stock})**")
            st.sidebar.write(f"**Current Price:** ${stock_info['currentPrice']:.2f}")
            st.sidebar.write(f"**Market Cap:** ${stock_info['marketCap']:,}")
            st.sidebar.write(f"**52 Week High:** ${stock_info['fiftyTwoWeekHigh']:.2f}")
            st.sidebar.write(f"**52 Week Low:** ${stock_info['fiftyTwoWeekLow']:.2f}")
            st.sidebar.write(f"**Sector:** {stock_info['sector']}")
            st.sidebar.write(f"**Industry:** {stock_info['industry']}")
            st.sidebar.write(f"**Description:** {stock_info['longBusinessSummary']}")

            stock_history = fetch_stock_history(search_stock, period='6mo')
            stock_history['RSI'] = calculate_rsi(stock_history['Close'])
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=stock_history.index, y=stock_history['Close'], mode='lines', name='Close Price'))
            fig.add_trace(go.Scatter(x=stock_history.index, y=stock_history['RSI'], mode='lines', name='RSI'))
            fig.update_layout(title=f'{search_stock} Price and RSI', xaxis_title='Date', yaxis_title='Price/RSI')
            st.sidebar.plotly_chart(fig)
        except Exception as e:
            st.sidebar.error(f"⚠️ Could not fetch stock data: {e}")

    tabs = st.tabs(['Portfolio', 'Transaction History', 'Performance', 'Trade', 'Analytics', 'Watchlist', 'Load Money', 'Info'])

    with tabs[0]:
        st.subheader('📊 Your Virtual Portfolio')
        st.write(f'💰 Cash Balance: ${st.session_state.cash_balance:.2f}')
        portfolio_df = pd.DataFrame(list(st.session_state.portfolio.items()), columns=['Stock', 'Shares'])
        portfolio_df['Current Price'] = portfolio_df['Stock'].apply(fetch_stock_price)
        portfolio_df['Total Value'] = portfolio_df['Shares'] * portfolio_df['Current Price']
        st.table(portfolio_df)
        fig = px.pie(portfolio_df, values='Total Value', names='Stock', title='Portfolio Distribution')
        st.plotly_chart(fig)

    with tabs[1]:
        st.subheader('📄 Transaction History')
        if st.session_state.transaction_history:
            history_df = pd.DataFrame(st.session_state.transaction_history)
            history_df['Date'] = pd.to_datetime(history_df['Date'])
            st.table(history_df)
            fig = px.line(history_df, x='Date', y='Total', color='Type', title='Transaction History Over Time')
            st.plotly_chart(fig)
        else:
            st.info("No transactions yet.")

    with tabs[2]:
        st.subheader('📈 Portfolio Performance')
        if st.session_state.performance:
            performance_df = pd.DataFrame(st.session_state.performance)
            performance_df['Date'] = pd.to_datetime(performance_df['Date'])
            fig = px.line(performance_df, x='Date', y='Total Value', title='Portfolio Performance Over Time')
            st.plotly_chart(fig)

        st.subheader('🔍 Portfolio Analytics')
        total_value = sum(st.session_state.portfolio[stock] * fetch_stock_price(stock) for stock in available_stocks) + st.session_state.cash_balance
        st.write(f'Total Portfolio Value: ${total_value:.2f}')
        if total_value > 0:
            diversification = {
                stock: (st.session_state.portfolio[stock] * fetch_stock_price(stock)) / total_value
                for stock in available_stocks
            }
            diversification_df = pd.DataFrame(list(diversification.items()), columns=['Stock', 'Proportion'])
            fig = px.bar(diversification_df, x='Stock', y='Proportion', title='Portfolio Diversification')
            st.plotly_chart(fig)

    with tabs[3]:
        st.subheader('💼 Trade Stocks')
        selected_stock = st.selectbox('Select a stock:', available_stocks)
        current_price = fetch_stock_price(selected_stock)
        st.write(f'Current price of {selected_stock}: ${current_price:.2f}')
        quantity = st.number_input('Enter quantity:', min_value=1, step=1)

        if st.button('Buy'):
            cost = quantity * current_price
            if st.session_state.cash_balance >= cost:
                st.session_state.portfolio[selected_stock] += quantity
                st.session_state.cash_balance -= cost
                st.success(f'✅ Bought {quantity} shares of {selected_stock} at ${current_price:.2f}')
                st.session_state.transaction_history.append({
                    'Date': datetime.datetime.now(),
                    'Stock': selected_stock,
                    'Type': 'Buy',
                    'Quantity': quantity,
                    'Price': current_price,
                    'Total': cost
                })
                total_val = sum(st.session_state.portfolio[stock] * fetch_stock_price(stock) for stock in available_stocks) + st.session_state.cash_balance
                st.session_state.performance.append({'Date': datetime.datetime.now(), 'Total Value': total_val})
            else:
                st.error('❌ Insufficient funds.')

        if st.button('Sell'):
            if st.session_state.portfolio[selected_stock] >= quantity:
                revenue = quantity * current_price
                st.session_state.portfolio[selected_stock] -= quantity
                st.session_state.cash_balance += revenue
                st.success(f'✅ Sold {quantity} shares of {selected_stock} at ${current_price:.2f}')
                st.session_state.transaction_history.append({
                    'Date': datetime.datetime.now(),
                    'Stock': selected_stock,
                    'Type': 'Sell',
                    'Quantity': quantity,
                    'Price': current_price,
                    'Total': revenue
                })
                total_val = sum(st.session_state.portfolio[stock] * fetch_stock_price(stock) for stock in available_stocks) + st.session_state.cash_balance
                st.session_state.performance.append({'Date': datetime.datetime.now(), 'Total Value': total_val})
            else:
                st.error('❌ Not enough shares to sell.')

    with tabs[4]:
        st.subheader('📊 Advanced Analytics')
        st.write("### Risk Metrics (1 Year)")
        sp500 = yf.Ticker("^GSPC").history(period='1y')['Close'].pct_change().dropna()
        metrics = {}
        for stock in available_stocks:
            data = fetch_stock_history(stock, '1y')
            if not data.empty:
                returns = data['Close'].pct_change().dropna()
                aligned = pd.concat([returns, sp500], axis=1).dropna()
                aligned.columns = ['Stock', 'SP500']
                beta = np.cov(aligned['Stock'], aligned['SP500'])[0, 1] / np.var(aligned['SP500'])
                metrics[stock] = {
                    'Volatility': returns.std(),
                    'Beta': round(beta, 2)
                }
        st.table(pd.DataFrame(metrics).T)

    with tabs[5]:
        st.subheader('⭐ Watchlist')
        add_stock = st.selectbox('Add to watchlist:', available_stocks)
        if st.button('Add to Watchlist'):
            if add_stock not in st.session_state.watchlist:
                st.session_state.watchlist.append(add_stock)
                st.success(f'{add_stock} added.')
        if st.session_state.watchlist:
            st.write('### Your Watchlist')
            st.table(pd.DataFrame(st.session_state.watchlist, columns=['Stock']))
            selected = st.selectbox('Watch stock:', st.session_state.watchlist)
            chart = fetch_stock_history(selected)
            if not chart.empty:
                fig = go.Figure(data=[go.Candlestick(x=chart.index,
                                                     open=chart['Open'],
                                                     high=chart['High'],
                                                     low=chart['Low'],
                                                     close=chart['Close'])])
                fig.update_layout(title=f'{selected} Candlestick', xaxis_title='Date', yaxis_title='Price')
                st.plotly_chart(fig)

            remove = st.selectbox('Remove from Watchlist:', st.session_state.watchlist)
            if st.button('Remove'):
                st.session_state.watchlist.remove(remove)
                st.success(f'{remove} removed.')

    with tabs[6]:
        st.subheader('💳 Load Money')
        st.image('QR.jpg', caption='Scan QR to Pay', width=200)
        tx_id = st.text_input('Transaction ID:')
        if len(tx_id) >= 8:
            amount = st.number_input('Enter amount to load (20-50):', min_value=20, max_value=50)
            if st.button('Load Money'):
                bonus = amount * amount
                st.session_state.cash_balance += bonus
                st.success(f'₹{bonus} added to your balance.')

    with tabs[7]:
        st.subheader('ℹ️ Info')
        st.markdown("""
        - Step 1: Go to **Trade** and buy some stock  
        - Step 2: Visit **Portfolio** to view your holdings  
        - Step 3: Check **Transaction History**  
        - Step 4: Use **Analytics** for performance metrics  
        - Step 5: Add your favorite stocks in **Watchlist**  
        - Step 6: If low on cash, visit **Load Money**  
        """)
        st.write("Contact us: [Tradelit Care](https://tradelitcare.streamlit.app)")

if __name__ == '__main__':
    main()