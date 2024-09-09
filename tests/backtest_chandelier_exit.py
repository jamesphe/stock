import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import akshare as ak
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import mplfinance as mpf
from matplotlib.ticker import FuncFormatter

from strategy.chandelier_exit import chandelier_exit

import datetime
import argparse

def get_stock_data(stock_code, start_date, end_date):
    """
    使用 akshare 获取股票日线历史数据
    """
    # 获取日线数据
    df = ak.stock_zh_a_hist(symbol=stock_code, start_date=start_date, end_date=end_date, adjust="qfq")
    
    # 重命名列以匹配原有代码
    df = df.rename(columns={
        "日期": "Date",
        "开盘": "Open",
        "最高": "High",
        "最低": "Low",
        "收盘": "Close",
        "成交量": "Volume"
    })
    
    # 将日期列设置为索引
    df.set_index("Date", inplace=True)
    df.index = pd.to_datetime(df.index)
    
    return df

def backtest_chandelier_exit(data):
    commission_rate = 0.001  # 假设佣金率为 0.1%
    initial_capital = 20000  # 初始资金

    print("数据框的列名:", data.columns)
    print("开始回测 Chandelier Exit 策略")
    
    # 在这里添加列名映射
    column_mapping = {
        'High': '最高',
        'Low': '最低',
        'Close': '收盘',
        'Open': '开盘',
        'Volume': '成交量'
    }
    
    # 重命名列
    data = data.rename(columns=column_mapping)
    
    # 应用 Chandelier Exit 策略
    data = chandelier_exit(data)
    
    # 将列名改回英文（如果后续代码需要）
    data = data.rename(columns={v: k for k, v in column_mapping.items()})
    
    # 计算20日均线
    data['MA20'] = data['Close'].rolling(window=20).mean()
    
    # 初始化回测结果
    data['Position'] = 0
    data['Cash'] = initial_capital
    data['Holdings'] = 0
    data['Portfolio'] = initial_capital
    
    position = 0
    buy_price = 0
    buy_date = None
    trades = []
    current_capital = initial_capital  # 当前可用资金

    for i in range(1, len(data)):
        if data.iloc[i]['Buy_Signal'] and position == 0:
            # 买入信号
            buy_price = data.iloc[i]['Close']
            buy_date = data.index[i]
            shares_to_buy = current_capital // (buy_price * (1 + commission_rate))  # 使用当前资金计算
            position = shares_to_buy
            cost = shares_to_buy * buy_price * (1 + commission_rate)
            current_capital -= cost  # 更新当前资金
            data.loc[data.index[i], 'Cash'] = current_capital
            data.loc[data.index[i], 'Holdings'] = shares_to_buy * data.iloc[i]['Close']
        elif data.iloc[i]['Direction'] == -1 and position > 0:
            # 卖出信号
            sell_price = data.iloc[i]['Close']
            sell_date = data.index[i]
            revenue = position * sell_price * (1 - commission_rate)
            current_capital += revenue  # 更新当前资金
            profit = revenue - (position * buy_price * (1 + commission_rate))
            returns = (sell_price / buy_price) - 1
            
            trades.append({
                '买入日期': buy_date,
                '买入价格': buy_price,
                '卖出日期': sell_date,
                '卖出价格': sell_price,
                '收益率': returns,
                '盈利金额': profit
            })
            
            data.loc[data.index[i], 'Cash'] = current_capital
            data.loc[data.index[i], 'Holdings'] = 0
            position = 0
            buy_price = 0
            buy_date = None
        else:
            # 持仓不变
            data.loc[data.index[i], 'Cash'] = current_capital
            data.loc[data.index[i], 'Holdings'] = position * data.iloc[i]['Close']
        
        data.loc[data.index[i], 'Position'] = position
        data.loc[data.index[i], 'Portfolio'] = data.iloc[i]['Cash'] + data.iloc[i]['Holdings']
    
    # 计算收益率和回撤
    data['Returns'] = data['Portfolio'].pct_change()
    data.loc[data.index[0], 'Returns'] = 0  # 设置第一天的收益率为0
    data['Cumulative_Returns'] = (1 + data['Returns']).cumprod() - 1
    data['Drawdown'] = (data['Portfolio'] / data['Portfolio'].cummax()) - 1
    
    # 计算策略指标
    total_return = data['Cumulative_Returns'].iloc[-1]
    max_drawdown = data['Drawdown'].min()
    sharpe_ratio = np.sqrt(252) * data['Returns'].mean() / data['Returns'].std()
    
    print(f"总收益率: {total_return:.2%}")
    print(f"最大回撤: {max_drawdown:.2%}")
    print(f"夏普比率: {sharpe_ratio:.2f}")
    
    # 打印交易记录
    print("\n交易记录：")
    for trade in trades:
        print(f"买入日期: {trade['买入日期'].strftime('%Y-%m-%d')}, 买入价格: {trade['买入价格']:.2f}")
        print(f"卖出日期: {trade['卖出日期'].strftime('%Y-%m-%d')}, 卖出价格: {trade['卖出价格']:.2f}")
        print(f"收益率: {trade['收益率']:.2%}, 盈利金额: {trade['盈利金额']:.2f}")
        print("---")
    
    return data, trades

# 使用示例
if __name__ == "__main__":
    # 创建参数解析器
    parser = argparse.ArgumentParser(description='运行 Chandelier Exit 策略回测')
    parser.add_argument('stock_code', type=str, help='股票代码，例如：601890')
    args = parser.parse_args()

    # 使用传入的股票代码
    stock_code = args.stock_code
    start_date = "20240101"
    end_date = datetime.date.today().strftime("%Y%m%d")
    
    print(f"正在对股票 {stock_code} 进行日线K线周期的回测分析...")
    
    # 使用 akshare 获取数据
    data = get_stock_data(stock_code, start_date, end_date)
    
    # 运行回测
    backtest_results, trades = backtest_chandelier_exit(data)
    
    # 创建一个新的图形对象和两个子图
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 16), sharex=True, gridspec_kw={'height_ratios': [3, 1]})

    # 设置红绿蜡烛图的颜色
    mc = mpf.make_marketcolors(up='red', down='green', inherit=True)
    s  = mpf.make_mpf_style(marketcolors=mc)

    # 准备买入和卖出信号的数据
    buy_signals = backtest_results[backtest_results['Buy_Signal']]
    sell_signals = backtest_results[(backtest_results['Direction'] == -1) & (backtest_results['Position'].shift(1) > 0)]

    # 创建买入和卖出信号的标记
    buy_markers = [None] * len(backtest_results)
    sell_markers = [None] * len(backtest_results)
    for date in buy_signals.index:
        buy_markers[backtest_results.index.get_loc(date)] = '^'
    for date in sell_signals.index:
        sell_markers[backtest_results.index.get_loc(date)] = 'v'

    # 在上面的子图中绘制红绿蜡烛图和买卖信号
    apds = [
        mpf.make_addplot(backtest_results['Long_Stop'], ax=ax1),
        mpf.make_addplot(backtest_results['Short_Stop'], ax=ax1),
        mpf.make_addplot(backtest_results['Portfolio'], ax=ax2),
        mpf.make_addplot(backtest_results['MA20'], ax=ax1, color='blue', width=1),  # 添加20日均线
        # 其addplot...
    ]
    mpf.plot(backtest_results, type='candle', ax=ax1, volume=False, show_nontrading=True, style=s, addplot=apds)

    # 在K图上添加买入点标记和价格标注
    for date, row in buy_signals.iterrows():
        ax1.scatter(date, row['Close'], color='green', marker='^', s=100)
        ax1.annotate(f'B:\n¥{row["Close"]:.2f}', (date, row['Close']), xytext=(0, 10), 
                     textcoords='offset points', ha='center', va='bottom',
                     bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),
                     rotation=45, fontsize=8)

    # 在K线图上添加卖出点标记和价格标注
    for date, row in sell_signals.iterrows():
        ax1.scatter(date, row['Close'], color='red', marker='v', s=100)
        ax1.annotate(f'S:\n¥{row["Close"]:.2f}', (date, row['Close']), xytext=(0, -10), 
                     textcoords='offset points', ha='center', va='top',
                     bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),
                     rotation=45, fontsize=8)

    # 添加时间刻度到 ax1（K线图）
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    ax1.xaxis.set_major_locator(mdates.AutoDateLocator())

    # 显示 ax1 的 x 轴标签
    ax1.tick_params(axis='x', rotation=45, labelsize=8)
    ax1.set_xlabel('')  # 移除 ax1 的 x 轴标签，因为它会与 ax2 的重叠

    # 在下面的子图中绘制投资组合价值
    ax2.plot(backtest_results.index, backtest_results['Portfolio'], label='Portfolio Value', color='blue')

    # 添加买入和卖出点到投资组合价值图
    ax2.scatter(buy_signals.index, buy_signals['Portfolio'], color='green', marker='^', s=100, label='Buy Signal')
    ax2.scatter(sell_signals.index, sell_signals['Portfolio'], color='red', marker='v', s=100, label='Sell Signal')

    # 为买入信号添加日期标签
    for date, value in zip(buy_signals.index, buy_signals['Portfolio']):
        ax2.annotate(date.strftime('%Y-%m-%d'), (date, value), xytext=(0, 10), 
                     textcoords='offset points', ha='center', va='bottom',
                     bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),
                     rotation=45, fontsize=8)

    # 为卖出信号添加日期标签
    for date, value in zip(sell_signals.index, sell_signals['Portfolio']):
        ax2.annotate(date.strftime('%Y-%m-%d'), (date, value), xytext=(0, -10), 
                     textcoords='offset points', ha='center', va='top',
                     bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),
                     rotation=45, fontsize=8)

    # 添加最大回撤区域
    max_drawdown_end = backtest_results['Drawdown'].idxmin()
    max_drawdown_start = backtest_results['Portfolio'][:max_drawdown_end].idxmax()
    ax2.fill_between(backtest_results.index, backtest_results['Portfolio'], 
                     where=(backtest_results.index >= max_drawdown_start) & (backtest_results.index <= max_drawdown_end), 
                     color='pink', alpha=0.3, label='Max Drawdown')

    # 设置 ax2 的 x 轴格式
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    ax2.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax2.tick_params(axis='x', rotation=45, labelsize=8)

    # 调整子图之间的间距
    plt.tight_layout()

    # 增加子图之间的垂直间距
    plt.subplots_adjust(hspace=0.3)

    # 将图例移到左上角，但稍微向右移动
    ax2.legend(loc='upper left', bbox_to_anchor=(0.02, 1.0))

    ax1.set_title(f'Chandelier Exit Strategy (Daily) - {stock_code} - Red/Green Candle Chart', fontsize=16)
    ax2.set_title(f'Portfolio Value (Daily) - {stock_code}', fontsize=16)

    ax2.set_xlabel('Date', fontsize=12)
    ax2.set_ylabel('Portfolio Value', fontsize=12)

    # 添加网格线
    ax2.grid(True, linestyle='--', alpha=0.7)

    # 将注释放到左下角
    total_return = backtest_results['Cumulative_Returns'].iloc[-1]
    max_drawdown = backtest_results['Drawdown'].min()
    sharpe_ratio = (backtest_results['Returns'].mean() / backtest_results['Returns'].std()) * np.sqrt(252)  # 假设252个交易日

    ax2.annotate(f'Total Return: {total_return:.2%}\nMax Drawdown: {max_drawdown:.2%}\nSharpe Ratio: {sharpe_ratio:.2f}', 
                 xy=(0.02, 0.02), xycoords='axes fraction', 
                 verticalalignment='bottom', horizontalalignment='left',
                 bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # 在 plt.show() 之前添加以下行
    # plt.get_current_fig_manager().window.showMaximized()

    plt.show()


