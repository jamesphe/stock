import pandas as pd
import akshare as ak
from datetime import datetime, timedelta

print("所有模块导入成功")

def is_trading_day(date):
    print(f"检查日期 {date.strftime('%Y-%m-%d')} 是否为交易日")
    try:
        calendar = ak.tool_trade_date_hist_sina()
        return date.strftime('%Y-%m-%d') in calendar['trade_date'].values
    except Exception as e:
        print(f"获取交易日历时出错: {e}")
        return False

def get_latest_trading_day():
    today = datetime.now()
    # 使用当前日期而不是未来日期
    return today.strftime('%Y%m%d')  # 使用 'YYYYMMDD' 格式

def update_stock_data(file_path):
    print("进入 update_stock_data 函数")
    df = pd.read_csv(file_path, parse_dates=['日期'])
    
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
    
    print(f"开始更新股票数据，时间范围: {start_date} 到 {end_date}")

    for index, row in df.iterrows():
        stock_code = row['股票代码']
        numeric_code = ''.join(filter(str.isdigit, stock_code))
        formatted_code = f"{'sh' if numeric_code.startswith(('6', '9')) else 'sz'}{numeric_code}"
        
        try:
            print(f"尝试获取 {formatted_code} 的数据...")
            stock_data = ak.stock_zh_a_daily(symbol=formatted_code, start_date=start_date, end_date=end_date)
            
            if not stock_data.empty:
                latest_data = stock_data.iloc[-1]
                close_price = latest_data['close']
                
                # 计算涨跌幅
                if len(stock_data) > 1:
                    prev_close = stock_data.iloc[-2]['close']
                    price_change = (close_price - prev_close) / prev_close * 100
                else:
                    price_change = 0
                
                df.at[index, '最新价'] = round(close_price, 2)
                df.at[index, '最新涨跌幅'] = round(price_change, 2)
                print(f"成功更新 {formatted_code} 的数据：最新价 {df.at[index, '最新价']}，最新涨跌幅 {df.at[index, '最新涨跌幅']}%")
            else:
                print(f"未找到 {formatted_code} 的最新数据")
        except Exception as e:
            print(f"获取 {formatted_code} 的数据时出错: {e}")
    
    # 如果 '涨跌幅' 列存在，删除它
    if '涨跌幅' in df.columns:
        df = df.drop('涨跌幅', axis=1)
    
    # 确保 '最新涨跌幅' 列在正确的位置
    columns = df.columns.tolist()
    if '最新涨跌幅' in columns:
        columns.remove('最新涨跌幅')
        price_index = columns.index('最新价')
        columns.insert(price_index + 1, '最新涨跌幅')
        df = df[columns]
    
    df.to_csv(file_path, index=False, encoding='utf-8-sig')
    print(f"更新后的数据已保存到原文件: {file_path}")

if __name__ == "__main__":
    print("准备执行主程序")
    file_path = 'output/均线多头_latest_data_2024-09-04.csv'
    update_stock_data(file_path)
    print("程序执行完毕")
