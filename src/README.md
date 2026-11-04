# 设计源码

- `rtl/`：四麦采集、定位特征计算、数据传输、PWM 与控制逻辑。
- `software/`：PS 驱动、C 求解器、三维处理、声纹推理和触屏程序。
- `interfaces/`：数据格式、寄存器及软硬件接口。
- `design/`：系统架构、计算与控制方案。
- `licenses/`：项目及第三方组件许可说明。

从[系统架构](design/main-architecture.md)了解模块划分，再按[复现步骤](../README.md)准备构建目录。声纹模型与 ARM 推理库位于 `software/ps/speaker_core/`。
