---
name: grounded-dev-loop
description: >-
  Runs coding and debugging in long conversations as a grounded loop. A small
  working set limits edits only. A repro, failing test, or call chain named by
  the user or an attached skill is this turn's evidence; parking it in next is
  a misoperation. Investigate mode forbids product edits and still runs that
  red command. When diagnose is attached, finish its Phase 1 before stopping:
  a cited source sample is not a root cause. This holds when diagnose lives
  outside Cursor built-in skills. Re-fetch evidence instead of trusting chat
  memory, keep one mode, make the smallest change, verify at the real seam,
  and recheck neighbors. Use when implementing, fixing bugs, debugging,
  refactoring, making tests pass, continuing a long coding thread, recovering
  after context compaction, reviewing a root cause, or when a previous change
  caused new breakages. Triggers: 据实落地, 编码, 实现, 修 bug, debug,
  重构, 长对话, 工作集, 落地, 复现, 爆炸半径, 根因, diagnose.
---

# 据实落地

复杂对话里，编码和排障输给三件事：目标漂了、把聊天摘要当事实、一次改动碰到不该碰的面。据实落地用同一套循环把实现和 debug 做完，而不是写得更多。

定位问题的反馈环用 diagnose。diagnose 一旦挂上，本回合先完成它的 Phase 1：跑一条已经能变红、对得上用户症状的命令。这一步压过「读完引用行就停」。diagnose 不在 Cursor 自带 skill 目录里，只要本回合挂上了，同样算数。新行为的测试切片用 tdd。完成句前的新鲜证据用 verification-before-completion。据实落地管：**这一轮怎么读、怎么改、怎么证明、怎么停。**

细节与反例见 [reference.md](reference.md)。回合状态见 [ledger.example.json](ledger.example.json)。短例见 [examples.md](examples.md)。

## 每回合强制顺序

不要先写代码再找理由。压缩、长线程、用户改口之后，从第 1 步重走，不要接着上一轮助手的结论干。

1. **目标** — 用用户这一轮的话，一句话。不是你扩出来的史诗。已否决的路径列成约束，不再捡回来。
2. **模式** — 只选一个：`investigate` | `debug` | `implement` | `refactor`。模式决定写权，见下。
3. **工作集** — 点名本回合真正改的符号/文件，尽量 ≤ 7。工作集只限制写入。点不出工作集，就还在读，不准改产品代码。
4. **证据** — 本回合工具输出：复现命令、失败测试、当前行为、类型错误。聊天里的「上次已经证实」不算。没看见就重取。用户或已挂 skill 点名的复现、失败测试、调用链，本回合跑完、读完。读到被引用的源码行还不是根因。
5. **一步因果** — 最多 1–3 个步骤，只解释工作集里的这一刀。禁止顺手重构、禁止顺手修邻居、禁止扩 API「顺便完整」。步骤数只限制因果解释，不限制本回合要跑的证据。
6. **写入** — 只改工作集（外加你为验证新写的、最小的测试）。数据文件、生成物、锁文件、密钥、用户点名禁止的路径：没有明确授权就不动。
7. **缝上验证** — 跑用户会碰到的那条入口（失败测试、复现命令、相关页面/API），不要换一条更容易绿的。
8. **邻居** — 若这次改动碰了共享状态、公共类型、默认值、校验、路由、schema：跑最靠近的邻居。新红先撤回误伤，再决定是否另开症状。
9. **停或交** — 必做证据已经在手之后，完成 / 受阻 / 下一步只一件事。禁止用新范围掩饰没做完。必做复现还没跑，就不能停，也不能把它放进 `next`。

同一条回复里「先想一遍再当真执行」没有新收据，不构成第 4 步。

## 模式（写权）

| 模式 | 何时 | 写什么 | 验证 |
|---|---|---|---|
| `investigate` | 还没复现、工作集不明、缺权限 | **不写产品代码** | 本回合跑点名的红命令，再给出 `OBSERVED` 引用和墙 |
| `debug` | 有失败行为 | 只改因果链上的最小点 | 亲见过的失败必须消失；不发明缺失数据去喂校验器 |
| `implement` | 用户要新行为 | 只改交付该行为所需的工作集 | 新行为在真实入口可观察；不预留「以后可能要」 |
| `refactor` | 明确要求结构/可读且行为不变 | 行为不变的编辑 | 相关测试在改前能跑的，改后仍须过 |

一次写入只许一种模式。debug 时不要做 refactor。implement 时不要顺手改无关模块的风格。

用户说「修这个 / 实现这个」= 对**工作集**授权，不是对整个仓库授权。不要把 allowlist 理解成「没点名文件就永远不写代码」——那会把实现任务卡死。

## 停规则管写入

工作集、`investigate`、「下一步只一件」同时成立时，只收紧写入和收尾：

- 小工作集仍然限制这一刀改哪些文件。
- 证据另算。用户或已挂 skill 点名的复现、失败测试、调用链属于本回合证据。放进 `next` 是误操作。
- `investigate` 不写产品代码，同时跑红命令。已挂 skill 要求反馈环先变红时，引用行不能代替那条命令。
- 「下一步只一件」只在必做证据已经存在之后使用。
- diagnose 挂上时，Phase 1 压过抽样读源码之后停手。它是否 Cursor 自带 skill，不改变顺序。
- 本循环没有权力把已挂 skill 或用户点名的证据收窄成下一步。把跳过解释成自己的收窄，仍然是误操作。

聊天摘要仍不是事实。一次写入仍只许一种模式。修复仍不能扩成顺手重构。

## 证据怎么活过长对话

模型没有信念，只有 token。压缩会留下结论、丢掉命令输出。

- 只把 **join key** 带去下一轮：`path`、符号、测试名、错误码、SHA、HTTP、issue id。不带根因作文。
- 自己写过文件、用户改过口、或你不确定是否见过原文： **重跑/重读**。新收据作废旧摘要。
- 分类（需要时才写出来，implement 不必每步填表）：
  - `OBSERVED`：可引用的工具原文
  - `UNKNOWN`：动工还缺的；缺的是关键事实则停
  - `BLOCKED`：环境墙；停，不编
  - `HYPOTHESIS`：假说；**不得**当事实去改代码
- 错误文案、类型报错、缺失字段 = 诊断输入，不是「去把空填满」的工单。空/缺/歧义常常是合法状态。

## 验证完整性（实现和 debug 都适用）

绿必须来自**行为**，不是来自改裁判：

- 不要只改 fixture/expected、改测试名、放宽断言、吞异常、抬超时/限额，来换这一刀的绿
- expected 不从你刚写的生产实现抄回来
- `calls > 0`、日志里有关键词、编译过、UI 可点，都不是字段级/行为级证据
- 验证走公开入口或用户指定路径，不走你为本次新写的、只会绿的 helper
- 同一失败信号上已经两次落空：停止加补丁。先画最短地形图（数据从哪进、谁说了算、旁路、谁会读到新值），再第三次动手

合同/不变量修复（测试在锁行为，而不是锁实现）时：拿掉这次修复，原失败应回来。只绿不红，说明你改了裁判或没打到那条路径。日常 UI 文案不必做 mutant。

## 每轮最少交代

```text
goal: <用户这一轮的一句话>
mode: investigate|debug|implement|refactor
working-set: <文件或符号>
evidence: <本回合命令/测试，关键输出>
changed: <实际写过的>
verified: <同一条缝的结果>
neighbors: <跑过 / 为何不用跑>
unshipped: <没做的，或无>
next: <必做证据已在手之后，零或一件>
```

## 编码（改本 skill 时）

本目录文本必须是 **UTF-8 with BOM**。显示名是正文标题里的四个汉字，禁止拆开用系统 ANSI/GBK 另存或 `>>` 追加。

改完后整文件按 UTF-8 读、按 UTF-8-BOM 写，然后执行：

```text
python scripts/assert-utf8.py
```

断言失败就不要提交、不要继续往文件里塞中文。PowerShell 只用 `Get-Content -Encoding UTF8` / `Set-Content -Encoding utf8BOM`（Windows PowerShell 5 的默认 `Set-Content -Encoding utf8` 才带 BOM；跨版本时以脚本为准）。
