# 软连接控制方案与开发工作流

## 核心原则

项目目录管版本，软连接管接入，迅投目录只做运行目标。

- `strategies\` 是策略源码和版本管理区。
- `links\` 是本机通往迅投安装目录的入口。
- `links\terminal-python-strategies` 指向迅投真实策略目录：`D:\迅投极速交易终端睿智融科版\python`。
- 迅投客户端实际运行的是真实策略目录中的文件，不是 `strategies\` 中的开发稿。

## 推荐分层

```text
strategies\
  current\        当前稳定快照
  dev\            日常开发版本
  release\        准备发布/比赛使用版本
  archive\        旧版本归档
```

`links\` 中的目录入口只对当前本机有效，不提交到远端仓库。

## 标准开发流程

1. 从稳定版本复制一个开发版本。

```powershell
New-Item -ItemType Directory -Force strategies\dev
Copy-Item strategies\current\STOCK_FACTOR_BASELINE.py strategies\dev\STOCK_FACTOR_DEV.py
```

2. 在 `strategies\dev` 中修改策略，不直接改迅投目录。

3. 做只读检查。

```powershell
python scripts\citics_quant_toolkit.py doctor
python scripts\citics_quant_toolkit.py strategy --path strategies\dev\STOCK_FACTOR_DEV.py
python scripts\citics_quant_toolkit.py xtdata --stock 000001.SZ --start 20260501 --end 20260508
```

4. 发布到迅投目录，先 dry-run。

```powershell
python scripts\publish_strategy.py strategies\dev\STOCK_FACTOR_DEV.py --name STOCK_FACTOR_BASELINE.py
```

5. 确认无误后执行发布。

```powershell
python scripts\publish_strategy.py strategies\dev\STOCK_FACTOR_DEV.py --name STOCK_FACTOR_BASELINE.py --execute
```

6. 在迅投客户端中重新打开或刷新策略，再跑回测。

## 发布安全规则

- 默认发布脚本只演练，不写入。
- 真正写入必须带 `--execute`。
- 覆盖迅投策略前会自动备份旧文件到 `strategies\archive\published_backups`。
- 发布前会检查源文件存在、语法可编译、目标目录来自 `links\terminal-python-strategies`。

## 读写边界

- 只读参考：`links\xuntou-root`
- 只读参考：`links\terminal-datadir`
- 只读参考：`links\terminal-logs`
- 只读参考：`links\xtquant-package`
- 发布写入：`links\terminal-python-strategies`

## 版本命名建议

```text
strategies\dev\stock_factor_dev.py
strategies\release\stock_factor_v20260510_riskfilter.py
results\20260510_riskfilter\
reports\20260510_riskfilter_notes.md
```

每次重要实验同时保存策略文件、回测参数、回测结果和结论。

## 回测与模拟盘隔离

- 回测版可以使用 `order_shares`、`C.get_history_data`、`C.get_financial_data`。
- 模拟盘/实盘版必须单独确认账户、交易模式、下单 API、撤单逻辑、仓位上限和异常处理。
- 不要直接拿回测脚本运行模拟盘或实盘。
