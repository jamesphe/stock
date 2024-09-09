import akshare as ak
import pandas as pd
import talib
import argparse
from datetime import datetime, timedelta

def get_stock_data(stock_code, start_date, end_date):
    """
    使用akshare获取股票的历史行情数据
    """
    stock_df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
    
    stock_df['date'] = pd.to_datetime(stock_df['日期'])
    stock_df.set_index('date', inplace=True)
    
    expected_columns = ['开盘', '收盘', '最高', '最低', '成交量', '成交额', '振幅', '涨跌幅', '涨跌额', '换手率']
    stock_df = stock_df[expected_columns]
    stock_df.columns = ['open', 'close', 'high', 'low', 'volume', 'amount', 'amplitude', 'pct_change', 'change', 'turnover']
    
    # 确保数据按日期升序排列
    stock_df.sort_index(inplace=True)
    
    return stock_df[['open', 'high', 'low', 'close', 'volume']]

def check_trend_market(data):
    short_ma = talib.SMA(data['close'], timeperiod=20)
    long_ma = talib.SMA(data['close'], timeperiod=50)
    if short_ma.iloc[-1] > long_ma.iloc[-1]:
        return "上升趋势市场"
    elif short_ma.iloc[-1] < long_ma.iloc[-1]:
        return "下降趋势市场"
    else:
        return "震荡市场"

def check_adx_trend(data):
    adx = talib.ADX(data['high'], data['low'], data['close'], timeperiod=14)
    if adx.iloc[-1] > 25:
        return "强趋势市场"
    elif adx.iloc[-1] < 20:
        return "震荡市场"
    else:
        return "弱趋势市场"

def check_rsi_market(data):
    rsi = talib.RSI(data['close'], timeperiod=14)
    if 40 < rsi.iloc[-1] < 60:
        return "震荡市场"
    elif rsi.iloc[-1] > 70:
        return "超买，可能趋势反转"
    elif rsi.iloc[-1] < 30:
        return "超卖，可能趋势反转"
    else:
        return "趋势市场"

def check_macd_market(data):
    macd, macdsignal, macdhist = talib.MACD(data['close'], fastperiod=12, slowperiod=26, signalperiod=9)
    if macdhist.iloc[-1] > 0 and macdhist.iloc[-2] <= 0:
        return "趋势转向，可能为上升趋势"
    elif macdhist.iloc[-1] < 0 and macdhist.iloc[-2] >= 0:
        return "趋势转向，可能为下降趋势"
    else:
        return "震荡市场"

def priority_decision(trend_result, adx_result, rsi_result, macd_result):
    if '上升趋势' in trend_result and '强趋势' in adx_result:
        return "上升趋势市场"
    elif '下降趋势' in trend_result and '强趋势' in adx_result:
        return "下降趋势市场"
    elif '震荡' in macd_result and '震荡' in rsi_result:
        return "震荡市场"
    elif '弱趋势' in adx_result:
        return "弱趋势市场"
    return "市场信号不一致，需要进一步分析"

def analyze_market(stock_code, start_date, end_date):
    data = get_stock_data(stock_code, start_date, end_date)
    
    trend_market = check_trend_market(data)
    adx_trend = check_adx_trend(data)
    rsi_market = check_rsi_market(data)
    macd_market = check_macd_market(data)

    final_decision = priority_decision(trend_market, adx_trend, rsi_market, macd_market)

    print(f"股票代码: {stock_code}")
    print(f"趋势判断: {trend_market}")
    print(f"ADX趋势强度: {adx_trend}")
    print(f"RSI判断: {rsi_market}")
    print(f"MACD动能判断: {macd_market}")
    print(f"最终决策: {final_decision}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='股票市场分析工具')
    parser.add_argument('stock_code', type=str, help='股票代码')
    args = parser.parse_args()

    stock_code = args.stock_code
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=60)).strftime('%Y%m%d')  # 获取更多历史数据以计算指标

    print(f"分析时间范围: {start_date} 到 {end_date}")
    analyze_market(stock_code, start_date, end_date)