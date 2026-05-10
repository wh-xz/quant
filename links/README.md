# Links

这个目录是本项目通往迅投安装目录的本机入口。

Windows 当前没有给普通进程创建真正符号链接的权限，所以目录入口使用 Junction，文件入口使用 `.lnk` 快捷方式。它们不复制数据，也不复制迅投程序，只是指向真实位置。

## 当前入口

- `xuntou-root` -> `D:\迅投极速交易终端睿智融科版`
- `xuntou-bin` -> `D:\迅投极速交易终端睿智融科版\bin.x64`
- `terminal-python-strategies` -> `D:\迅投极速交易终端睿智融科版\python`
- `terminal-datadir` -> `D:\迅投极速交易终端睿智融科版\datadir`
- `terminal-logs` -> `D:\迅投极速交易终端睿智融科版\userdata\log`
- `factor-site-packages` -> `D:\迅投极速交易终端睿智融科版\bin.x64\因子版\Lib\site-packages`
- `xtquant-package` -> `D:\迅投极速交易终端睿智融科版\bin.x64\因子版\Lib\site-packages\xtquant`
- `terminal-exe.lnk` -> 迅投终端启动程序
- `factor-python.lnk` -> 因子版 Python
- `desktop-terminal-shortcut.lnk` -> 桌面原始快捷方式

## 使用建议

- 开发脚本可以通过 `links\terminal-datadir`、`links\terminal-logs` 读取数据和日志。
- 策略改动仍建议先在 `strategies\` 保存版本，再决定是否同步到 `links\terminal-python-strategies` 对应的真实终端目录。
- 不要把 `links\` 提交到仓库；这些入口只对当前这台电脑有效。
