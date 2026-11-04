# FPGA SoundSight

## 项目简介

SoundSight 是基于 Zynq-7020 的声音感知与双轴指向系统。系统采用边长 40 mm 的正四面体四麦阵列，计算声源的方位角和俯仰角，并通过水平、垂直舵机调整指向。RGB 触摸屏用于选择模式、管理声纹用户、调整参数和控制启停。

系统提供两种自动跟随模式：

- **SOUND：纯声音跟随。** 根据音量门限和方向筛选结果控制双轴转动。
- **SPEAKER：声纹跟随。** 在有效方向基础上增加目标用户声纹许可，评分超过门限后刷新许可有效期。

此外支持无动作测角、无声手动标定、声纹录入与删除、运行统计和故障记录。PL 完成四麦采集、特征与 PCM 数据传输、PWM 输出及保护；PS 在双核 Linux/PYNQ 中完成三维方向处理、声纹推理、参数管理和触屏交互。

## 仓库结构

| 目录 | 内容 |
|---|---|
| `src/` | RTL、PS 软件、声纹模型与推理库、架构和接口说明 |
| `sim/` | RTL 测试平台、软件回归测试 |
| `build/` | 构建脚本、Vivado 工程配置、综合与实现报告 |
| `board/` | bit/HWH/XSA、安装包、启动脚本与接线操作说明 |
| `data/` | 测试数据、运行日志、参考结果与整机照片 |
| `skill/` | FPGA 模块验证、PYNQ Overlay/DMA 验证两个技能包 |
| `report/` | 设计报告、大模型协作记录 |

[设计报告（PDF）](report/design-report.pdf) · [设计报告（Word）](report/design-report.docx) · [大模型协作记录](report/ai-collaboration.md) · [系统架构](src/design/main-architecture.md) · [实测结果](data/evidence/final-board-20261103/readme.md)

## 复现步骤

### 1. 准备环境与硬件

| 项目 | 配置 |
|---|---|
| FPGA | Zynq-7020，器件 `xc7z020clg400-2` |
| FPGA 工具 | Vivado 2025.2，配置 `PATH` 或 `XILINX_VIVADO` |
| 主机测试 | Python 3、NumPy、Pillow、GCC |
| 板端系统 | 与板卡匹配的 PYNQ 2.7 / ARMv7 Linux，Python 3.8、GCC |
| 外设 | 四麦正四面体阵列、RGB 触摸屏、水平和垂直舵机 |

开发板使用额定电源适配器，舵机独立供电并与开发板共地。当前 S2 配置的水平 PWM 为 **J3-2/M15**，垂直 PWM 为 **J3-3/J14**。接线和机械限位参照[板端说明](board/README.md)与[标定说明](board/guides/ps-manual-calibration.md)。

### 2. 准备构建目录并执行软件测试

在仓库根目录运行：

```text
python -B build/prepare_workspace.py --output build/workspace
```

脚本生成 `build/workspace`，其中的文件组织供构建和测试脚本使用。输出目录须为空。进入工作目录执行：

```text
cd build/workspace
python -B tools/check_current_software.py --output ../checks/software
python -B -m unittest discover -s software/tests -p test_public_enrollment.py
cd ../..
```

检查结果保存在 `build/checks/software`。确认测试通过后继续；再次运行时使用新的结果目录。

### 3. 重建 Vivado 工程

1. 将 `build/handoff/screen_s2` 复制到新的短英文工作路径，完整路径不超过 78 字节。
2. 在该目录运行 `build.bat`，生成工程、BD 和 IP。
3. 用 Vivado 打开生成的 `project/par/SoundSight_PS_3D.xpr`，检查 BD 和源文件。
4. 在 Vivado 中依次执行综合、实现和 Generate Bitstream，检查时序与资源结果。

[S2 工程说明](build/handoff/readme.md)给出配置和报告导出方法；[综合与实现报告](build/reports/current/readme.md)用于对照。板端安装包使用 `board/artifacts/screen_s2` 中配套的 bit/HWH，XSA 位于同一目录。

### 4. 安装板端程序

将 `board/artifacts/soundsight_pynq_3d_speaker.zip` 通过 WinSCP 或 SD 卡传到板端。以下命令以 `/boot` 为上传位置；执行前退出正在运行的采集程序和屏幕面板。

```sh
sudo python3 /boot/soundsight_pynq_3d_speaker.zip --destination /home/xilinx/FPGA_SoundSight
```

如安装输出 `reboot_required=true`，先重启。随后执行：

```sh
cd /home/xilinx/FPGA_SoundSight
sudo sh soundsight-3d.sh check
sudo sh soundsight-3d.sh prepare
sudo sh soundsight-3d.sh status
```

`check` 编译并检查板端软件；`prepare` 加载配套位流并设置时钟、复位和运行环境。成功后先进行无动作测角：

```sh
sudo sh soundsight-3d.sh follow-sound --axes off --frames 100
```

### 5. 调整参数并验证双轴

查看当前配置：

```sh
sudo sh soundsight-3d.sh level
sudo sh soundsight-3d.sh filter
sudo sh soundsight-3d.sh servo-config horizontal
sudo sh soundsight-3d.sh servo-config vertical
```

音量门限和窗口参数按现场结果调整，例如：

```sh
sudo sh soundsight-3d.sh level 12500
sudo sh soundsight-3d.sh filter 3 1
```

`filter 3 1` 表示每组 3 帧、至少 1 帧方向有效，仍需通过空间一致性筛选。按[手动标定步骤](board/guides/ps-manual-calibration.md)确认零位、转向和机械允许范围后，运行纯声音双轴跟随：

```sh
sudo sh soundsight-3d.sh follow-sound --axes both --frames 0
```

按 Ctrl+C 停止，摘要保存到应用目录的 `logs`。

### 6. 录入声纹并运行声纹跟随

首次使用先录入、选择目标用户，按 `RECORD_NOW` 提示连续讲话：

```sh
sudo sh soundsight-3d.sh speaker-enroll user1 --seconds 5
sudo sh soundsight-3d.sh speaker-select user1
sudo sh soundsight-3d.sh speaker-check
sudo sh soundsight-3d.sh speaker --axes off --seconds 30 --speaker-stats
```

分别观察本人和其他人的评分，再设置门限与许可时长。下面的 0.65、3 秒是配置格式示例，实际取值按测试结果确定：

```sh
sudo sh soundsight-3d.sh speaker-config 0.65 --ttl 3
sudo sh soundsight-3d.sh speaker --axes both --frames 0 --speaker-stats
```

过线评分从计算完成时刷新许可有效期；转动还需同时满足当前音量、有效方向和机械限位。未选择用户或未配置门限时，不授予声纹跟随许可。Ctrl+C 停止后，可查看本轮统计：

```sh
sudo sh soundsight-3d.sh speaker-stats
```

### 7. 启用触摸屏操作

退出命令行运行会话，将 `board/artifacts/soundsight_screen_product_p1.zip` 上传到板端 `/boot`，执行：

```sh
sudo python3 /boot/soundsight_screen_product_p1.zip --destination /home/xilinx/FPGA_SoundSight
```

按安装输出重启。HOME 页面选择 SOUND 或 SPEAKER、选择轴，再按 START；STOP 结束运行。USERS 页面用于录入、选择和确认删除用户，SETTINGS 页面调整参数。屏幕控制和终端采集择一使用，详细操作见[触屏说明](board/guides/screen-product.md)。

### 8. 查看结果与重新打包

运行摘要保存在板端应用目录的 `logs`，可通过 WinSCP 下载。软件统计、机械测量和声纹对照数据见 [data](data/README.md)，文件字段和日常命令见[运行说明](board/guides/pynq-final-runtime.md)。

在仓库根目录生成新的安装包：

```text
python -B build/package_runtime.py --output board/output/runtime-new.zip
```

技能包的验证、安装与使用见 [skill/README.md](skill/README.md)。项目与第三方许可证见 [src/licenses](src/licenses)。
