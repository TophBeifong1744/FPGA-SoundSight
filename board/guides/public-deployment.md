# 板端安装与声纹录入

板卡使用已有匹配的 PYNQ 2.7 / ARMv7 系统；舵机使用独立电源并与控制板共地。

## 安装

把 `board/artifacts/soundsight_pynq_3d_speaker.zip` 上传到板端 `/boot` 或其他可读位置。退出采集与屏幕服务后，执行：

```sh
sudo python3 /boot/soundsight_pynq_3d_speaker.zip --destination /home/xilinx/FPGA_SoundSight
```

首次安装使用新的应用目录，用户档案在录入后建立。安装器保护已有配置与日志；位流由后续 `prepare` 命令加载。如输出要求重启，先重启，再执行：

```sh
cd /home/xilinx/FPGA_SoundSight
sudo sh soundsight-3d.sh check
sudo sh soundsight-3d.sh prepare
sudo sh soundsight-3d.sh status
sudo sh soundsight-3d.sh speaker-list
```

新安装的用户列表为空。先录入本人：

```sh
sudo sh soundsight-3d.sh speaker-enroll user1 --seconds 5
sudo sh soundsight-3d.sh speaker-select user1
sudo sh soundsight-3d.sh speaker-check
sudo sh soundsight-3d.sh speaker --axes off --seconds 30 --speaker-stats
```

录入时按 RECORD_NOW 提示讲话，舵机保持关闭；语音不足则保留失败结果并重新录入。先观察本人和非本人分数，再设定门限；以下只是参数格式示例：

```sh
sudo sh soundsight-3d.sh speaker-config 0.65 --ttl 3
sudo sh soundsight-3d.sh level 12500
sudo sh soundsight-3d.sh filter 3 1
```

机械零位、方向和允许范围按实际机构标定，参照[操作说明](pynq-final-runtime.md)。确认后，纯声源与声纹跟随分别为：

```sh
sudo sh soundsight-3d.sh follow-sound --axes both --frames 0
sudo sh soundsight-3d.sh speaker --axes both --frames 0 --speaker-stats
```

两条运行命令择一执行，Ctrl+C停止。未选择目标或未配置评分门限时，声纹模式不会授予跟随许可。

## 触屏服务

完成上述安装、prepare并退出所有运行会话后，将 `board/artifacts/soundsight_screen_product_p1.zip` 上传到 `/boot`，执行：

```sh
sudo python3 /boot/soundsight_screen_product_p1.zip --destination /home/xilinx/FPGA_SoundSight
```

按安装输出完成重启，屏幕 USERS 页面可录入、选择与删除用户。新用户、门限、机械标定和日志存放在安装目录中，后续升级保留。

## 公共资源

公共资源位于 `src/software/ps/speaker_core`，包括 CP1/VF1、基准 ONNX 模型、前端参数、ARM 后端和 ONNX Runtime 动态库。对应许可证保留在同目录 `licenses`。
