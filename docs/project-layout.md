# 项目目录说明

## 源码与策略

- `scripts\citics_quant_toolkit.py`：统一检查入口。
- `scripts\通用板块下载.py`：原始板块下载脚本，已从根目录归档到脚本目录。
- `strategies\current\STOCK_FACTOR_BASELINE.py`：当前终端主策略的项目内快照。

## 研究与结果

- `notebooks\citics_quant_factor_research.ipynb`：因子研究入口。
- `results\`：保存回测结果、参数记录、指标表、截图和日志摘要。
- `reports\`：保存比赛报告、策略说明、提交材料和复盘文档。

## 数据

- `data\exports\`：从迅投或 notebook 导出的样本数据。
- `data\external\`：赛方给的外部文件、手工下载的数据包。
- `data\processed\`：研究过程生成的中间数据。

真实行情和财务数据不复制进项目目录，主缓存仍在 `D:\迅投极速交易终端睿智融科版\datadir`。

## 文档与资料

- `docs\manuals\操作文档.pdf`：操作文档。
- `docs\manuals\股衍使用手册\`：迅投研量化交易终端手册和 `.rzrk` 策略案例。
- `vendor\xtquant.rar`：离线包/安装资料。
- `private\`：远程服务器、账号等敏感资料。
- `tmp\`：临时图片和一次性排查文件。
- `links\`：本机 Junction/快捷方式入口，指向迅投真实安装目录、数据目录、日志目录和 XtQuant 包。
