import sys
import os
import pandas as pd

# 将项目根目录添加到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import data_fetcher

# 准备股票代码列表
stocks = [
    ('000001', '平安银行'),
    ('600000', '浦发银行'),
    ('601318', '中国平安')
]

# 调用 run 函数获取股票数据
stocks_data = data_fetcher.run(stocks)

# 创建保存数据的目录
data_dir = os.path.join(project_root, "test_data")
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

# 处理获取到的数据
for stock, data in stocks_data.items():
    print(f"股票代码：{stock[0]}, 股票名称：{stock[1]}")
    print(data.head())  # 打印每只股票的前几行数据
    print("\n")
    
    # 保存数据到CSV文件
    file_name = f"{stock[0]}_{stock[1]}_60min_test.csv"
    file_path = os.path.join(data_dir, file_name)
    data.to_csv(file_path, index=False, encoding='utf-8-sig')
    print(f"数据已保存到文件: {file_path}")
    print("\n")

print("所有测试数据已保存完毕。")
