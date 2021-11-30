import pandas as pd
import json

YEAR = 2021
FILTER_YEAR = True

crypto_prices = None
trades = None
sell_trades_detailed = None

days_in_month = {
    1:31,
    2:28,
    3:31,
    4:30,
    5:31,
    6:30,
    7:31,
    8:31,
    9:30,
    10:31,
    11:30,
    12:31
}

def load_trades():
    global trades
    trades = pd.read_csv('trades.csv')

    trades['Transaction Type'] = trades['Transaction Type'].str.upper()
    trades['Timestamp'] = pd.to_datetime(trades.Timestamp)

    trades = trades.sort_values(['Timestamp']) # This now sorts in date order
    #print(trades)

def load_prices():
    global crypto_prices
    with open('crypto_prices.json', 'r') as json_file:
        crypto_prices = json.load(json_file)
    #print(crypto_prices['eth'])

def get_balance():
    df = trades.groupby(['Asset', 'Transaction Type']).sum()
    #print(df)

def compute_earnings():
    global sell_trades_detailed
    sell_trades_detailed = pd.DataFrame(columns = ['Timestamp', 'Asset', 'Size', 'Buy Price', 'Sell Price', 'Total Sale', 'Gain', 'Percent Gain'])

    assets = trades['Asset'].unique()
    # filter by coin type
    for asset in assets:

        df = trades[trades['Asset'] == asset]
        df_buys = df[df['Transaction Type'] == 'BUY']
        df_sells = df[df['Transaction Type'] == 'SELL']

        # check for sales
        if len(df_sells.index) > 0:
            buy_index = 0
            buy_len = len(df_buys.index)
            buy_remaining = 0
            buy_price = None

            sell_index = 0
            sell_len = len(df_sells.index)
            sell_remaining = 0
            sell_price = None

            # end condition: run out of sells or run out of btc bought
            while buy_index < buy_len and sell_index < sell_len:
                if buy_remaining == 0:
                    buy_remaining = df_buys.iloc[buy_index]['Size']
                    buy_price = df_buys.iloc[buy_index]['Price']
                if sell_remaining == 0:
                    sell_remaining = df_sells.iloc[sell_index]['Size']
                    sell_price = df_sells.iloc[sell_index]['Price']
                
                sell_trades_detailed = sell_trades_detailed.append({
                    'Timestamp': df_sells.iloc[sell_index]['Timestamp'],
                    'Asset': asset,
                    'Size': min(buy_remaining, sell_remaining),
                    'Buy Price': buy_price,
                    'Sell Price': sell_price,
                    'Total Sale': sell_price * min(buy_remaining, sell_remaining),
                    'Gain': sell_price * min(buy_remaining, sell_remaining) - buy_price * min(buy_remaining, sell_remaining),
                    'Percent Gain': (sell_price - buy_price) / buy_price * 100
                }, ignore_index=True)

                buy_remaining = buy_remaining - min(buy_remaining, sell_remaining)
                sell_remaining = sell_remaining - min(buy_remaining, sell_remaining)

                if buy_remaining == 0:
                    buy_index += 1
                if sell_remaining == 0:
                    sell_index += 1

            # calculate any extra using previous cost basis
            if sell_remaining > 0:
                sell_trades_detailed = sell_trades_detailed.append({
                    'Timestamp': df_sells.iloc[sell_index]['Timestamp'],
                    'Asset': asset,
                    'Size': min(buy_remaining, sell_remaining),
                    'Buy Price': buy_price,
                    'Sell Price': sell_price,
                    'Total Sale': sell_price * min(buy_remaining, sell_remaining),
                    'Gain': sell_price * sell_remaining - buy_price * sell_remaining,
                    'Percent Gain': sell_price / buy_price * 100
                }, ignore_index=True)

    # doesnt work yet
    sell_trades_detailed['Year'] = pd.DatetimeIndex(sell_trades_detailed['Timestamp']).year
    

def print_detailed_report():
    global sell_trades_detailed
    if len(sell_trades_detailed.index) < 1:
        print('Transactions missing. Please enter trade details in trades.csv.')
        return

    if FILTER_YEAR:
        sell_trades_detailed = sell_trades_detailed.loc[sell_trades_detailed['Year'] == YEAR]
        if len(sell_trades_detailed.index) < 1:
            print('No crypto sales for defined year.')
            return

    print('Crypto Sales:')        
    print(sell_trades_detailed)
    print('')

    print('Total Observed Earnings:')
    print('$' + str(round(sell_trades_detailed['Gain'].sum(), 2)))
    print('')

    print('Total Sale:')
    print('$' + str(round(sell_trades_detailed['Total Sale'].sum(), 2)))
    print('')

    print('Average Observed Gain:')
    print(str(round(sell_trades_detailed['Gain'].sum()/(sell_trades_detailed['Total Sale'].sum())*100, 2)) + '%')


def main():
    load_prices()
    load_trades()

    # get_balance()

    compute_earnings()

    print_detailed_report()

main()