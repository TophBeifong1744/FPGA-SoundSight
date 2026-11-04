# S2 工程复现与报告导出

与 [2026-11-03 S2 报告](../reports/current/screen_s2_20261103/readme.md) 配套。工程工作路径使用短英文目录。Vivado 版本为 2025.2，器件 xc7z020clg400-2。

2026-11-03：P1 产品化软件不改硬件，继续使用本目录的 S2 配方和原样报告导出脚本。
更新包见 [P1 ZIP](../../board/artifacts/soundsight_screen_product_p1.zip)，安装和板测见[产品化说明](../../board/guides/screen-product.md)。

## 内容与来源

- `screen_s2/`：S2 工程配方、RTL、XDC、BD/IP、初始化数据及 `build.bat`。包含 49 项工程输入，配置清单见 `source-map.json`。
- `source-map.json`：工程输入与构建路径的对应表。
- `tools/export_bd_impl_reports.tcl`：在 Vivado GUI 中导出实现报告。
- `tools/rebuild_tool.tcl`：导出工程源码和配置。
- `tools/report-export-rules.md`：报告导出的操作说明。

S2 配方用于构建 PL 工程，P1 触屏和 CF1A 声纹程序通过板端运行包安装。

## 复现工程

将本目录复制到新的短 ASCII 路径，设置本机 `XILINX_VIVADO` 指向 Vivado 2025.2 根目录，或让 `vivado.bat` 可从 PATH 找到。进入 `screen_s2`：

```bat
build.bat
```

无参数只创建工程、BD 和 IP，不启动综合/实现。生成工程位于 `screen_s2/project/par/SoundSight_PS_3D.xpr`，随后可在 GUI 手动运行综合和实现。

如需命令行完整重建，在另一份尚无 `project/par` 的全新副本中运行：

```bat
build.bat route
```

此命令会运行综合、布线、审计并生成 bit/HWH/XSA，不下载到板卡。不能在已经执行无参数 `build.bat` 的同一副本上再次运行；旧输出受保护。仅综合使用 `build.bat synth`，同样要求新副本。重新实现后的数值应以新报告为准，不能沿用本次已保存实现的结果。

## 导出已有实现报告

在 Vivado GUI 打开准确工程，保存 BD，并确认目标实现已经布线且未过期。在 Tcl Console 执行（将占位路径换成你的本地路径）：

```tcl
source {交接目录/tools/export_bd_impl_reports.tcl}
```

默认使用当前 Implementation Run，输出到工程目录 `reports/export_年月日_时分秒/`，不覆盖旧结果。需要指定 run 或报告父目录，可在 source 前设置：

```tcl
set ::bd_impl_export_run impl_1
set ::bd_impl_export_dir {本机报告父目录}
```

脚本从已有实现导出报告。必须在 GUI 导出 PDF；batch 文本报告成功但缺 PDF 仍属于部分失败。五份文件齐全且 `export_info.txt` 中 `Export errors: 0` 才是完整导出，不等于设计签核通过。

## 从以后修改的工程重新交接源码

打开接收方实际修改后的工程，在 GUI Tcl Console 执行：

```tcl
source {交接目录/tools/rebuild_tool.tcl}
```

该工具保存 BD，并将工程配方、BD Tcl、已登记源码、约束及清单导出到 `handoff/latest`，同时备份已有输出。导出前应将外部源码加入工程；修改后的设计需重新运行综合、实现和相应功能测试。
