---
name: ipynb-to-py-verbatim
description: "用于 ipynb 转 py、ipynb to py、notebook 转 Python。固定使用 Conda 环境 ipynb_py_conda（缺失则创建，已有则复用），以 Jupytext py:hydrogen 输出同目录同名的 # %% 脚本；保留代码、注释和 magic，Markdown/raw 转注释，转换无中间文件。支持 Windows、Linux、macOS。"
---

# 使用 Jupytext Hydrogen 转换 ipynb 为 py

用户说“ipynb 转 py”时，默认使用 [scripts/convert_notebook.py](scripts/convert_notebook.py)。该脚本调用公共 `jupytext.writes()` 的 `py:hydrogen` 格式，并核对输出；不要让 AI 重新生成原代码，也不要换回其他导出器或旧的标准库渲染方案。

只传入原 notebook 路径：`A.ipynb → A.py`、`A.part.ipynb → A.part.py`，目录和文件名主体不变。这是内容转换，原 `.ipynb` 保留，不对原文件执行重命名。每个 notebook 仅新增一个最终 `.py`，不另存报告、图片、脚本副本或中间 notebook。

## 转换规则

- 保留原单元顺序、全部代码和原注释；只允许将源码中的 CRLF/CR 统一为 LF，并允许单元之间的分隔空行。原缩进、单元内空白、行尾空格、magic、shell 命令和已有错误都保留。
- code 使用 `# %%`；Markdown 使用 `# %% [markdown]`，raw 使用 `# %% [raw]`。Markdown/raw 正文全部为 `#` 行注释，不使用三引号文本。
- `%`、`!`、`%%bash` 等保持可交给 IPython 的原语法，不注释命令、不改写成 `subprocess`。这保留执行能力，转换过程本身不执行原程序。
- 不导出 `outputs`、图片二进制、`attachments`、widgets 或执行编号。不复制或下载图片。Markdown 中原有图片引用作为注释文字保留；源码本来包含的图片处理代码或字符串仍属于源码，应保留。
- 原 notebook 只读。已存在的输出（包括符号链接、悬空链接和目录）直接拒绝，不提供强制覆盖，不另加后缀避让；父目录必须已存在。

## 环境与执行

所有平台统一使用名为 `ipynb_py_conda` 的 Conda 环境；不改名或删除其他环境，不回退到 base、venv、uv 或系统 Python。按下述流程自动准备或复用；若用户/项目明确限制安装，遵守该限制，已经授权的操作不重复询问。

1. 找到已有 Conda 的真实可执行路径，运行 `"<CONDA_EXE>" env list --json`（PowerShell 在命令前加 `&`），检查环境路径。不存在 Conda 时报告缺少 Conda，不自行下载独立软件。
2. 没有 `ipynb_py_conda` 时，创建并安装转换依赖：Windows 使用 `& '<CONDA_EXE>' create --name ipynb_py_conda --override-channels -c conda-forge python=3.11 jupytext=1.16.7 --yes`；Linux/macOS 使用 `"<CONDA_EXE>" create --name ipynb_py_conda --override-channels -c conda-forge python=3.11 jupytext=1.16.7 --yes`。Jupytext 会带入 nbformat 等依赖，无需安装完整 Jupyter、IPython 或 Bash 来做转换。
3. 已有环境直接复用，解析其实际 prefix：Windows 解释器为 `<PREFIX>/python.exe`，Linux/macOS 为 `<PREFIX>/bin/python`。不要猜测 Conda 安装目录；多个同名 prefix 无法消歧时先询问。使用这个绝对路径及 `-B -c "import sys, jupytext, nbformat; print(sys.executable); print(sys.version); print(jupytext.__version__); assert sys.version_info >= (3, 9)"` 检查解释器和依赖。已有可用的 Jupytext 不自动升级或降级，每次转换仍逐字符校验。
4. 如果已有环境仅缺 Jupytext/nbformat，在同一已确认 prefix 安装：`"<CONDA_EXE>" install --prefix "<PREFIX>" --override-channels -c conda-forge jupytext=1.16.7 nbformat --yes`（PowerShell 前加 `&`），然后重新核验。已有 Python 低于 3.9 或依赖安装/求解失败时，报告问题，不静默重建环境、更改版本或改用另一个环境。

初次安装 Skill、创建环境或补齐依赖可能产生安装器临时文件、环境文件及 Conda 包缓存；“无中间文件”适用于依赖就绪后的 notebook 转换，不能把安装过程描述成零文件。

解析本 skill 目录及上述环境解释器的绝对路径。日常转换直接调用这个来源已核验的 Conda Python；不要使用 `conda run`，它会生成临时 `.bat`/`.sh` 启动脚本。`-B` 与转换器内的 `sys.dont_write_bytecode = True` 阻止依赖导入生成 `.pyc`。以下尖括号内容必须替换为真实路径：

Windows PowerShell：

```powershell
& '<IPYNB_PY_CONDA_PYTHON>' -B '<SKILL_DIR>/scripts/convert_notebook.py' '<SOURCE.ipynb>'
```

Linux/macOS bash/zsh：

```sh
"<IPYNB_PY_CONDA_PYTHON>" -B "<SKILL_DIR>/scripts/convert_notebook.py" "<SOURCE.ipynb>"
```

兼容旧调用的第二个路径参数只接受与自动推导结果相同的路径；不得指定其他名称或目录。JSON 校验摘要只输出到 stdout，不重定向到文件；不要生成临时测试脚本、日志、缓存、临时 notebook、备份或图片。转换完全在内存中完成，只以独占创建模式写最终 `.py`。磁盘写入失败或进程被中断时可能留下不完整的最终文件；应报告失败并保留现场，不宣称成功或自动删除/覆盖重试。

固定转换配置为：

```python
{
    "extension": ".py",
    "format_name": "hydrogen",
    "comment_magics": False,
    "cell_metadata_filter": "-all",
    "notebook_metadata_filter": "-all",
    "root_level_metadata_as_raw_cell": False,
}
```

脚本在内存中仅复制各单元的类型与原文，并清空全部 notebook/cell 元数据和输出载荷后交给 Jupytext。这避免 `active`、`language`、`cell_marker` 等原元数据把代码注释掉或把 Markdown 变成三引号；仅设置 metadata filter 不足以规避所有此类行为。关闭 `root_level_metadata_as_raw_cell`，避免首个 `--- … ---` raw 单元被当成 YAML 文件头。

## Bash 与 magic 的运行方式

- 导出文件中含 `!`、`%` 或 `%%bash` 时，使用 IPython/Jupyter kernel 按原单元运行，例如 VS Code 的 `# %%` 单元。普通 `python output.py` 不能直接解释这些语法；也不要把含 `%%bash` 的整份脚本一次交给 IPython 当成一个单元。
- `!命令` 使用宿主系统的 shell，Windows 中并不自动等同于 Bash；`%%bash` 才明确调用 Bash。原命令依赖的程序仍须在执行环境可用。
- 执行 `%%bash` 前确认现有 Bash 实际可运行。Windows 的 `bash.exe` 可能是没有可用发行版的 WSL 启动器；已有 Git Bash 可作为实际解释器。可在初始化 IPython 的配置中，用官方 `ScriptMagics.script_paths` 将 `bash` 映射到已确认的 Bash 绝对路径。不要为此改写用户单元、修改全局 PATH 或自动安装 WSL/Git Bash。
- 只有用户请求运行时才执行转换后的代码。验证转换工具时只运行专门构造的无害测试单元，不执行用户分析 notebook。

## 核验与交付

检查退出码及 JSON：`format` 为 `py:hydrogen`、`line_endings` 为 `LF`、`input_unchanged` 和 `entire_output_verified` 为 `true`，核对单元数量和源/目标 SHA-256。脚本按原单元顺序、已知正文长度检查每个字符，正文中的已有 `# %%` 不作为校验分割依据；最后核对全部输出已被解释，防止夹带输出或附件。

如果 Jupytext 对正文产生 LF 规范化之外的改动，写入前报错停止；不能静默纠错、忽略差异或自动换渲染方案。非 CR/LF 的分隔字符（如换页符、垂直制表符、U+2028）、特殊 Unicode 缩进以及 magic 行的 `# escape` 指令可能触发此保护，应报告具体单元，不宣称转换成功。

已有 `# %%` 必须保留，但编辑器可能将正文中的标记识别为额外分区；提示用户此限制，不转义原代码。支持 nbformat 4 的 Python notebook；明确声明的非 Python 语言、已识别的非 Python kernel 名、未知单元类型和非法 source 会被拒绝。缺少明确语言声明时会提示；仅凭未知 kernel 名无法确认源码语言，不应据此断言其为 Python。

交付输出路径、实际命令、内容核验结果及 Bash 运行所需条件。区分转换内容保留、无害 Bash 测试通过、用户原程序运行正确这三种结论。保持源文件只读，不进行双向同步、`--execute`、`--sync`、`--inplace` 或 formatter 操作。
