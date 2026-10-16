# 无损传达 Skill 1.0.0：交付与验证记录

状态：**文件已创建，静态验证 PASS；实际宿主验证 NOT_RUN，整体验证 PARTIAL。**

## 交付范围

- 对外名称：无损传达 Skill。
- 安装标识：`lossless-intent`。
- 交付物：独立 Skill 文件夹与 ZIP 压缩包，共 10 个包内文件。
- 允许 Codex 按描述自动调用；不将允许自动调用等同于每次必定触发。
- 核心规则共 73 行，详细协议、案例、模板及测试按需加载。
- 没有安装到用户电脑，没有更改账号、全局规则、项目仓库或其他 Skill，没有提交、推送、部署或发布。

## 实际执行的检查

| 检查类型 | 结果 | 范围 |
|---|---|---|
| 包内静态检查 | PASS，29/29 项 | 文件、名称、引用、元数据子集、用例结构、关键规则文字、完整性 |
| 独立 YAML 解析 | PASS | 用当前环境 PyYAML 读取 SKILL.md 元数据和 agents/openai.yaml |
| Python 语法检查 | PASS | 校验脚本能够被解析 |
| 故意损坏副本的拒绝检查 | PASS，6/6 项 | 检查器正确拒绝缺文件、错误名称、关闭自动调用、断链、重复用例编号和伪报行为结果 |
| ZIP CRC 和路径检查 | PASS | 无重复成员、绝对路径或父目录跳转 |
| ZIP 字节对照与解压后重检 | PASS | 压缩包每个文件与源文件一致，解压后静态检查通过 |
| 实际模型行为用例 | NOT_RUN，24 个已准备 | 没有独立目标模型或宿主运行，不把理想答案当实际输出 |
| Codex／Claude Code 自动触发和安装 | NOT_RUN | 未在用户环境安装或验证 |
| 第三方完整兼容性 | NOT_RUN | 标准格式不等于所有宿主均兼容 |
| 效率和理解准确率 | NOT_RUN | 无受控对照，不提供改善百分比 |

## 检查方法及限制

先在缺少核心文件的构建目录运行检查器，实际返回失败；再创建完整文件后重新运行，返回通过。这个先失败再通过仅验证包结构与检查器，不是模型行为的红绿测试。

命令：

```text
python lossless-intent/tests/validate_skill.py
```

基础敏感模式检查只覆盖明显的密钥文本模式，不构成完整安全审计。文档关键词覆盖不证明模型遵守。独立 YAML 解析也不等于经过所有宿主的官方认证。

## 静态检查明细

| 检查 | 结果 |
|---|---|
| package directory | PASS |
| required files | PASS |
| no symlinks | PASS |
| no unexpected package files | PASS |
| UTF-8 without BOM | PASS |
| frontmatter delimiters | PASS |
| skill name and folder | PASS |
| description format and length | PASS |
| trigger description | PASS |
| metadata version | PASS |
| no tool preapproval | PASS |
| core under 500 lines | PASS |
| balanced fenced code blocks | PASS |
| Codex allows implicit invocation | PASS |
| display name and explicit invocation | PASS |
| local Markdown links | PASS |
| rule coverage: 自动启动及明确任务绕过 | PASS |
| rule coverage: 整体与局部 | PASS |
| rule coverage: 有范围的确认 | PASS |
| rule coverage: 非互斥选项 | PASS |
| rule coverage: 反馈分类 | PASS |
| rule coverage: 停止及回放 | PASS |
| rule coverage: 权限与隐私 | PASS |
| rule coverage: 能力及事实边界 | PASS |
| rule coverage: 交接及局部恢复 | PASS |
| behavioral case structure | PASS |
| behavioral status remains unclaimed | PASS |
| basic secret-pattern scan | PASS |
| SHA-256 manifest | PASS |

## 已确认需求的实现位置

| 已确认需求或经验 | 文件 |
|---|---|
| 名称、自动按需介入、明确任务直接处理 | SKILL.md、agents/openai.yaml |
| 整体小样、一个关键分歧、回放与交接 | SKILL.md |
| 非互斥选项、短回答余留歧义、许可边界 | references/protocol.md |
| 两组测试经验，不固化项目特定功能 | references/examples-and-lessons.md |
| 保留原话、范围、未定项与授权 | assets/consensus-template.md |
| 安装与实际触发检查 | README.md |
| 后续独立测试 | tests/acceptance-cases.json、tests/README.md |

## 安装包校验值

文件：`lossless-intent-v1.0.0.zip`  
大小：26197 字节  
SHA-256：

```text
b20f8bb7eef61ef57373b96e12ca7a5cbc0887127abf2c79885acfa1058e96ef
```

官方格式与安装资料核对日期：2026-10-16，来源列在包内 README。这个日期表示文档核对，不代表已在对应版本上完成运行验收。

唯一关键后续验证：在实际使用的 AI 工具里安装后，分别测试一次重要歧义自动介入、一次明确小修改直接完成，再按需要运行其余行为用例。
