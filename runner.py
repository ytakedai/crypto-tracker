import pandas as pd
import json
import os

YEAR = 2022
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

def load_reports():
    global trades
    trades = pd.DataFrame(columns = ['Timestamp' ,'Transaction Type', 'Asset', 'Size', 'Price', 'Fees'])
    
    for file_name in os.listdir('./reports/'):
        if file_name.endswith('.csv'):
            temp_df = pd.read_csv('./reports/' + file_name, sep='/n', header=None, engine='python')
            temp_df = temp_df[0].str.split(',', expand=True)
            
            # Coinbase
            if 'You' in temp_df.iloc[0][0]:
                temp_df = temp_df.iloc[3:]

                header_row = 3
                temp_df.columns = temp_df.iloc[0]
                temp_df = temp_df.drop(header_row)
                temp_df = temp_df[['Timestamp', 'Transaction Type', 'Asset', 'Quantity Transacted', 'Spot Price at Transaction', 'Fees']]
            
                temp_df = temp_df.rename({'Quantity Transacted': 'Size', 'Spot Price at Transaction': 'Price'}, axis=1)
                trades = pd.concat([trades, temp_df], ignore_index=True)

            # Coinbase Pro
            elif 'portfolio' in temp_df.iloc[0][0]:
                temp_df = temp_df.iloc[0:]

                header_row = 0
                temp_df.columns = temp_df.iloc[0]
                temp_df = temp_df.drop(header_row)
                temp_df = temp_df[['created at', 'side', 'size unit', 'size', 'price', 'fee']]
            
                temp_df = temp_df.rename({'created at': 'Timestamp', 'side': 'Transaction Type', 'size unit': 'Asset', 'size':'Size', 'price': 'Price', 'fee': 'Fees'}, axis=1)
                trades = pd.concat([trades, temp_df], ignore_index=True)
            
            # Manual Entry
            elif 'Timestamp' in temp_df.iloc[0][0]:
                temp_df = temp_df.iloc[0:]

                header_row = 0
                temp_df.columns = temp_df.iloc[0]
                temp_df = temp_df.drop(header_row)
                if list(temp_df.columns) == ['Timestamp', 'Transaction Type', 'Asset', 'Size', 'Price', 'Fees']:
                    trades = pd.concat([trades, temp_df], ignore_index=True)
                else:
                    print('Manual entry file:' + file_name + 'does not have proper first row.')
                
    # Convert numbers to float type
    trades = trades.fillna(0)
    trades['Size'] = pd.to_numeric(trades.Size.astype(str).str.replace(',',''), errors='coerce').fillna(0.0).astype(float)
    trades['Price'] = pd.to_numeric(trades.Price.astype(str).str.replace(',',''), errors='coerce').fillna(0.0).astype(float)
    trades['Fees'] = pd.to_numeric(trades.Fees.astype(str).str.replace(',',''), errors='coerce').fillna(0.0).astype(float)

    # Save transactions to CSV
    trades.to_csv('trades.csv', encoding='utf-8', index=False)
    print(trades)

def load_trades():
    global trades

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
    sell_trades_detailed = pd.DataFrame(columns = ['Asset', 'Size', 'Buy Price', 'Sell Price', 'Total Sale', 'Gain', 'Percent Gain'])

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
                
                # long term/short term gain (accuracy down to the seconds)
                seconds_in_day = 24 * 60 * 60
                seconds_between_trade = (df_sells.iloc[sell_index]['Timestamp']-df_buys.iloc[buy_index]['Timestamp']).days
                
                # add trade details
                sell_trades_detailed = sell_trades_detailed.append({
                    'Buy Timestamp': df_buys.iloc[buy_index]['Timestamp'],
                    'Sell Timestamp': df_sells.iloc[sell_index]['Timestamp'],
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
                    'Buy Timestamp': df_sells.iloc[sell_index]['Timestamp'],
                    'Sell Timestamp': df_sells.iloc[sell_index]['Timestamp'],
                    'Asset': asset,
                    'Size': min(buy_remaining, sell_remaining),
                    'Buy Price': buy_price,
                    'Sell Price': sell_price,
                    'Total Sale': sell_price * min(buy_remaining, sell_remaining),
                    'Gain': sell_price * sell_remaining - buy_price * sell_remaining,
                    'Percent Gain': sell_price / buy_price * 100
                }, ignore_index=True)

    sell_trades_detailed['Buy Timestamp'] = pd.DatetimeIndex(sell_trades_detailed['Buy Timestamp'])
    sell_trades_detailed['Sell Timestamp'] = pd.DatetimeIndex(sell_trades_detailed['Sell Timestamp'])
    sell_trades_detailed['Days Held'] = (sell_trades_detailed['Sell Timestamp'] - sell_trades_detailed['Buy Timestamp']).astype('timedelta64[D]')
    sell_trades_detailed['Is Long Term'] = (sell_trades_detailed['Sell Timestamp'] - sell_trades_detailed['Buy Timestamp']).astype('timedelta64[D]') >= 365
    sell_trades_detailed['Sale Year'] = pd.DatetimeIndex(sell_trades_detailed['Sell Timestamp']).year
    

def print_detailed_report():
    global sell_trades_detailed
    if len(sell_trades_detailed.index) < 1:
        print('Transactions missing. Please enter trade details in trades.csv.')
        return

    if FILTER_YEAR:
        sell_trades_detailed = sell_trades_detailed.loc[sell_trades_detailed['Sale Year'] == YEAR]
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
    print('')

    print('Short Term Earnings:')
    sell_trades_detailed_short = sell_trades_detailed[sell_trades_detailed['Is Long Term'] == False]
    print('$' + str(round(sell_trades_detailed_short['Gain'].sum(), 2)))
    print('')

    print('Long Term Earnings:')
    sell_trades_detailed_long = sell_trades_detailed[sell_trades_detailed['Is Long Term'] == True]
    print('$' + str(round(sell_trades_detailed_long['Gain'].sum(), 2)))
    print('')


def main():
    load_reports()
    load_prices()
    load_trades()

    # get_balance()

    compute_earnings()

    print_detailed_report()

main()