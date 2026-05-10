# coding:utf-8

import time
from datetime import datetime, date
from xtquant import xtdata
import pandas as pd

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.float_format', lambda x: '{:.10f}'.format(x))

# 记录上次执行的日期
last_run_date = None
# 青春版端口号
# xtdata.connect(port=58616)


print(f"===== 开始执行 {datetime.now()} =====")


# 下载元数据
xtdata.download_metatable_data()
metainfo = xtdata.get_metatable_list()
print(metainfo)

# 需要下载的表
tables = [
    # 'finance_balance_sheet',  # 负债
    # 'finance_income',         # 利润
    # 'finance_cash_flow',      # 现金流量表
    # 'global_etf_base_history',  # 海外新指数
    # 'announcement'
    'factor_sentiment'
]

for table_name in tables:
    try:
        print(f"\n正在处理: {table_name}")

        # 下载数据
        xtdata.download_tabular_data(
            ['XXXXXX.XX'],
            table_name,
            start_time='',
            end_time='',
            incrementally=None,
            download_type='validatebypage'
        )

        # 获取表配置
        info = xtdata.get_metatable_config(table_name)
        fields_zn = {v["fieldName"]: v["fieldNameCn"] for k, v in info["fields"].items()}
        fields_zn = {table_name + '.' + k: v for k, v in fields_zn.items()}

        # 获取数据
        df = xtdata.get_tabular_data([table_name], [], period='', start_time='', end_time='', count=-1)
        df = df.rename(columns=fields_zn)
        print(df)

    except Exception as e:
        print(f"{table_name} 错误: {e}")


