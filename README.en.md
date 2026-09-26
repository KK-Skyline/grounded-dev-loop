<p align="center">
  <a href="README.md">中文</a> · <strong>English</strong>
</p>

<p align="center">
  <img src="assets/hero.png" alt="据实落地 grounded-dev-loop" width="100%">
</p>

<p align="center">
  <a href="LICENSE"><img alt="CC BY-NC 4.0" src="https://img.shields.io/badge/license-CC%20BY--NC%204.0-c4a574"></a>
  <img alt="Cursor Agent Skill" src="https://img.shields.io/badge/Cursor-Agent%20Skill-2a2620">
</p>

<p align="center">
  <a href="#what-it-does">What it does</a> ·
  <a href="#usage">Usage</a> ·
  <a href="#authors">Authors</a> ·
  <a href="#license">License</a>
</p>

> A Cursor Agent Skill. In a long thread, coding and debugging drift: the goal turns into an epic, a chat summary is treated as fact, and one edit lands on a surface it should leave alone. 据实落地 locks this turn to: **goal → mode → working set → evidence from this turn → one change → verification at the real entry → neighbors → stop.**

## What it does

| It locks | It leaves alone |
| --- | --- |
| The goal, in the user's words for this turn | The previous assistant's conclusion, used as evidence |
| One mode: investigate / debug / implement / refactor | A refactor slipped into a debug |
| A working set of about seven symbols; the cap limits edits only | A named reproduction skipped by a stop rule; unnamed data, secrets, or generated files |
| Verification on the entry the user actually hits | A test expected-value edited so the run turns green |

The instructions are in [SKILL.md](SKILL.md). Boundaries are in [reference.md](reference.md). Short examples are in [examples.md](examples.md).

## Usage

Clone it into Cursor's personal skills directory:

```bash
git clone https://github.com/KK-Skyline/grounded-dev-loop.git "$HOME/.cursor/skills/grounded-dev-loop"
```

Windows PowerShell:

```powershell
git clone https://github.com/KK-Skyline/grounded-dev-loop.git "$env:USERPROFILE\.cursor\skills\grounded-dev-loop"
```

In chat, say “据实落地” or `@grounded-dev-loop`. The machine id is `grounded-dev-loop`.

After changing a Chinese text file, run this from the repository root:

```text
python scripts/assert-utf8.py
```

It checks that Markdown and JSON are UTF-8 with a BOM, and that the heading 「据实落地」 was not corrupted by a system ANSI save.

## Authors

- **院长** ([KK-Skyline](https://github.com/KK-Skyline))
- **Grok** (xAI)

The skill text, boundaries, examples, and encoding constraint were written together in Cursor. Grok has no GitHub account and does not appear on the contributors graph, so this section records that work.

Made on 2026-09-18. The Cursor conversation title that day was “Excel file modification instructions” (id `b2acdcd0-9a49-43fd-bb77-f1a67382df1f`), in the pallet-tool workspace. Later the same day the Chinese name was set to 「据实落地」, and the UTF-8 BOM constraint was added.

## License

[CC BY-NC 4.0](LICENSE) (Attribution-NonCommercial 4.0).

You may copy, share, adapt, and redistribute it. Keep the attribution when you share it, and state what you changed. **Commercial use is not allowed.** No further restrictions are added.

Full legal text: <https://creativecommons.org/licenses/by-nc/4.0/legalcode>
