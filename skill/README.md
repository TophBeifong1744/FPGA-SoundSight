# 通用验证技能

- **fpga-module-verification**：RTL 接口与数值合同、自检测试平台、XSim 和握手控制排障。
- **pynq-overlay-dma-validation**：Overlay 元数据、DMA 所有权、故障模拟与会话日志审计。

从[技能总览](package-overview.md)和各技能的 `skill.md` 开始。使用方法和安装命令见[验证与安装说明](delivery.md)。

在仓库根目录执行离线验证：

```text
python -B build/release/check_competition_skills.py --skills-root skill --output build/checks/skills
```

已保存的离线结果包括 7 项模块测试及 74 项 PYNQ 方法测试（61 个子测试），详见[验证记录](../data/evidence/competition-skills-20261104/readme.md)。XSim 结果和离线结果分别记录。
