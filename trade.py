import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import random
import string

# Function to initialize session state variables
def init_session_state():
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = pd.DataFrame(columns=['Stock', 'Quantity', 'Total_Invested'])
    if 'history' not in st.session_state:
        st.session_state.history = pd.DataFrame(columns=['Date', 'Stock', 'Trade_Type', 'Quantity', 'Price'])
    if 'wallet_balance' not in st.session_state:
        st.session_state.wallet_balance = 0
    if 'generated_password' not in st.session_state:
        st.session_state.generated_password = ""

# Initialize session state
init_session_state()

# Function to add a trade
def add_trade(stock, trade_type, quantity, price):
    new_trade = pd.DataFrame({
        'Date': [datetime.now()],
        'Stock': [stock],
        'Trade_Type': [trade_type],
        'Quantity': [quantity],
        'Price': [price]
    })
    st.session_state.history = pd.concat([st.session_state.history, new_trade], ignore_index=True)
    
    if trade_type == 'Buy':
        if stock in st.session_state.portfolio['Stock'].values:
            st.session_state.portfolio.loc[st.session_state.portfolio['Stock'] == stock, 'Quantity'] += quantity
            st.session_state.portfolio.loc[st.session_state.portfolio['Stock'] == stock, 'Total_Invested'] += quantity * price
        else:
            new_row = pd.DataFrame({'Stock': [stock], 'Quantity': [quantity], 'Total_Invested': [quantity * price]})
            st.session_state.portfolio = pd.concat([st.session_state.portfolio, new_row], ignore_index=True)
    elif trade_type == 'Sell':
        if stock in st.session_state.portfolio['Stock'].values:
            st.session_state.portfolio.loc[st.session_state.portfolio['Stock'] == stock, 'Quantity'] -= quantity
            st.session_state.portfolio.loc[st.session_state.portfolio['Stock'] == stock, 'Total_Invested'] -= quantity * price
            if st.session_state.portfolio.loc[st.session_state.portfolio['Stock'] == stock, 'Quantity'].values[0] == 0:
                st.session_state.portfolio = st.session_state.portfolio[st.session_state.portfolio['Stock'] != stock]

# Function to generate a 6-digit password and load wallet
def load_wallet(input_string):
    if len(input_string) >= 8:
        # Generate a 6-digit password
        generated_password = ''.join(random.choices(string.digits, k=6))
        st.session_state.generated_password = generated_password
        
        # Load wallet based on input string
        if input_string == '001':
            st.session_state.wallet_balance += 500
        elif input_string == '110':
            st.session_state.wallet_balance += 1000
        st.success(f"Wallet loaded successfully with ${st.session_state.wallet_balance}!")

# Streamlit app layout
st.title("Enhanced Paper Trading App")

# Load Wallet section
st.header("Load Wallet")
input_string = st.text_input("Enter a string of at least 8 characters")
if st.button("Done Generate"):
    if len(input_string) >= 8:
        load_wallet(input_string)
    else:
        st.error("Input string must be at least 8 characters long")

# Display the generated password
if st.session_state.generated_password:
    st.write(f"Generated Password: {st.session_state.generated_password}")

# Display wallet balance
st.write(f"Wallet Balance: ${st.session_state.wallet_balance}")

# User input for trade
st.header("Add Trade")
stock = st.text_input("Stock Symbol", "")
trade_type = st.selectbox("Trade Type", ["Buy", "Sell"])
quantity = st.number_input("Quantity", min_value=1, step=1)
price = st.number_input("Price", min_value=0.0, step=0.01)

if st.button("Submit Trade"):
    if stock and quantity > 0 and price > 0:
        add_trade(stock, trade_type, quantity, price)
        st.success(f"Trade added: {trade_type} {quantity} of {stock} at ${price} each")
    else:
        st.error("Please enter valid trade details")

# Display portfolio
st.header("Portfolio")
if not st.session_state.portfolio.empty:
    st.write(st.session_state.portfolio)
else:
    st.write("No stocks in portfolio")

# Display trade history
st.header("Trade History")
if not st.session_state.history.empty:
    st.write(st.session_state.history)
else:
    st.write("No trade history")

# Plot portfolio value over time
st.header("Portfolio Value Over Time")
if not st.session_state.history.empty:
    history_df = st.session_state.history.copy()
    history_df['Date'] = pd.to_datetime(history_df['Date'])
    history_df['Total_Value'] = history_df['Quantity'] * history_df['Price']
    daily_value = history_df.groupby(history_df['Date'].dt.date)['Total_Value'].sum().cumsum()
    plt.figure(figsize=(10, 5))
    plt.plot(daily_value.index, daily_value.values, marker='o')
    plt.title("Portfolio Value Over Time")
    plt.xlabel("Date")
    plt.ylabel("Total Value")
    st.pyplot(plt)
else:
    st.write("No trade history to plot")

# Plot stock holdings
st.header("Stock Holdings")
if not st.session_state.portfolio.empty:
    plt.figure(figsize=(10, 5))
    plt.bar(st.session_state.portfolio['Stock'], st.session_state.portfolio['Quantity'])
    plt.title("Stock Holdings")
    plt.xlabel("Stock")
    plt.ylabel("Quantity")
    st.pyplot(plt)
else:
    st.write("No stocks to plot")

# Plot trade analysis
st.header("Trade Analysis")
if not st.session_state.history.empty:
    history_df = st.session_state.history.copy()
    buy_trades = history_df[history_df['Trade_Type'] == 'Buy']
    sell_trades = history_df[history_df['Trade_Type'] == 'Sell']
    plt.figure(figsize=(10, 5))
    plt.hist(buy_trades['Price'], bins=30, alpha=0.5, label='Buy Prices')
    plt.hist(sell_trades['Price'], bins=30, alpha=0.5, label='Sell Prices')
    plt.title("Trade Analysis")
    plt.xlabel("Price")
    plt.ylabel("Frequency")
    plt.legend()
    st.pyplot(plt)
else:
    st.write("No trade data to analyze")

# Simple performance metrics
st.header("Performance Metrics")
if not st.session_state.portfolio.empty:
    total_invested = sum(trade['Quantity'] * trade['Price'] for trade in st.session_state.history.to_dict('records') if trade['Trade_Type'] == 'Buy')
    total_value = st.session_state.portfolio['Total_Invested'].sum()
    performance = (total_value - total_invested) / total_invested * 100 if total_invested > 0 else 0
    st.write(f"Total Invested: ${total_invested:.2f}")
    st.write(f"Current Portfolio Value: ${total_value:.2f}")
    st.write(f"Overall Performance: {performance:.2f}%")
else:
    st.write("No performance metrics to display")