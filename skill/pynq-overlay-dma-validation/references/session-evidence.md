# 映射式会话审计

audit_session.py只读JSON，不连接设备。任何项目通过合同字段路径映射为统一语义，路径是对象键数组，不执行表达式。

schema_version=1：
- success：结束状态路径和允许值。
- zero：本轮必须为0的故障/错误累计。
- empty：必须null或空列表的错误/清理字段。
- true：必须严格true的停止确认。
- counters：本轮起止计数求差，下降即FAIL，不猜回绕/复位。
- duration：有限正秒数。
- tail：只有明确允许的停止原因下才允许最终状态掩码；zero仍必须为0。
- recent_results：只报告近期列表条数，不推断整轮统计。
- statistics：可选整轮累计路径，enabled=true时审核。

[example-audit.json](example-audit.json)为通用字段示例，不是产品运行默认值。缺字段、错类型、NaN/Infinity、未知schema均失败；未知不能补0。

统计字段：enabled、successful_calculations、threshold_passes、total_compute_seconds、average_compute_seconds、max_compute_seconds。count=0时均值/最大值必须null；threshold_passes可null（未设门限）。

PASS只表示映射字段的一致性成立，不证明日志来源、物理到位、未记录的包连续性、算法准确率或周期级时延。
