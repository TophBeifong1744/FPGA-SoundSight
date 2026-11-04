# 只测角度、手动标定与自动跟随

先按[安装说明](public-deployment.md)准备。当前S2信号为水平J3-2/M15、垂直J3-3/J14；舵机独立供电并与控制板共地。

## 查看并配置

在安装目录中执行；示例机械范围须按实际机构调整：

```sh
cd /home/xilinx/FPGA_SoundSight
sudo sh soundsight-3d.sh status
sudo sh soundsight-3d.sh level
sudo sh soundsight-3d.sh filter
sudo sh soundsight-3d.sh servo-config horizontal
sudo sh soundsight-3d.sh servo-config vertical
sudo sh soundsight-3d.sh level 12500
sudo sh soundsight-3d.sh filter 3 1
sudo sh soundsight-3d.sh servo-config horizontal 180 1 170 190
sudo sh soundsight-3d.sh servo-config vertical 110 1 105 115
```

`servo-config`四项依次为前方/零位角、正反方向、允许最小角、允许最大角。配置保存后用于下一次会话。

## 先测角度与手动标定

```sh
sudo sh soundsight-3d.sh follow-sound --axes off --frames 100
sudo sh soundsight-3d.sh manual --horizontal 180 --seconds 3
sudo sh soundsight-3d.sh manual --vertical 110 --seconds 3
```

手动命令不要求声音和声纹；仍遵守范围、超时和停止保护。机械映射、安装方向及可达范围校准后再启用跟随。

## 自动跟随与停止

```sh
sudo sh soundsight-3d.sh follow-sound --axes both --frames 0
sudo sh soundsight-3d.sh speaker --axes both --frames 0 --speaker-stats
```

两条命令择一运行。前者只按声音方向；后者还要求已录入并选择目标、配置评分门限且许可有效。Ctrl+C停止并保存摘要；切换模式前先结束当前会话。屏幕服务运行时从面板控制，不同时启动命令行采集。

三维滤波与声纹详细操作见[完整运行说明](pynq-final-runtime.md)。
