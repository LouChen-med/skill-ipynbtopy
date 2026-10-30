---
name: ipynb-to-py-verbatim
description: "用于 ipynb 转 py、ipynb to py、notebook 转 Python。使用 Jupytext py:hydrogen 保留原代码、原注释及可按单元执行的 Bash/magic，Markdown/raw 转注释，丢弃输出和图片附件，统一 LF；不执行、纠错或格式化用户代码。支持 Windows、Linux、macOS。"
---

# 使用 Jupytext Hydrogen 转换 ipynb 为 py

用户说“ipynb 转 py”时，默认使用 [scripts/convert_notebook.py](scripts/convert_notebook.py)。该脚本调用公共 `jupytext.writes()` 的 `py:hydrogen` 格式，并核对输出；不要让 AI 重新生成原代码，也不要换回其他导出器或旧的标准库渲染方案。

## 转换规则

- 保留原单元顺序、全部代码和原注释；只允许将源码中的 CRLF/CR 统一为 LF，并允许单元之间的分隔空行。原缩进、单元内空白、行尾空格、magic、shell 命令和已有错误都保留。
- code 使用 `# %%`；Markdown 使用 `# %% [markdown]`，raw 使用 `# %% [raw]`。Markdown/raw 正文全部为 `#` 行注释，不使用三引号文本。
- `%`、`!`、`%%bash` 等保持可交给 IPython 的原语法，不注释命令、不改写成 `subprocess`。这保留执行能力，转换过程本身不执行原程序。
- 不导出 `outputs`、图片二进制、`attachments`、widgets 或执行编号。不复制或下载图片。Markdown 中原有图片引用作为注释文字保留；源码本来包含的图片处理代码或字符串仍属于源码，应保留。
- 原 notebook 只读。已存在的输出直接拒绝，不提供强制覆盖；父目录必须已存在。

## 环境与执行

使用当前用户/项目允许且已经确认的 Python 3.9+ 环境。转换需要该环境中已有的 Jupytext（依赖包含 nbformat）；本机验证版本为 Jupytext 1.16.7。其他版本仍须通过逐单元内容校验。缺少依赖时先检查其他允许的已有环境；安装或升级依赖必须遵守用户授权规则，不自动安装。

解析本 skill 目录下的脚本绝对路径，不依赖工作目录、固定盘符、用户名、shebang 或脚本可执行权限。以下模板中的尖括号内容必须替换为已确认的真实路径：

Windows PowerShell：

```powershell
& '<PYTHON_EXE>' -B '<SKILL_DIR>/scripts/convert_notebook.py' '<SOURCE.ipynb>' '<NEW_OUTPUT.py>'
```

Linux/macOS bash/zsh：

```sh
"<PYTHON_EXE>" -B "<SKILL_DIR>/scripts/convert_notebook.py" "<SOURCE.ipynb>" "<NEW_OUTPUT.py>"
```

用户要求 Conda 时，使用已确认的 Conda 路径和真实环境名：

```powershell
& '<CONDA_EXE>' run -n '<ENV_NAME>' python -B '<SKILL_DIR>/scripts/convert_notebook.py' '<SOURCE.ipynb>' '<NEW_OUTPUT.py>'
```

```sh
"<CONDA_EXE>" run -n "<ENV_NAME>" python -B "<SKILL_DIR>/scripts/convert_notebook.py" "<SOURCE.ipynb>" "<NEW_OUTPUT.py>"
```

固定转换配置为：

```python
{
    "extension": ".py",
    "format_name": "hydrogen",
    "comment_magics": False,
    "cell_metadata_filter": "-all",
    "notebook_metadata_filter": "-all",
}
```

脚本在内存中仅复制各单元的类型与原文，并清空全部 notebook/cell 元数据和输出载荷后交给 Jupytext。这避免 `active`、`language`、`cell_marker` 等原元数据把代码注释掉或把 Markdown 变成三引号；仅设置 metadata filter 不足以规避所有此类行为。

## Bash 与 magic 的运行方式

- 导出文件中含 `!`、`%` 或 `%%bash` 时，使用 IPython/Jupyter kernel 按原单元运行，例如 VS Code 的 `# %%` 单元。普通 `python output.py` 不能直接解释这些语法；也不要把含 `%%bash` 的整份脚本一次交给 IPython 当成一个单元。
- `!命令` 使用宿主系统的 shell，Windows 中并不自动等同于 Bash；`%%bash` 才明确调用 Bash。原命令依赖的程序仍须在执行环境可用。
- 执行 `%%bash` 前确认现有 Bash 实际可运行。Windows 的 `bash.exe` 可能是没有可用发行版的 WSL 启动器；已有 Git Bash 可作为实际解释器。可在初始化 IPython 的配置中，用官方 `ScriptMagics.script_paths` 将 `bash` 映射到已确认的 Bash 绝对路径。不要为此改写用户单元、修改全局 PATH 或自动安装 WSL/Git Bash。
- 只有用户请求运行时才执行转换后的代码。验证转换工具时只运行专门构造的无害测试单元，不执行用户分析 notebook。

## 核验与交付

检查退出码及 JSON：`format` 为 `py:hydrogen`、`line_endings` 为 `LF`、`input_unchanged` 和 `entire_output_verified` 为 `true`，核对单元数量和源/目标 SHA-256。脚本按原单元顺序、已知正文长度检查每个字符，正文中的已有 `# %%` 不作为校验分割依据；最后核对全部输出已被解释，防止夹带输出或附件。

如果 Jupytext 对正文产生 LF 规范化之外的改动，写入前报错停止；不能静默纠错、忽略差异或自动换渲染方案。少数 Unicode 分隔符可能触发此保护，应报告具体单元，不宣称转换成功。

已有 `# %%` 必须保留，但编辑器可能将正文中的标记识别为额外分区；提示用户此限制，不转义原代码。支持 nbformat 4 的 Python notebook；明确声明的非 Python 语言、已识别的非 Python kernel 名、未知单元类型和非法 source 会被拒绝。缺少明确语言声明时会提示；仅凭未知 kernel 名无法确认源码语言，不应据此断言其为 Python。

交付输出路径、实际命令、内容核验结果及 Bash 运行所需条件。区分转换内容保留、无害 Bash 测试通过、用户原程序运行正确这三种结论。保持源文件只读，不进行双向同步、`--execute`、`--sync`、`--inplace` 或 formatter 操作。
