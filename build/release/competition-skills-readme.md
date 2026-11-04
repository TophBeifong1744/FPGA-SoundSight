# FPGA / PYNQ 通用验证技能

离线检查使用 Python 标准库，XSim 示例还需要对应版本的 Vivado。

- skills/fpga-module-verification：接口/数值合同、自检TB、XSim runner、控制时序方法。
- skills/pynq-overlay-dma-validation：profile/golden检查、DMA模拟、连续运行方法、映射式会话审计。
- check_competition_skills.py：统一离线检查及可选XSim，不构建完整工程或操作硬件。
- evidence/history-20261018：原缺源失败及实际XSim/离线结果。
- evidence/current-20261104：本次离线复测及外部实测日志的只读审计。
- ai-corrections.md：调试案例与问题修正记录。
- source-map.json：技能文件与来源的对应表。

## 使用与安装

从解压根目录运行：

```text
python -B check_competition_skills.py --skills-root skills --output <new-results>
```

可选加 --vivado-bin "<vivado-bin>" 执行独立RTL示例。输出目录必须不存在。当前离线预期为模块7项、PYNQ74项方法/61子测试，正常接收96字节、双超时按预期失败且保留所有权，硬件保护入口拒绝执行。

安装到支持 Skills 的助手时，将各技能目录复制到助手技能目录，并将 `skill.md` 改为 `SKILL.md`。其他文件保持原名；验证记录供查阅。

离线模拟、XSim 仿真和已有板端日志审计分别记录。实际 DMA 验收需要按目标工程配置硬件适配器。
