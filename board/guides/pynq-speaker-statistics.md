# 可选的整轮声纹统计

本次只更新PS程序，不改RTL、BD、位流、声纹门限、TTL或跟随规则。

## 开启与查询

默认不累计。每次需要统计时，在原speaker命令后加`--speaker-stats`：

```sh
sudo sh soundsight-3d.sh speaker --axes both --seconds 30 --speaker-stats
```

持续运行直到Ctrl+C：

```sh
sudo sh soundsight-3d.sh speaker --axes both --seconds 0 --speaker-stats
```

只测试评分不驱动舵机，把`--axes both`改为`--axes off`。不加`--speaker-stats`即关闭，这个开关不持久保存到配置。

运行结束并出现`SPEAKER_3D_STOPPED`后，查看上一次已保存运行：

```sh
sudo sh soundsight-3d.sh speaker-stats
```

这条命令只读本地文件，不需要PYNQ、prepare或板卡访问。会显示原日志位置、目标人、会话结果、门限以及：

| 字段 | 含义 |
| --- | --- |
| SUCCESSFUL | 整轮成功算出有限、合法声纹分数的次数 |
| PASSED | 上述分数大于或等于本轮声纹门限的次数 |
| AVG_SECONDS | 所有成功计算的平均耗时，包含过线和未过线结果 |
| MAX_SECONDS | 所有成功计算的最大耗时 |

统计从声纹计算线程直接累计，不从最近32条记录或合并后的IPC事件反推。语音不足、无分数、推理异常不计入次数和平均值的分母。没有成功计算时平均/最大显示N/A；未配置声纹门限时通过次数显示N/A。

成功计算指得到了分数，不等于当前可以转动。整轮包含正常停止时正在完成的本轮尾部计算；它们可能在硬件已STOP后结束。过线次数不等于转动次数、实际许可刷新次数，也不是识别准确率。真实故障会话仍标FAIL；已收到的成功计算统计保留，收不到子进程汇总时明确显示UNAVAILABLE，不伪装成零次。

## 保存与开销

- 只有显式开启时，计算线程在每次结果完成后更新固定数量的计数、耗时变量。无新增线程、逐帧文件、模型调用或运行中SD写盘。
- 耗时沿用原`compute_seconds`：本次任务开始至结果计算完成，不包含此前等待排队、录音时长或SD写盘时间。
- 原`logs/speaker-3d-*.json`在结束后保存整轮统计，字段为`speaker_worker.statistics`。
- `logs/speaker-last-stats.json`是单个最后运行摘要，在结束后原子替换。系统时间回退也不会选错日志；每轮关闭统计时也会将它标为DISABLED，避免把上一轮开启时的旧数字误当成本轮结果。
- 读取统计不重跑识别。突然断电或进程被强杀仍可能无法保存当前轮，不能当作已有完整结果。原每轮日志的保留/清理规则不变。

## 安装与查询

完整公共包已包含统计功能，按[板端安装说明](public-deployment.md)安装。运行命令增加`--speaker-stats`，结束后执行`sudo sh soundsight-3d.sh speaker-stats`。没有已保存会话时显示NO_SAVED_SESSION。
