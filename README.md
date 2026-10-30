# skill-ipynbtopy

## 1. 主要功能

将 Python Jupyter Notebook（`.ipynb`）转换为带 `# %%` 单元的 `.py`，转换引擎为 Jupytext `py:hydrogen`。

- 保留原代码、原注释、缩进及单元内空白，统一换行为 LF。
- Markdown/raw 正文全部转为行注释，分别使用 `# %% [markdown]`、`# %% [raw]`。
- 保留 `%`、`!`、`%%bash` 原语法，丢弃执行输出、图片二进制和附件；Markdown 图片引用文字仍保留为注释。
- 原 notebook 只读，不执行、纠错或格式化用户代码；输出文件已存在时拒绝覆盖。

适用于 Windows、Linux、macOS。需要 Python 3.9+ 和已有的 Jupytext；Bash/magic 的运行另外需要 IPython/Jupyter 及对应的 shell。

## 2. 文件树与说明

```text
skill-ipynbtopy/
├── README.md                         安装、阅读与运行说明
├── AGENTS.md                         项目架构、进展及代理协作约束
└── ipynb-to-py-verbatim/              可直接安装的完整 skill
    ├── SKILL.md                      触发条件、转换规则与操作流程
    ├── agents/
    │   └── openai.yaml               Codex 展示信息和自动触发设置
    └── scripts/
        └── convert_notebook.py       Jupytext 转换入口及逐单元内容校验
```

## 3. 使用与阅读顺序

先阅读本文件，再阅读 [SKILL.md](ipynb-to-py-verbatim/SKILL.md)；维护代码时同时遵守 [AGENTS.md](AGENTS.md)。

**直接下载：** [下载整个仓库的 ZIP](https://github.com/LouChen-med/skill-ipynbtopy/archive/refs/heads/main.zip)，解压后取其中的 `ipynb-to-py-verbatim` 文件夹。

**让 Codex 安装：** 将下面的请求交给 Codex：

```text
使用 $skill-installer，从 https://github.com/LouChen-med/skill-ipynbtopy/tree/main/ipynb-to-py-verbatim 安装这个 skill。
```

**手动安装：** 只复制完整的 `ipynb-to-py-verbatim` 文件夹到 Codex 的用户 skills 目录。当前通用位置为 Linux/macOS 的 `~/.agents/skills/`，或 Windows PowerShell 的 `$HOME/.agents/skills/`。如果当前 Codex 已配置其他 skills 目录，使用该实例实际采用的位置。不要把整个仓库当成一个 skill，也不要重复安装同名副本。

安装后可直接说“ipynb 转 py”，或显式使用 `$ipynb-to-py-verbatim`。Codex 会自动检测 skill；若未显示，重启 Codex 后再检查。

## 4. 代码运行顺序

1. 确认已有 Python 环境及其中的 Jupytext。若需要自行安装依赖，先按当前环境管理和授权规则操作。Conda 命令模板如下，替换实际 Conda 路径与已有环境名；此步骤无需为转换安装用户分析代码的依赖。

   ```sh
   "<CONDA_EXE>" install -n "<ENV_NAME>" -c conda-forge jupytext
   ```

   Windows PowerShell 在上述命令前加调用运算符 `&`。

2. 确认源 `.ipynb` 和尚不存在的目标 `.py`，目标父目录必须存在。通过已确认的解释器运行脚本；所有尖括号内容均须替换为实际绝对路径。

   Windows PowerShell：

   ```powershell
   & '<PYTHON_EXE>' -B '<SKILL_DIR>/scripts/convert_notebook.py' '<SOURCE.ipynb>' '<NEW_OUTPUT.py>'
   ```

   Linux/macOS bash/zsh：

   ```sh
   "<PYTHON_EXE>" -B "<SKILL_DIR>/scripts/convert_notebook.py" "<SOURCE.ipynb>" "<NEW_OUTPUT.py>"
   ```

   使用 Conda 执行时，完整模板见 [SKILL.md](ipynb-to-py-verbatim/SKILL.md)。

3. 检查退出码和 JSON 报告：`format` 应为 `py:hydrogen`，`line_endings` 应为 `LF`，`input_unchanged` 与 `entire_output_verified` 应为 `true`。脚本同时报告单元数及源/目标 SHA-256；正文出现 LF 规范化以外的变化时会停止写入。

4. 如需运行转换后的 Bash/magic，在 IPython/Jupyter kernel 中按 `# %%` 单元执行。`%%bash` 中间不加空格，并位于代码单元第一行；`!命令` 使用宿主系统 shell，`%%bash` 才明确调用 Bash。Windows 需确认实际 Bash 可用，必要时通过 IPython 的 `ScriptMagics.script_paths` 指定已有 Git Bash。含这些语法的文件不能直接交给普通 `python output.py`，也不应整份作为一个 IPython 单元执行。
