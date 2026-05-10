# Strategies

- `current\STOCK_FACTOR_BASELINE.py` 是从迅投终端策略目录复制出的当前快照。
- 终端里的实际运行文件仍是 `D:\迅投极速交易终端睿智融科版\python\STOCK_FACTOR_BASELINE.py`。
- 每次重大改动建议另存一个明确版本，例如 `v20260510_factor_filter.py`。
- 回测版、模拟盘版和实盘版不要混用；模拟盘/实盘版本必须显式确认账户、模式和下单 API。
- 发布到迅投目录前，优先使用 `python scripts\publish_strategy.py <source.py> --name <target.py>` 做 dry-run，再加 `--execute` 真正发布。
