# 中信量化大赛部署清单

## 本机已就绪

- 迅投终端：`D:\迅投极速交易终端睿智融科版`
- 当前策略：`D:\迅投极速交易终端睿智融科版\python\STOCK_FACTOR_BASELINE.py`
- 因子版 Python：`D:\迅投极速交易终端睿智融科版\bin.x64\因子版\python.exe`
- 数据缓存：`D:\迅投极速交易终端睿智融科版\datadir`
- 日志目录：`D:\迅投极速交易终端睿智融科版\userdata\log`
- 本项目：`D:\wh_xz\quant`

## 常用检查命令

```powershell
cd D:\wh_xz\quant
python scripts\citics_quant_toolkit.py doctor
python scripts\citics_quant_toolkit.py env
python scripts\citics_quant_toolkit.py strategy
python scripts\citics_quant_toolkit.py logs --pattern error
python scripts\citics_quant_toolkit.py xtdata --stock 000001.SZ --start 20240501 --end 20240510
python -m pytest tests
```

## 回测前

- 迅投终端已打开并登录。
- `doctor` 检查通过，至少确认终端目录、策略文件、日志目录、因子版 Python 存在。
- `xtdata` 抽检能读到日线数据。
- 当前策略版本已复制或记录到 `strategies\`。
- 回测参数、股票池、基准、手续费、滑点和调仓频率已记录。

## 回测后

- 保存收益曲线、回撤、年化、夏普、胜率、换手、持仓数量等结果到 `results\`。
- 保存关键日志摘要，尤其是选股数量、过滤数量、异常股票和下单记录。
- 在 `reports\` 记录本轮策略改动、参数、结论和下一步。

## 模拟盘前

- 单独创建模拟盘策略文件，不直接拿回测脚本冒然运行。
- 确认账户、交易模式、下单函数、撤单逻辑、单票上限、总仓位上限。
- 先小规模运行并观察日志，再扩大范围。

## 安全边界

- 当前工具命令均为只读检查，不会下单。
- 不把 `private\`、`config.json`、临时文件或大数据缓存提交/外发。
- 远程服务器需要独立验证终端、数据、策略和账号状态。
