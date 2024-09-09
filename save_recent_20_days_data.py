import os
import datetime

def save_recent_20_days_data(results, output_dir="output"):
    # 获取当前日期
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')

    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for (stock_code, stock_name), df in results.items():
        # 取最近20天的数据
        recent_20_days_data = df.tail(20)
        
        # 构建文件名
        file_name = f"{stock_code}_{current_date}.csv"
        file_path = os.path.join(output_dir, file_name)

        # 保存为CSV文件
        recent_20_days_data.to_csv(file_path, index=False, encoding='utf-8-sig')
        print(f"Saved {stock_code} data to {file_path}")
