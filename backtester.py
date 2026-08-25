import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf

#download historical AAPL data
data = yf.download('AAPL', start='2020-01-01', end='2026-01-01')

# Remove multi-level columns
data.columns = data.columns.get_level_values(0)

#calculate moving averages
data['SMA20' ] = data['Close'].rolling(window=20).mean()
data['SMA50' ] = data['Close'].rolling(window=50).mean()

#starting portfolio
initial_cash = 10000  # Starting cash
cash = initial_cash  #set current cash to initial cash
shares = 0 #starting shares

values = []

#run backtest
for day in data.index:

    if day < data.index[50]:  # Skip the first 50 days to ensure SMA50 is available
        continue

    if data.loc[day, 'SMA20'] > data.loc[day, 'SMA50'] and cash > 0:
        # Buy shares as 20-day SMA is above 50-day SMA and we have cash
        bought_shares = int(cash //data.loc[day, 'Close'])
        cash -= bought_shares * data.loc[day, 'Close']
        shares += bought_shares

    elif data.loc[day, 'SMA20'] < data.loc[day, 'SMA50'] and shares > 0:
        # Sell shares as 20-day SMA is below 50-day SMA and we have shares
        cash += shares * data.loc[day, 'Close']
        shares = 0

    #Calculate portfolio value
    portfolio_value = cash + shares * data.loc[day, 'Close']

    values.append({'cash': cash, 
                   'shares': shares, 
                   'portfolio_value': portfolio_value
                   })

#extract results
portfolio_values = [value['portfolio_value'] for value in values]
cash_values = [value['cash'] for value in values]
shares_values = [value['shares'] for value in values]
total_return = (portfolio_value - initial_cash) / initial_cash * 100

# Buy-and-hold benchmark
initial_price = data.loc[data.index[50], 'Close']
final_price = data.loc[data.index[-1], 'Close']

buy_and_hold_shares = int(initial_cash // initial_price)
remaining_cash = initial_cash - (buy_and_hold_shares * initial_price)

buy_and_hold_value = (buy_and_hold_shares * final_price) + remaining_cash
buy_and_hold_return = ((buy_and_hold_value - initial_cash) / initial_cash) * 100

#print results
print(f"Final Portfolio Value: ${portfolio_value:.2f}")
print(f"Initial Capital: ${initial_cash:.2f}    ")
print(f"Total Return: {total_return:.2f}%")
print(f"Buy & Hold Return: {buy_and_hold_return:.2f}%")

#plot
plt.figure(1)
plt.plot(portfolio_values)
plt.title('Portfolio Value Over Time')
plt.xlabel('Trading Day')
plt.ylabel('Portfolio Value ($)')

plt.figure(2)
plt.plot(cash_values)
plt.title('Cash Over Time')
plt.xlabel('Trading Day')
plt.ylabel('Cash Value ($)')

plt.figure(3)
plt.plot(shares_values)
plt.title('Shares Over Time')
plt.xlabel('Trading Day')
plt.ylabel('Share Value ($)')

plt.show()



        
