import akshare as ak
import pandas as pd
import datetime

def save_stock_data(stock_code):
    # 获取当前日期
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')

    # 获取股票近20天的行情数据
    stock_data = ak.stock_zh_a_hist(symbol=stock_code, period="daily", adjust="qfq", start_date=(datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y%m%d'), end_date=current_date.replace('-', ''))

    # 检查是否成功获取数据
    if stock_data.empty:
        print(f"无法获取股票 {stock_code} 的数据")
        return

    # 只保留最近20天的数据
    stock_data = stock_data.head(20)

    # 保存到本地文件，以股票代码和当天日期为文件名
    file_name = f"{stock_code}_{current_date}.csv"
    stock_data.to_csv(file_name, index=False)

    print(f"股票 {stock_code} 的近20天行情数据已保存到文件：{file_name}")