# AF1：无声纹三维跟随

> A收件补充（2026-10-29）：B已完成板端安装、原21项与新7项离线测试；未完成实际跟随。垂直手动命令接受但未观察到动作，先按接管说明（历史引用：`total-handoff-20261029.md`）定位。以下安装器仅适用于B所列原始基线，已装AF1无需重装；不用于覆盖后续A侧保护修复。

仅新增显式`follow-sound`入口，复用现有三维快照、空间筛选及双轴控制。
不启动声纹或PCM DMA进程；不区分说话人，任何满足方向/音量条件的声源均可能被跟随。
默认仍为axes off。机械配置缺失或不合法时拒绝开轴；STOP、失效撤销、限位及硬件租约保持原实现。

| 入口 | 行为 |
|---|---|
| `run` | 只测角，轴关闭 |
| `run --axes both` / `speaker --axes both` | 保持原声纹门控 |
| `follow-sound` | 无声纹测角，轴默认关闭 |
| `follow-sound --axes both` | 显式无声纹双轴跟随 |
| `manual` | 保持原手动标定功能 |

## 安装与使用

按[板端安装说明](public-deployment.md)安装。以下命令在应用目录`/home/xilinx/FPGA_SoundSight`中执行。

## 运行

先用无动作短测核对方向、通道和门限：

```sh
sudo env PYTHONUNBUFFERED=1 sh soundsight-3d.sh follow-sound --axes off --frames 100 --debug
```

确认两轴零位、方向、实测机械限位和阵列方向后，才执行：

```sh
sudo env PYTHONUNBUFFERED=1 sh soundsight-3d.sh follow-sound --axes both --frames 300
```

300是定位帧数，不是秒。省略frames为持续运行，Ctrl+C停止。
输出`FOLLOW_SOUND=AF1 SPEAKER=DISABLED IDENTITY_GATE=OFF`说明选中了新入口。
停止后查看`THREE_D_STOPPED SUMMARY=... ERROR=...`并保留JSON。
`speaker-config --disable`不是无声纹开关，它仍只会禁止声纹许可。
旧文档的`run --axes`示例在接合版仍指向声纹，纯声学测试使用本页新命令。

## 安装备份

当前完整包安装器在目标目录保留本次替换的备份。恢复前先停止业务并核对对应备份清单。

## 验证边界

PC路由/客户端和原三维软件模型回归通过；后续B交接记录已确认板端安装、两份C库构建及21+7项离线测试通过。尚无真实AF1采集或机械跟随实测。
本更新不提供未经实测的零位/限位示例。原声纹进度保持。
