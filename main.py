import yfinance as yf
import pandas as pd

# Global variables
INITIAL_BALANCE = 100000  # Starting Capital

# Data Collection
def get_stock_data(ticker, interval):
    if interval == '1m':
        period = '7d'
    elif interval in ['2m', '5m', '15m', '30m', '90m']: 
        period = '60d'
    elif interval in ['60m', '1h']: 
        period = '730d'
    else:
        period = None 

    if period:
        stock = yf.download(ticker, period=period, interval=interval)
    else:
        stock = yf.download(ticker, start='2020-01-01', interval=interval) # Can adjust the start date here

    return stock

# Strategy
def def_strategy(data, short_window=5, long_window=20):
    data['EMA_Short'] = data['Close'].ewm(span=short_window, adjust=False).mean()
    data['EMA_Long'] = data['Close'].ewm(span=long_window, adjust=False).mean()

    # Short EMA > Long EMA.  1 = Buy Signal, 0 = No Signal.
    data['BuySignal'] = (data['EMA_Short'] > data['EMA_Long']).astype(int)

    return data

# Execution System
def execute_trades(data, initial_balance=INITIAL_BALANCE, allocation=0.9):
    balance = initial_balance
    position = 0   # Current number of shares held
    trade_log = []

    for idx, row in data.iterrows():
        price = row['Close']
        buy_signal = row['BuySignal']

        # Buy Condition
        if buy_signal == 1 and balance > price:
            invest_amount = balance * allocation
            shares_to_buy = int(invest_amount // price)
            cost = shares_to_buy * price
            if shares_to_buy > 0:
                balance -= cost
                position += shares_to_buy
                trade_log.append((idx, 'BUY', shares_to_buy, price, balance))

        # Sell Condition
        elif buy_signal == 0 and position > 0:
            shares_to_sell = position
            sale_value = shares_to_sell * price
            balance += sale_value
            trade_log.append((idx, 'SELL', shares_to_sell, price, balance))
            position = 0

    return balance, position, trade_log

# Backtesting
def backtest_performance(trades, final_portfolio_value, initial_balance=INITIAL_BALANCE):
    if not trades:
        return {
            "Total Return (%)": 0.0,
            "Number of Trades": 0,
            "Final Portfolio Value": round(final_portfolio_value, 2)
        }

    num_trades = len(trades)

    total_return_percent = (final_portfolio_value - initial_balance) / initial_balance * 100

    columns = ["Date", "Type", "Shares", "Price", "Balance"]
    df_trades = pd.DataFrame(trades, columns=columns)

    buys = df_trades[df_trades["Type"] == "BUY"]
    sells = df_trades[df_trades["Type"] == "SELL"]

    metrics = {
        "Initial Balance": initial_balance,
        "Final Portfolio Value": round(final_portfolio_value, 2),
        "Total Return (%)": round(total_return_percent, 2),
        "Number of Trades": num_trades,
        "Number of Buys": len(buys),
        "Number of Sells": len(sells)
    }
    return metrics

# Main
def main():
    ticker = 'AAPL' # Change Ticker Here
    interval = '1d' # Currently designed for daily trades
    data = get_stock_data(ticker, interval)
    data = def_strategy(data)

    cash_balance, shares_held, trades = execute_trades(data)

    if not data.empty:
        final_price = data['Close'].iloc[-1]
        portfolio_value = cash_balance + (shares_held * final_price)
    else:
        portfolio_value = cash_balance
    
    print(f"Cash Balance: ${cash_balance:.2f}")
    print(f"Shares Held in {ticker}: {shares_held}")
    print(f"Current Price of {ticker}: ${final_price:.2f}")
    print(f"Total Portfolio Value: ${portfolio_value:.2f}")

    # Print last 5 trades
    print("\nTrade Log (Last 5):")
    for trade in trades[-5:]:
        print(trade)

    metrics = backtest_performance(
        trades,
        final_portfolio_value=portfolio_value
    )

    #print("--- Backtest Results ---") # Uncomment for Backtest analysis
    #for k, v in metrics.items():
    #    print(f"{k}: {v}")

if __name__ == '__main__':
    main()

# Future steps: Diversify portfolio, Cap investment in single trades, HFT, Second Strategy: Breakout/RSI, Automatically Identify Stocks, ML enhancement.
