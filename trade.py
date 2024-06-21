import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import datetime
import numpy as np

# Define available stocks for simplicity
available_stocks = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NFLX', 'NVDA']

# Initial virtual balance
initial_balance = 1000

# Initialize session state variables
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
    stock = yf.Ticker(ticker)
    return stock.history(period="1d")['Close'].iloc[0]

def fetch_stock_details(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    return info

def fetch_stock_history(ticker, period='1mo'):
    stock = yf.Ticker(ticker)
    history = stock.history(period=period)
    return history

def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def main():
    st.title('Advanced Paper Trading Simulator')

    # Initialize session state
    initialize_session_state()

    # Sidebar for stock search
    st.sidebar.header('Stock Search')
    search_stock = st.sidebar.text_input('Enter stock ticker (e.g., AAPL):', value='AAPL')
    if search_stock:
        stock_info = fetch_stock_details(search_stock)
        st.sidebar.write(f"**{stock_info['shortName']} ({search_stock})**")
        st.sidebar.write(f"**Current Price:** ${stock_info['currentPrice']:.2f}")
        st.sidebar.write(f"**Market Cap:** ${stock_info['marketCap']:,}")
        st.sidebar.write(f"**52 Week High:** ${stock_info['fiftyTwoWeekHigh']:.2f}")
        st.sidebar.write(f"**52 Week Low:** ${stock_info['fiftyTwoWeekLow']:.2f}")
        st.sidebar.write(f"**Sector:** {stock_info['sector']}")
        st.sidebar.write(f"**Industry:** {stock_info['industry']}")
        st.sidebar.write(f"**Description:** {stock_info['longBusinessSummary']}")

        # Historical Stock Price Chart in Sidebar
        stock_history = fetch_stock_history(search_stock, period='6mo')
        stock_history['RSI'] = calculate_rsi(stock_history['Close'])
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=stock_history.index, y=stock_history['Close'], mode='lines', name='Close Price'))
        fig.add_trace(go.Scatter(x=stock_history.index, y=stock_history['RSI'], mode='lines', name='RSI'))
        fig.update_layout(title=f'{search_stock} Price and RSI', xaxis_title='Date', yaxis_title='Price/RSI')
        st.sidebar.plotly_chart(fig)

    # Tabs for different sections
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(['Portfolio', 'Transaction History', 'Performance', 'Trade', 'Analytics', 'Watchlist', 'Load Money', 'info'])

    with tab1:
        st.subheader('Your Virtual Portfolio')
        st.write(f'Cash balance: ${st.session_state.cash_balance:.2f}')
        portfolio_df = pd.DataFrame(list(st.session_state.portfolio.items()), columns=['Stock', 'Shares'])
        portfolio_df['Current Price'] = portfolio_df['Stock'].apply(fetch_stock_price)
        portfolio_df['Total Value'] = portfolio_df['Shares'] * portfolio_df['Current Price']
        st.table(portfolio_df)

        # Pie chart of portfolio distribution
        fig = px.pie(portfolio_df, values='Total Value', names='Stock', title='Portfolio Distribution')
        st.plotly_chart(fig)

    with tab2:
        st.subheader('Transaction History')
        if st.session_state.transaction_history:
            history_df = pd.DataFrame(st.session_state.transaction_history)
            st.table(history_df)

            # Plot transaction history
            fig = px.line(history_df, x='Date', y='Total', color='Type', title='Transaction History Over Time')
            st.plotly_chart(fig)

    with tab3:
        st.subheader('Portfolio Performance')
        if st.session_state.performance:
            performance_df = pd.DataFrame(st.session_state.performance)
            fig = px.line(performance_df, x='Date', y='Total Value', title='Portfolio Performance Over Time')
            st.plotly_chart(fig)

        # Advanced Portfolio Analytics
        st.subheader('Portfolio Analytics')
        portfolio_value = sum(st.session_state.portfolio[stock] * fetch_stock_price(stock) for stock in available_stocks)
        total_value = portfolio_value + st.session_state.cash_balance
        st.write(f'Total portfolio value: ${total_value:.2f}')

        diversification = {stock: (st.session_state.portfolio[stock] * fetch_stock_price(stock)) / total_value for stock in available_stocks}
        diversification_df = pd.DataFrame(list(diversification.items()), columns=['Stock', 'Proportion'])
        fig = px.bar(diversification_df, x='Stock', y='Proportion', title='Portfolio Diversification')
        st.plotly_chart(fig)

    with tab4:
        st.subheader('Trade Stocks')
        # Display available stocks
        selected_stock = st.selectbox('Select a stock:', available_stocks)
        
        # Get real-time price of the selected stock
        current_price = fetch_stock_price(selected_stock)
        st.write(f'Current price of {selected_stock}: ${current_price:.2f}')

        # Get user input for quantity of stocks to buy/sell
        quantity = st.number_input('Enter quantity:', min_value=1, step=1)

        # Buttons for buying and selling
        buy_button = st.button('Buy')
        sell_button = st.button('Sell')

        # Simulate buying/selling stocks
        if buy_button or sell_button:
            transaction_type = 'Buy' if buy_button else 'Sell'
            cost = quantity * current_price
            
            if buy_button and st.session_state.cash_balance >= cost:
                st.session_state.portfolio[selected_stock] += quantity
                st.session_state.cash_balance -= cost
            elif sell_button and st.session_state.portfolio[selected_stock] >= quantity:
                st.session_state.portfolio[selected_stock] -= quantity
                st.session_state.cash_balance += cost
            else:
                st.error('Transaction could not be completed due to insufficient funds or stocks.')
                return

            # Record transaction
            st.session_state.transaction_history.append({
                'Date': datetime.datetime.now(),
                'Stock': selected_stock,
                'Type': transaction_type,
                'Quantity': quantity,
                'Price': current_price,
                'Total': cost
            })

            # Record performance
            total_value = sum(st.session_state.portfolio[stock] * fetch_stock_price(stock) for stock in available_stocks) + st.session_state.cash_balance
            st.session_state.performance.append({
                'Date': datetime.datetime.now(),
                'Total Value': total_value
            })

            st.success(f'{transaction_type} {quantity} shares of {selected_stock} at ${current_price:.2f} each.')

    with tab5:
        st.subheader('Advanced Analytics')
        
        st.write("### Risk Metrics")
        risk_metrics = {}
        for stock in available_stocks:
            stock_data = fetch_stock_history(stock, period='1y')
            returns = stock_data['Close'].pct_change().dropna()
            risk_metrics[stock] = {
                'Standard Deviation': returns.std(),
                'Beta': np.cov(returns, returns)[0, 1] / np.var(returns)
            }

        risk_metrics_df = pd.DataFrame(risk_metrics).T
        st.table(risk_metrics_df)

        # Comparison with S&P 500
        st.write("### Performance Comparison with S&P 500")
        sp500 = yf.Ticker("^GSPC").history(period='1y')
        sp500['Returns'] = sp500['Close'].pct_change().dropna()
        
        if st.session_state.performance:
            portfolio_values = pd.Series([perf['Total Value'] for perf in st.session_state.performance])
            portfolio_returns = portfolio_values.pct_change().dropna()

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=portfolio_returns.index, y=portfolio_returns, mode='lines', name='Portfolio Returns'))
            fig.add_trace(go.Scatter(x=sp500['Returns'].index, y=sp500['Returns'], mode='lines', name='S&P 500 Returns'))
            fig.update_layout(title='Portfolio vs S&P 500 Returns', xaxis_title='Date', yaxis_title='Returns')
            st.plotly_chart(fig)

    with tab6:
        st.subheader('Watchlist')
        
        # Add stocks to watchlist
        add_stock = st.selectbox('Add stock to watchlist:', available_stocks)
        if st.button('Add to Watchlist'):
            if add_stock not in st.session_state.watchlist:
                st.session_state.watchlist.append(add_stock)
                st.success(f'{add_stock} added to watchlist.')
            else:
                st.warning(f'{add_stock} is already in the watchlist.')

        # Display watchlist
        if st.session_state.watchlist:
            st.write('### Your Watchlist')
            watchlist_df = pd.DataFrame(st.session_state.watchlist, columns=['Stock'])
            st.table(watchlist_df)

            # Select stock from watchlist to display candlestick chart
            watchlist_stock = st.selectbox('Select a stock from watchlist to view chart:', st.session_state.watchlist)
            if watchlist_stock:
                stock_history = fetch_stock_history(watchlist_stock, period='1mo')
                fig = go.Figure(data=[go.Candlestick(x=stock_history.index,
                                                     open=stock_history['Open'],
                                                     high=stock_history['High'],
                                                     low=stock_history['Low'],
                                                     close=stock_history['Close'])])
                fig.update_layout(title=f'Candlestick Chart for {watchlist_stock}', xaxis_title='Date', yaxis_title='Price')
                st.plotly_chart(fig)

            # Option to remove stock from watchlist
            remove_stock = st.selectbox('Remove stock from watchlist:', st.session_state.watchlist)
            if st.button('Remove from Watchlist'):
                st.session_state.watchlist.remove(remove_stock)
                st.success(f'{remove_stock} removed from watchlist.')

    with tab7:
        st.subheader('Load Money')
        st.write('scan QR using any payment aggregator || copy your transaction id and enter below')
        st.image('QR.jpg', caption='Scan this QR code for payment', width=200)
        st.write('Enter your transaction ID to proceed with loading money.')
        st.markdown("<marquee style='color: red;'>Caution: Enter transaction ID only after payment. If we don't find a matching ID, REFUND will not be executed.</marquee>", unsafe_allow_html=True)
        random_number = st.text_input('Transaction ID:')
        if len(random_number) >= 8:
            amount_to_load = st.number_input('Enter amount to load (20-50):', min_value=20, max_value=50)
            if st.button('Load Money'):
                st.session_state.cash_balance += amount_to_load * amount_to_load
                st.success(f'${amount_to_load * amount_to_load} loaded to your account.')
    with tab8:
        st.subheader('Information')
        st.write('this simulator just shows the working of trading platform , where beginners can get started')
        st.write('there are tabs/options to choose but follow these steps for clear vision')
        st.write('step 1 : go to trade and buy some stock')
        st.write('step 2 : check out portfolio for holding info')
        st.write('step 3 : checkout transactions for transacted details ')
        st.write('info: you can know more about stock in left top bar button , add correct stock keyword  ')
        st.write('info :  you can put some stocks for watclist in watchlist tab')
        st.write('info : if you run out of money , visit load money tab ')
        st.write('great! now youre good to go , try out more  ')
        st.write('Thankyou')
        st.write(" click link to contact us : https://tradelitcare.streamlit.app ")
  
if __name__ == '__main__':
    main()
