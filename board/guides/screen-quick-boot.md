# 屏幕快速启动

2026-11-03。本更新继承删除声纹档案、180度旋转、旧Pillow兼容和方向筛选修复。无需Vivado、新位流或系统镜像。

## 改了什么

旧开机路径每次执行完整prepare：重新编译两套C求解器、三维回归和旧版启动回归。屏幕服务现在调用 `soundsight-3d.sh prepare --quick`，只检查已安装原生库加载及ABI/几何格式，然后执行原硬件准备和状态检查，不编译、不跑整套回归。

HWH、安装文件、库可加载性、设备互斥、已有帧/故障、FCLK/复位、双轴/PCM能力、显示DMA及触摸准备仍按原逻辑执行。不会自动开轴、清故障、丢旧帧，也不删除bootpy依赖。Linux启动本身、PYNQ导入与显示初始化尚未优化。

完整 `soundsight-3d.sh check`（离线构建及三维测试）和不带quick的 `soundsight-3d.sh prepare`（完整准备）保留。原生C代码/库有变化后，须先停止服务并执行check；快速启动只检查加载/ABI，不能证明库与新C源码一致。缺库或不兼容会报QUICK_BOOT_LIBRARY_ERROR，先check修复，再启动服务，不静默跳过。

## 旧记录依据

原件 `document/evidence/report-measurements-20261103/p1-ui-01/product-check.zip` 的latest.json：BOOT=54.062秒，PREPARING=54.537秒，TOUCH_SETUP=126.543秒，PANEL_STARTING=134.536秒，首次READY=143.790秒。

即产品阶段约89.73秒，其中prepare约72.01秒（包含编译/自测和硬件准备，不能全算可省时间）。这是内核单调时钟，不包含上电至内核启动之前的U-Boot时间，也不是背光首次亮起的实测时刻。新版本速度待板端同条件冷启动对比，不提前声称节省多少秒。

## 安装与使用

按[板端安装说明](public-deployment.md)安装。以下命令在应用目录`/home/xilinx/FPGA_SoundSight`中执行。

## 冷启动测量和导出

在无运行任务时正常重启：`sudo reboot`，不要直接拔电。下次屏幕正常就绪后读取：

```sh
cd /home/xilinx/FPGA_SoundSight
python3 -c "import json; d=json.load(open('logs/product/latest.json')); print(json.dumps(d.get('startup_timing',{}),indent=2)); print(d.get('events',[])[:6])"
sudo sh soundsight-product.sh export
```

WinSCP取回 `logs/product-check.zip`。新增DISPLAY_LIT记录背光开启后时间；READY为触摸可用时间。`*_uptime_seconds`是Linux单调时钟值，`*_since_service_seconds`从product.py本轮BOOT起算，不包含之前服务依赖/解释器探测时间。后续START/STOP不覆盖首次亮屏/READY指标；整段系统开机耗时仍需外部计时或结合系统日志。

实际断电再上电的比较需先通过屏幕SHUT DOWN或系统正常关机再断电，按相同供电/SD卡/配置对比。未进行板端计时前，不标提速验收通过。
