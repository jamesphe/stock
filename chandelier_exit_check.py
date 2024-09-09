import akshare as ak
import talib
import pandas as pd
import numpy as np
import argparse

# 获取股票数据
def get_stock_data(stock_code, start_date, end_date):
    stock_df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
    print(f"原始数据列: {stock_df.columns}")
    print(f"原始数据形状: {stock_df.shape}")
    
    stock_df['date'] = pd.to_datetime(stock_df['日期'])
    stock_df.set_index('date', inplace=True)
    
    expected_columns = ['开盘', '收盘', '最高', '最低', '成交量', '成交额', '振幅', '涨跌幅', '涨跌额', '换手率']
    stock_df = stock_df[expected_columns]
    stock_df.columns = ['open', 'close', 'high', 'low', 'volume', 'amount', 'amplitude', 'pct_change', 'change', 'turnover']
    
    print(f"处理后数据列: {stock_df.columns}")
    print(f"处理后数据形状: {stock_df.shape}")
    
    # 确保数据按日期升序排列
    stock_df.sort_index(inplace=True)
    
    return stock_df[['open', 'high', 'low', 'close', 'volume']]

# 计算ATR
def calculate_atr(data, period=14):
    high = data['high'].values
    low = data['low'].values
    close = data['close'].values
    atr = talib.ATR(high, low, close, timeperiod=period)
    data['ATR'] = atr
    return data

# 计算Chandelier Exit
def chandelier_exit(data, length=14, mult=2.0, use_close=True):
    data = calculate_atr(data, period=length)
    
    if use_close:
        data['highest'] = data['close'].rolling(window=length).max()
        data['lowest'] = data['close'].rolling(window=length).min()
    else:
        data['highest'] = data['high'].rolling(window=length).max()
        data['lowest'] = data['low'].rolling(window=length).min()
    
    data['long_stop'] = data['highest'] - mult * data['ATR']
    data['short_stop'] = data['lowest'] + mult * data['ATR']
    
    data['long_stop'] = np.where(
        (data['close'].shift(1) > data['long_stop'].shift(1)) & (data['long_stop'] > data['long_stop'].shift(1)),
        data['long_stop'],
        data['long_stop'].shift(1)
    )
    
    data['short_stop'] = np.where(
        (data['close'].shift(1) < data['short_stop'].shift(1)) & (data['short_stop'] < data['short_stop'].shift(1)),
        data['short_stop'],
        data['short_stop'].shift(1)
    )
    
    data['dir'] = np.where(data['close'] > data['short_stop'].shift(1), 1,
                           np.where(data['close'] < data['long_stop'].shift(1), -1, np.nan))
    data['dir'] = data['dir'].fillna(method='ffill')
    
    data['Chandelier_Exit'] = np.where(data['dir'] == 1, data['long_stop'], data['short_stop'])
    
    return data

# 生成买卖信号
def generate_signal(data):
    current_dir = data['dir'].iloc[-1]
    prev_dir = data['dir'].iloc[-2]
    
    if current_dir == 1 and prev_dir == -1:
        return "买入信号"
    elif current_dir == -1 and prev_dir == 1:
        return "卖出信号"
    else:
        return "持仓不变"

# 主程序
if __name__ == "__main__":
    # 创建参数解析器
    parser = argparse.ArgumentParser(description='检查股票的 Chandelier Exit 信号')
    parser.add_argument('stock_code', type=str, help='股票代码')
    args = parser.parse_args()

    stock_code = args.stock_code  # 从命令行参数获取股票代码
    start_date = "20240101"  # 起始日期
    end_date = pd.Timestamp.today().strftime('%Y%m%d')  # 截止日期为当天

    # 获取股票数据
    stock_data = get_stock_data(stock_code, start_date, end_date)
    
    print(f"最终数据头部:\n{stock_data.head()}")
    print(f"最终数据尾部:\n{stock_data.tail()}")

    # 计算Chandelier Exit
    stock_data = chandelier_exit(stock_data)
    
    # 生成交易信号
    signal = generate_signal(stock_data)
    latest_close = stock_data['close'].iloc[-1]
    latest_exit = stock_data['Chandelier_Exit'].iloc[-1]
    latest_date = stock_data.index[-1]
    latest_dir = stock_data['dir'].iloc[-1]

    print(f"\n股票代码: {stock_code}")
    print(f"最新交易日期: {latest_date.strftime('%Y-%m-%d')}")
    print(f"最新收盘价: {latest_close:.2f}")
    print(f"Chandelier Exit: {latest_exit:.2f}")
    print(f"当前方向: {'多头' if latest_dir == 1 else '空头'}")
    print(f"交易信号: {signal}")