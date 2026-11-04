# 构建与验证

- `prepare_workspace.py`：按文件清单生成供构建和测试使用的工作目录。
- `handoff/screen_s2/`：Vivado 工程配置、源码和 `build.bat` 入口。
- `vivado/screen_s2/`：S2 配方及约束；`tools/`：工程准备、检查和报告导出工具。
- `reports/current/`：综合与实现报告；`reports/ps_3d/screen_s2/`：S2 配套检查结果。
- `package_runtime.py`：生成板端完整运行包；`check_runtime.py`：验证安装和包内资源。
- `release/`：技能包验证、打包与安装工具。

操作顺序见[根目录复现步骤](../README.md)，工程配置见[Vivado 构建说明](handoff/readme.md)，检查结果见[构建与软件检查](standalone-check.md)。
