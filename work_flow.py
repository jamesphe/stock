# -*- encoding: UTF-8 -*-

import os
import data_fetcher
import settings
import strategy.enter as enter
from strategy import turtle_trade, climax_limitdown
from strategy import backtrace_ma250
from strategy import breakthrough_platform
from strategy import parking_apron
from strategy import low_backtrace_increase
from strategy import keep_increasing
from strategy import high_tight_flag
from strategy import chandelier_exit
import akshare as ak
import push
import logging
import time
import datetime
import pandas as pd
import ast

def prepare():
    logging.info("************************ process start ***************************************")
    all_data = ak.stock_zh_a_spot_em()
    subset = all_data[['代码', '名称']]
    stocks = [tuple(x) for x in subset.values]
    statistics(all_data, stocks)

    strategies = {
        '放量上涨': enter.check_volume,
        '均线多头': keep_increasing.check,
        '停机坪': parking_apron.check,
        #'回踩年线': backtrace_ma250.check,
        # '突破平台': breakthrough_platform.check,
        #'无大幅回撤': low_backtrace_increase.check,
        '海龟交易法则': turtle_trade.check_enter,
        #'高而窄的旗形': high_tight_flag.check,
        #'放量跌停': climax_limitdown.check,
        '吊灯止损': chandelier_exit.check_enter,
    }

    if datetime.datetime.now().weekday() == 0:
        strategies['均线多头'] = keep_increasing.check

    process(stocks, strategies)


    logging.info("************************ process   end ***************************************")

def process(stocks, strategies):
    stocks_data = data_fetcher.run(stocks)
    for strategy, strategy_func in strategies.items():
        check(stocks_data, strategy, strategy_func)
        time.sleep(2)

def check(stocks_data, strategy, strategy_func):
    end = settings.config['end_date']
    m_filter = check_enter(end_date=end, strategy_fun=strategy_func)
    results = dict(filter(m_filter, stocks_data.items()))
    
    if len(results) > 0:
        suitable_stocks = []
        latest_data = []  # 用于存储所有符合条件的股票的最新一条数据
        
        for stock_code, df in results.items():
            # 计算技术指标
            df = calculate_technical_indicators(df)
            
            # 计算STTS评分
            stts_score = calculate_advanced_stts_score(df)
            
            # 设定一个阈值，例如1.5，超过这个分数认为适合短线交易
            if stts_score > 1.5:
                latest_row = df.iloc[-1].copy()
                
                # 添加换手率、涨跌幅和收盘价的过滤条件
                if 3 <= latest_row['换手率'] <= 15 and -3 <= latest_row['涨跌幅'] <= 7 and 5 <= latest_row['收盘'] <= 40:
                    suitable_stocks.append(stock_code)
                    save_recent_20_days_data({(stock_code, ""): df},strategy)   
                    logging.info(f"股票代码 {stock_code} 适合短线交易，STTS分数: {stts_score}")
                    
                    # 获取最新一条行情数据，并添加到 latest_data 中
                    latest_row['股票代码'] = stock_code
                    latest_data.append(latest_row)
                else:
                    logging.info(f"股票代码 {stock_code} 的换手率、涨跌幅或收盘价不在指定范围内，未添加到最新行情数据。")
            else:
                logging.info(f"股票代码 {stock_code} 不适合短线交易，STTS分数: {stts_score}")
         
        # 将所有符合条件的股票的最新行情数据保存到同一个文件中
        if latest_data:
            save_latest_data_to_file(latest_data, strategy)
        
        if suitable_stocks:
            push.strategy('**************"{0}"**************\n{1}\n**************"{0}"**************\n'.format(strategy, suitable_stocks))
        else:
            logging.info(f"策略 '{strategy}' 没有筛选出适合短线交易的股票。")
    else:
        logging.info(f"策略 '{strategy}' 没有筛选出符合初步条件的股票。")

    # 防止请求过于频繁，适当增加延时
    time.sleep(2)

def save_latest_data_to_file(latest_data, strategy):
    """
    将符合条件的股票的最新行情数据保存到同一个CSV文件中。
    
    参数:
    latest_data (list): 每只股票最新行情数据的列表。
    strategy (str): 策略名称，用于文件命名。
    """
    # 转换为 DataFrame
    latest_df = pd.DataFrame(latest_data)
    
    # 构建文件名
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    file_name = f"{strategy}_latest_data_{current_date}.csv"
    file_path = os.path.join("output", file_name)

    # 保存为CSV文件
    latest_df.to_csv(file_path, index=False, encoding='utf-8-sig')
    print(f"所有符合条件股票的最新行情数据已保存到文件：{file_path}")

def check_enter(end_date=None, strategy_fun=enter.check_volume):
    def end_date_filter(stock_data):
        if end_date is not None:
            if end_date < stock_data[1].iloc[0].日期:  # 该股票在end_date时还未上市
                logging.debug("{}在{}时还未上市".format(stock_data[0], end_date))
                return False
        return strategy_fun(stock_data[0], stock_data[1], end_date=end_date)
    return end_date_filter

# 统计数据
def statistics(all_data, stocks):
    limitup = len(all_data.loc[(all_data['涨跌幅'] >= 9.5)])
    limitdown = len(all_data.loc[(all_data['涨跌幅'] <= -9.5)])

    up5 = len(all_data.loc[(all_data['涨跌幅'] >= 5)])
    down5 = len(all_data.loc[(all_data['涨跌幅'] <= -5)])

    msg = "涨停数：{}   跌停数：{}\n涨幅大于5%数：{}  跌幅大于5%数：{}".format(limitup, limitdown, up5, down5)
    push.statistics(msg)

def save_recent_20_days_data(results, strategy, output_dir="output"):
    # 获取当前日期
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')

    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for stock_info, df in results.items():
        # 解包股票信息，处理可能的嵌套元组
        if isinstance(stock_info[0], tuple):
            stock_code, stock_name = stock_info[0]
        else:
            stock_code, stock_name = stock_info
        
        # 如果 stock_name 为空，则使用 stock_code 作为文件名的一部分
        if not stock_name:
            stock_name = stock_code
        
        # 取最近20天的数据
        recent_20_days_data = df.tail(20)
        
        # 构建文件名，使用股票名称和日期
        file_name = f"{stock_name}_{current_date}.csv"
        file_path = os.path.join(output_dir, file_name)

        # 保存为CSV文件
        recent_20_days_data.to_csv(file_path, index=False, encoding='utf-8-sig')
        print(f"Saved {stock_name} ({stock_code}) data to {file_path}")

# 增加计算技术指标的函数
def calculate_technical_indicators(df):
    # 计算 ATR（平均真实波幅）
    df['最高-最低'] = df['最高'] - df['最低']
    df['最高-前收盘'] = abs(df['最高'] - df['收盘'].shift(1))
    df['最低-前收盘'] = abs(df['最低'] - df['收盘'].shift(1))
    df['真实波幅'] = df[['最高-最低', '最高-前收盘', '最低-前收盘']].max(axis=1)
    df['ATR'] = df['真实波幅'].rolling(window=14).mean().round(2)
    
    # 计算 MACD（指标参数12, 26, 9）
    df['EMA12'] = df['收盘'].ewm(span=12, adjust=False).mean().round(2)
    df['EMA26'] = df['收盘'].ewm(span=26, adjust=False).mean().round(2)
    df['MACD'] = (df['EMA12'] - df['EMA26']).round(2)
    df['信号线'] = df['MACD'].ewm(span=9, adjust=False).mean().round(2)
    df['MACD柱'] = (df['MACD'] - df['信号线']).round(2)
    
    # 计算布林带（Bollinger Bands）
    df['20日均线'] = df['收盘'].rolling(window=20).mean().round(2)
    df['20日标准差'] = df['收盘'].rolling(window=20).std().round(2)
    df['上轨'] = (df['20日均线'] + (df['20日标准差'] * 2)).round(2)
    df['下轨'] = (df['20日均线'] - (df['20日标准差'] * 2)).round(2)
    
    # 计算 RSI（相对强弱指数）
    df['价格变化'] = df['收盘'].diff(1)
    df['上涨'] = df['价格变化'].apply(lambda x: x if x > 0 else 0)
    df['下跌'] = df['价格变化'].apply(lambda x: -x if x < 0 else 0)
    df['平均上涨'] = df['上涨'].rolling(window=14).mean().round(2)
    df['平均下跌'] = df['下跌'].rolling(window=14).mean().round(2)
    df['相对强度'] = (df['平均上涨'] / df['平均下跌']).round(2)
    df['RSI'] = (100 - (100 / (1 + df['相对强度']))).round(2)
    
    return df

# 计算 STTS 分数的函数（中文名称，并保留两位小数）
def calculate_advanced_stts_score(df):
    # 振幅/10
    amplitude_score = round(df['振幅'].iloc[-1] / 10, 2)
    
    # 成交量/平均成交量
    average_volume = df['成交量'].rolling(window=5).mean().iloc[-1]
    volume_score = round(df['成交量'].iloc[-1] / average_volume, 2)
    
    # 换手率/5
    turnover_rate_score = round(df['换手率'].iloc[-1] / 5, 2)
    
    # 涨跌幅/5
    price_change_score = round(df['涨跌幅'].iloc[-1] / 5, 2)
    
    # ATR指标计算
    atr_score = round(df['ATR'].iloc[-1] / df['ATR'].rolling(window=14).mean().iloc[-1], 2)
    
    # MACD柱 越大越好
    macd_score = df['MACD柱'].iloc[-1]
    
    # 布林带宽度（上轨 - 下轨）
    bollinger_band_width = round((df['上轨'].iloc[-1] - df['下轨'].iloc[-1]) / df['收盘'].iloc[-1], 2)
    
    # RSI评分
    rsi_score = round((70 - df['RSI'].iloc[-1]) / 70, 2)  # 越接近70分数越低，超过70不建议短线操作
    
    # 综合得分
    stts_score = round((amplitude_score + volume_score + turnover_rate_score + price_change_score +
                  atr_score + macd_score + bollinger_band_width + rsi_score), 2)
    
    return stts_score
    # 振幅/10
    amplitude_score = df['振幅'].iloc[-1] / 10
    
    # 成交量/平均成交量
    average_volume = df['成交量'].rolling(window=5).mean().iloc[-1]
    volume_score = df['成交量'].iloc[-1] / average_volume
    
    # 换手率/5
    turnover_rate_score = df['换手率'].iloc[-1] / 5
    
    # 涨跌幅/5
    price_change_score = df['涨跌幅'].iloc[-1] / 5
    
    # ATR指标计算
    atr_score = df['ATR'].iloc[-1] / df['ATR'].rolling(window=14).mean().iloc[-1]
    
    # MACD柱 越大越好
    macd_score = df['MACD柱'].iloc[-1]
    
    # 布林带宽度（上轨 - 下轨）
    bollinger_band_width = (df['上轨'].iloc[-1] - df['下轨'].iloc[-1]) / df['收盘'].iloc[-1]
    
    # RSI评分
    rsi_score = (70 - df['RSI'].iloc[-1]) / 70  # 越接近70分数越低，超过70不建议短线操作
    
    # 综合得分
    stts_score = (amplitude_score + volume_score + turnover_rate_score + price_change_score +
                  atr_score + macd_score + bollinger_band_width + rsi_score)
    
    return stts_score
    # 振幅/10
    amplitude_score = df['振幅'].iloc[-1] / 10
    
    # 成交量/平均成交量
    average_volume = df['成交量'].rolling(window=5).mean().iloc[-1]
    volume_score = df['成交量'].iloc[-1] / average_volume
    
    # 换手率/5
    turnover_rate_score = df['换手率'].iloc[-1] / 5
    
    # 涨跌幅/5
    price_change_score = df['涨跌幅'].iloc[-1] / 5
    
    # ATR指标计算
    atr_score = df['ATR'].iloc[-1] / df['ATR'].rolling(window=14).mean().iloc[-1]
    
    # MACD Histogram 越大越好
    macd_score = df['MACD Histogram'].iloc[-1]
    
    # 布林带宽度（Upper Band - Lower Band）
    bollinger_band_width = (df['Upper Band'].iloc[-1] - df['Lower Band'].iloc[-1]) / df['收盘'].iloc[-1]
    
    # RSI评分
    rsi_score = (70 - df['RSI'].iloc[-1]) / 70  # 越接近70分数越低，超过70不建议短线操作
    
    # 综合得分
    stts_score = (amplitude_score + volume_score + turnover_rate_score + price_change_score +
                  atr_score + macd_score + bollinger_band_width + rsi_score)
    
    return stts_score