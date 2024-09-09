import sys
import os
import pandas as pd
from datetime import date
import numpy as np

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from strategy.chandelier_exit import check_enter

def load_test_data(file_path):
    data = pd.read_csv(file_path, parse_dates=['日期'])
    return data

def test_chandelier_exit():
    data = load_test_data('../output/国民技术_2024-09-06.csv')
    
    today = date.today().strftime('%Y-%m-%d')
    
    测试场景 = [
        ("默认参数", {}),
        ("自定义参数", {"length": 30, "mult": 2.5}),
        ("当天日期", {"end_date": today})
    ]

    for 描述, 参数 in 测试场景:
        print(f"\n测试{描述}:")
        result = check_enter('测试股票', data, **参数)
        print(f"是否应该进入交易：{result}")

if __name__ == "__main__":
    test_chandelier_exit()