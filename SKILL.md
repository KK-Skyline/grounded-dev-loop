---
name: grounded-dev-loop
description: >-
  Runs coding and debugging in long conversations as a state machine. The model
  fills the ledger and judges the current state; scripts/next-state.py selects
  the next state from ordered guards. A small working set limits edits only. A
  repro, failing test, or call chain named by the user or an attached skill is
  this turn's evidence; parking it in next is a misoperation. Investigate mode
  forbids product edits and still runs that red command. When diagnose is
  attached, finish its Phase 1 before stopping: a cited source sample is not a
  root cause. This holds when diagnose lives outside Cursor built-in skills.
  Re-fetch evidence instead of trusting chat memory, keep one mode, make the
  smallest change, verify at the real seam, and recheck neighbors. Use when
  implementing, fixing bugs, debugging, refactoring, making tests pass,
  continuing a long coding thread, recovering after context compaction,
  reviewing a root cause, or when a previous change caused new breakages.
  Triggers: 据实落地, 编码, 实现, 修 bug, debug, 重构, 长对话, 工作集, 落地,
  复现, 爆炸半径, 根因, diagnose.
---

# 据实落地

这一轮按扩展状态机执行。当前状态里的说明负责判断和生成。下一状态由 `python scripts/next-state.py` 根据账本变量选出：守卫按书写顺序，第一条成立的生效，无条件边在最后。模型不从全文里再推断该做什么。

细节与反例见 [reference.md](reference.md)。账本字段见 [ledger.example.json](ledger.example.json)。短例见 [examples.md](examples.md)。守卫以脚本为准；下面的表只是可读副本。改表不改脚本，控制流没有变。

定位问题的反馈环用 diagnose。diagnose 一旦挂上，在 `evidence_ran` 成为真之前不能进入写入、验证或任何终端。diagnose 不在 Cursor 自带 skill 目录里，同样算数。新行为的测试切片用 tdd。完成句前的新鲜证据用 verification-before-completion。

## 变量

先完成当前状态的操作，把结果写进账本，再把账本从标准输入交给脚本。脚本打印的整份账本替换旧账本。计数器只由脚本增加。

| 变量 | 谁写 | 含义 |
|---|---|---|
| `q` | 脚本 | 当前状态 |
| `mode` | bind | `investigate` `debug` `implement` `refactor` 之一 |
| `working_set` | bind | 本回合可写的符号或文件，尽量 ≤ 7。只限制写入 |
| `diagnose_attached` | bind | 本回合是否挂了 diagnose |
| `evidence_command` | select_evidence | 用户或已挂 skill 点名的复现、失败测试、调用链；否则是用户会碰到的那条入口 |
| `evidence_ran` | run_evidence | 该命令已在本回合跑完，输出在手里 |
| `wrote` | write | 工作集已写入 |
| `seam_ran` | verify_seam | 写入之后又跑了同一条入口。从 write 进入验证时脚本会把它清掉 |
| `verdict` | judge_verdict | `behavior_pass` `proxy_green` `still_red` `judge_changed` 之一 |
| `shared_touched` | write | 改动碰了共享状态、公共类型、默认值、校验、路由、schema |
| `neighbors_ran` | neighbors | 最近的邻居命令已跑 |
| `rework_count` `proxy_count` `terrain_done` | 脚本或 map_terrain | 同一信号的返工、代理绿打回、地形图是否画完 |

聊天摘要、上一轮助手的结论、没看见输出的「上次已证实」，都不能写成 `evidence_ran: true`。同一条回复里先想一遍再当真执行，没有新收据，不算跑过。

## 状态

### bind

写本回合目标：用户这一轮的一句话，不是扩出来的史诗。已否决的路径写入约束，不再捡回来。只选一个模式。点名工作集；点不出工作集就保持为空，后面不能写产品代码。用户说「修这个 / 实现这个」是对工作集授权，不是对整个仓库授权。空工作集只表示还没点名可写对象，不表示用户没授权的数据、密钥、生成物可以写。

只把 join key 留在账本里：`path`、符号、测试名、错误码、SHA、HTTP、issue id。不写根因作文。

边：无条件 → `select_evidence`。

### select_evidence

点名的复现、失败测试、调用链就是 `evidence_command`。读到被引用的源码行还不是根因，不能拿它代替这条命令。没有点名时，命令是用户会碰到的入口，不是一条更容易绿的替代。

边：命令为空 → `end_blocked`；否则 → `run_evidence`。

### run_evidence

跑 `evidence_command`。把关键输出留在账本能指回的地方。没跑完就停在这里，不能把命令放进 `next`。

边：没跑完 → `end_blocked`；跑完 → `gate_write`。

### gate_write

| 模式 | 何时 | 写什么 | 验证 |
|---|---|---|---|
| `investigate` | 还没复现、工作集不明、缺权限 | 不写产品代码 | 红命令已经跑过，再交 `OBSERVED` 和墙 |
| `debug` | 有失败行为 | 只改因果链上的最小点 | 亲见过的失败必须消失 |
| `implement` | 用户要新行为 | 只改交付该行为所需的工作集 | 新行为在真实入口可观察 |
| `refactor` | 明确要求结构或可读，且行为不变 | 行为不变的编辑 | 改前能过的相关测试，改后仍过 |

一次写入只许一种模式。`debug` 不夹重构。`implement` 不改无关模块的风格。`investigate` 跑完证据后进入 `end_reported`，不进入 `write`。

边：模式不在四种里，或 debug/implement/refactor 没有工作集 → `end_blocked`；`investigate` → `end_reported`；否则 → `write`。

### write

只改工作集，外加为验证新写的最小测试。数据文件、生成物、锁文件、密钥、用户点名禁止的路径，没有明确授权不动。一步因果最多 1–3 步，只解释这一刀。不顺手重构，不顺手修邻居，不扩 API。

错误文案、类型报错、缺失字段是诊断输入。空、缺、歧义可以是合法状态，不要为了填满去发明数据。

边：还没写入 → `end_blocked`；写入后脚本清掉 `seam_ran` → `verify_seam`。

### verify_seam

再跑写入前那一条 `evidence_command`。不换一条更容易绿的命令，不改用只会绿的 helper。

边：写入后没再跑 → `end_blocked`；跑了 → `judge_verdict`。

### judge_verdict

只输出封闭标签里的一个，写进 `verdict`。标签对不对仍是这一状态的判断；脚本只按标签转移。

- `behavior_pass`：用户会碰到的那条入口上，该行为出现或该失败消失。改前能过的相关测试仍过。
- `proxy_green`：绿来自参数、文件快照、调用次数、日志单词、编译通过、界面可点，或本回合新写的 helper。这些不是入口行为。
- `still_red`：同一条入口仍是原来的失败。
- `judge_changed`：为了变绿改了 expected、测试名、断言、超时或限额，吞了异常，或删掉、收窄了原本会守住行为的回归。合同修复若拿掉生产改动不再变红，也是这个标签。

日常 UI 文案不必做 mutant。不发明缺失数据去喂校验器。expected 不从刚写的生产实现抄回来。

边，按此顺序：

1. 标签不在封闭集 → `end_blocked`
2. `judge_changed` → `end_unverified`
3. 第一次 `proxy_green` → 清掉 `seam_ran`，回到 `verify_seam`
4. 再次 `proxy_green` → `end_unverified`
5. `still_red` 且已经两次回到写入、地形图还没画 → `map_terrain`
6. `still_red` 且返工已到上限 → `end_unverified`
7. 其余 `still_red` → 回到 `write`
8. `behavior_pass` 且碰了共享面、邻居还没跑 → `neighbors`
9. `behavior_pass` → `end_verified`

### neighbors

跑最靠近的邻居。新红先撤回误伤，再决定是否另开症状。邻居通过不能把非 `behavior_pass` 抬成 verified。

边：没跑 → `end_blocked`；跑完且标签仍是 `behavior_pass` → `end_verified`。

### map_terrain

同一失败信号两次落空之后停手补丁。画出数据从哪进、谁说了算、旁路、谁会读到新值。`terrain_done` 只在这张图写完后置真。第三刀必须打在图上的一个节点。

边：图没画完 → `end_blocked`；画完 → `write`。

## 终端

| 状态 | kind | 可以声称 |
|---|---|---|
| `end_verified` | verified | 同一条缝上的行为通过，邻居该跑的已经跑过 |
| `end_reported` | reported | investigate 已跑完点名命令，没有改产品代码 |
| `end_unverified` | unverified | 不能说修好了、全绿了、入口已经证明 |
| `end_blocked` | blocked | 缺命令、缺工作集、没跑完，或环境墙。停下，不编 |

脚本若收到模型自己跳到 `end_verified`，但标签不是 `behavior_pass`，或共享面邻居还没跑，会改去 `end_unverified` 或 `neighbors`。diagnose 还没跑完证据时，后继状态和终端都会被拉回 `run_evidence` 或 `select_evidence`。

停规则只在必做证据已经在手之后使用。工作集、investigate、「下一步只一件」都不能把点名的复现收窄成下一步。本循环不能把已挂 skill 或用户点名的证据放进 `next`。

## 交卷

```text
goal: <用户这一轮的一句话>
q: <脚本打印的 q>
kind: <verified|reported|unverified|blocked 或空>
mode: investigate|debug|implement|refactor
working-set: <文件或符号>
evidence: <本回合命令/测试，关键输出>
changed: <实际写过的>
verified: <同一条缝的结果>
neighbors: <跑过 / 为何不用跑>
unshipped: <没做的，或无>
next: <终端之后零或一件；证据未跑完时必须为空>
```

需要区分证据等级时再写：`OBSERVED` 是可引用的工具原文；`UNKNOWN` 缺关键事实则停；`BLOCKED` 是环境墙；`HYPOTHESIS` 不得当事实去改代码。implement 不必每步填这张分类表。

## 编码（改本 skill 时）

本目录文本必须是 **UTF-8 with BOM**。显示名是正文标题里的四个汉字，禁止拆开用系统 ANSI/GBK 另存或 `>>` 追加。

改完后整文件按 UTF-8 读、按 UTF-8-BOM 写，然后执行：

```text
python scripts/assert-utf8.py
python scripts/next-state.py --self-check
```

断言失败就不要提交、不要继续往文件里塞中文。PowerShell 只用 `Get-Content -Encoding UTF8` / `Set-Content -Encoding utf8BOM`（Windows PowerShell 5 的默认 `Set-Content -Encoding utf8` 才带 BOM；跨版本时以脚本为准）。

改控制流时先改 `scripts/next-state.py` 并让 `--self-check` 通过。只改本文件的转移表，机器不会跟着变。
