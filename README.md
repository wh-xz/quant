# 中信量化大赛工作台

这个目录是本机参赛开发区，服务于迅投极速交易终端睿智融科版、XtQuant 数据检查、策略版本管理、回测结果归档和比赛报告整理。

## 快速入口

```powershell
cd D:\wh_xz\quant
python scripts\citics_quant_toolkit.py doctor
```

常用只读检查：

```powershell
python scripts\citics_quant_toolkit.py env
python scripts\citics_quant_toolkit.py strategy
python scripts\citics_quant_toolkit.py logs --pattern error
python scripts\citics_quant_toolkit.py xtdata --stock 000001.SZ --start 20240501 --end 20240510
```

这些命令只做环境、日志、数据和策略文件检查，不会下单。

## 当前核心路径

- 本机终端：`D:\迅投极速交易终端睿智融科版`
- 终端可执行文件：`D:\迅投极速交易终端睿智融科版\bin.x64\XtItClient.exe`
- 终端内置策略目录：`D:\迅投极速交易终端睿智融科版\python`
- 当前主策略源文件：`D:\迅投极速交易终端睿智融科版\python\STOCK_FACTOR_BASELINE.py`
- 本项目策略快照：`strategies\current\STOCK_FACTOR_BASELINE.py`
- 迅投数据缓存：`D:\迅投极速交易终端睿智融科版\datadir`
- 迅投日志目录：`D:\迅投极速交易终端睿智融科版\userdata\log`
- 本机软连接入口：`links\`

## 目录结构

- `scripts/`：项目工具、数据下载脚本、环境检查入口。
- `strategies/`：策略快照、候选版本、模拟盘/实盘版本草稿。
- `notebooks/`：因子研究、参数实验、收益和回撤分析。
- `data/`：导出的样本数据、中间数据和数据说明；真实行情主缓存仍在迅投 `datadir`。
- `results/`：回测结果、调参记录、指标表和对比实验。
- `reports/`：比赛报告、策略说明、提交材料。
- `docs/`：部署清单、环境说明、官方手册和操作流程。
- `tests/`：项目工具测试。
- `vendor/`：安装包或第三方离线包。
- `private/`：账号、远程服务器等敏感资料，不要提交或外发。
- `tmp/`：临时截图、渲染图、一次性排查文件。
- `links/`：指向迅投安装目录、数据、日志和 XtQuant 包的本机入口。

## 推荐比赛流程

1. 用 `doctor` 确认本机环境和依赖。
2. 用 `xtdata` 抽检行情、板块、财务数据能否读到。
3. 在 `strategies/current` 固化当前可运行版本，每次重大改动另存新版本。
4. 在迅投终端做回测，结果截图、指标表和日志放进 `results/`。
5. 用 notebook 做因子研究、参数对比和收益归因。
6. 稳定后再单独创建模拟盘版本，显式确认账户、交易模式和下单 API。
7. 把最终策略逻辑、风控、数据口径和回测结论整理到 `reports/`。

## 重要文档

- `docs\data-status.md`：已下载数据、验证结果和后续补数清单。
- `docs\competition-rules.md`：比赛规则确认清单和 Codex 约束。
- `docs\environment-map.md`：本机、远程服务器、迅投终端和 Codex 的分工。
- `docs\deployment-checklist.md`：赛前/回测/模拟盘检查清单。
- `docs\workflow.md`：结合软连接的策略开发、检查和发布流程。
- `docs\manuals\`：迅投官方操作文档和策略案例。
- `links\README.md`：软连接/Junction 入口说明。
