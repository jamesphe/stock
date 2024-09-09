# -*- coding: UTF-8 -*-

import numpy as np
import pandas as pd


def calculate_atr(high, low, close, length=14):
    tr = np.maximum(high - low, np.abs(high - close.shift(1)), np.abs(low - close.shift(1)))
    atr = tr.rolling(window=length).mean()
    print(f"计算得到的 ATR: {atr.tail()}")
    return atr

def true_range(high, low, close):
    return np.maximum(high - low, np.abs(high - close.shift(1)), np.abs(low - close.shift(1)))

def chandelier_exit(data, length=14, mult=2, use_close=True):
    print(f"开始计算 Chandelier Exit, 参数: length={length}, mult={mult}, use_close={use_close}")
    
    data = data.copy()  # 创建数据的副本以避免 SettingWithCopyWarning
    
    # 将这些行修改为使用正确的列名
    data['ATR'] = calculate_atr(data['最高'], data['最低'], data['收盘'], length)
    data['TR'] = true_range(data['最高'], data['最低'], data['收盘'])
    
    if use_close:
        data['highest'] = data['收盘'].rolling(window=length).max()
        data['lowest'] = data['收盘'].rolling(window=length).min()
    else:
        data['highest'] = data['最高'].rolling(window=length).max()
        data['lowest'] = data['最低'].rolling(window=length).min()
    
    data['Long_Stop'] = data['highest'] - (mult * data['ATR'])
    data['Short_Stop'] = data['lowest'] + (mult * data['ATR'])
    
    print(f"计算得到的 Long_Stop: {data['Long_Stop'].tail()}")
    print(f"计算得到的 Short_Stop: {data['Short_Stop'].tail()}")
    
    data['Direction'] = np.select(
        [data['收盘'] > data['Short_Stop'].shift(1), data['收盘'] < data['Long_Stop'].shift(1)],
        [1, -1],
        default=0
    )
    
    data['Direction'] = data['Direction'].replace(0).ffill()
    
    # 添加20日均线计算
    data['20日均线'] = data['收盘'].rolling(window=20).mean()

    # 修改买入信号的条件，使用已有的20日均线数据
    data['Buy_Signal'] = (data['Direction'] == 1) & (data['Direction'].shift(1) == -1) & (data['收盘'] > data['20日均线'])
    
    print(f"最后5个交易日的 Direction: {data['Direction'].tail()}")
    print(f"最后5个交易日的 Buy_Signal: {data['Buy_Signal'].tail()}")
    
    return data

def check_enter(code_name, data, end_date=None, length=14, mult=2.0, use_close=True):
    print(f"开始检查股票 {code_name} 是否满足进场条件")
    
    if end_date:
        data = data[data['时间'] <= end_date]
    
    if len(data) < length + 1:
        print(f"股票 {code_name} 数据不足，无法进行分析")
        return False

    data = chandelier_exit(data, length, mult, use_close)
    
    if data.iloc[-1]['Buy_Signal']:
        print(f"股票 {code_name} 在最后一个交易日产生买入信号")
        return True

    print(f"股票 {code_name} 在最后一个交易日没有产生买入信号")
    return False
