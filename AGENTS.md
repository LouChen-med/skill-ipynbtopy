# 项目协作指令

## 1. 项目目标

提供供 Codex 与 DeepSeek Harness 共用、可下载和安装的 Skill，使用 Jupytext `py:hydrogen` 将 Python notebook 单向导出为 `.py`。保留原代码、原注释和 Bash/magic 原语法，Markdown/raw 转行注释，丢弃输出及图片附件；仅允许 LF 规范化和单元之间的分隔空行。

## 2. 总体架构

Codex 或 DeepSeek Harness 根据 Skill 描述选择工作流，解析已加载 Skill 的资源目录，并调用同一个固定转换脚本。脚本只读解析 notebook，在内存中清除元数据和输出载荷，将单元类型与源码交给公共 `jupytext.writes()`，核对完整输出后创建目标文件，并返回 JSON 摘要。

输入 `A.ipynb` 固定输出同目录 `A.py`，原文件保留。环境统一使用 `ipynb_py_conda`，缺失则按授权创建，已有则复用；环境及 Conda 安装缓存保留在 notebook 目录之外。转换在内存中完成，每次成功调用只新增最终 `.py`，摘要仅输出终端。

## 3. 核心模块

- **工作流与发现：** `SKILL.md` 定义双运行器的触发条件、保留规则及跨平台操作；`agents/openai.yaml` 提供 Codex 展示信息与调用策略。DeepSeek Harness 通过技能资源目录定位同一转换器，安装时核对实际扫描目录及同名副本。
- **转换与隔离：** 固定使用 Hydrogen、`comment_magics=False` 和元数据过滤。仍须在内存中清空原 notebook/cell 元数据，防止 `active`、`language`、`cell_marker` 等影响代码或 Markdown。
- **内容与文件保护：** 按原单元顺序及已知正文长度校验，不按源码中已有的 `# %%` 分割。仅接受 CRLF/CR→LF，必须解释全部输出字符；核对源/目标哈希，拒绝覆盖已有输出。
- **依赖与运行：** 固定 Conda 环境 `ipynb_py_conda` 中的 Python 3.9+、Jupytext 及 nbformat 负责转换；新建环境指定 Python 3.11 和 Jupytext 1.16.7，已有可用环境不自动升级或降级。直接使用已核验的环境解释器及 `-B`，避免 `conda run` 的临时启动脚本与 Python 字节码缓存。IPython/Jupyter 和对应 shell 仅用于用户另行请求的代码执行。

## 4. 当前进展

- 已完成 Hydrogen 转换、元数据与输出载荷隔离、Markdown/raw 注释、同名输出、原文件只读保护及逐字符内容校验；已存在的输出、悬空链接及非普通输入文件会被拒绝。
- 已完成 Codex 与 DeepSeek Harness 共用 Skill 的适配。已用 Windows 上的 DeepSeek Harness 0.2.1-rc.2 实际加载器验证技能发现、用户/模型调用权限、资源目录定位，并从加载结果调用转换器确认命令行入口和拒绝覆盖行为。此验证不等于已完成模型自然语言触发的端到端测试。
- 此前 Windows 回归的 23 项测试全部通过，其中包含 120 组随机正文组合及现有 notebook 与既有输出的逐字比对。测试通过 stdin/内存执行并阻止测试进程写盘；没有新增测试脚本、日志或中间结果，也未执行用户 notebook。
- 该次验证复用了已有 `ipynb_py_conda`：Python 3.11.18、Jupytext 1.16.7、nbformat 5.11.1。原 notebook 与现有输出的 SHA-256 保持不变。
- Linux 已进行可移植性审查及 shell 特殊路径参数检查；完整转换尚未在原生 Linux 环境实测，macOS 亦未原生实测。不能把 Windows 结果表述为三个系统均已实测。
- 已将转换后的 AI 双文件回读设为必做步骤，并完成一份现有 notebook 的 146 个单元只读复核，未发现转换差异；该样本包含 80 个代码单元、66 个 Markdown 单元，不含 raw/magic。复核未执行用户代码、未生成核验文件。
- 已统一仓库根目录下的 Skill 源码布局；Windows 本地仓库已接入 GitHub 既有历史，并配置 `main` 跟踪 `origin/main`。后续仍需补充 Linux/macOS 原生验证。

## 5. 协作规范

- 修改前先阅读现有实现与依赖，保持最小改动，不擅自更换转换引擎或扩展为运行、纠错、格式化工具。
- 原 notebook 保持只读；完整保留代码和原注释，仅规范化 CRLF/CR 为 LF。保留原错误及 Bash/magic，不注释命令、不改写成 `subprocess`。
- Markdown/raw 必须为行注释；输出、附件、图片二进制和 widgets 不进入目标内容。原 Markdown 图片引用及源码中的图片处理语句仍属于原文，应保留。
- 出现额外源码变化时，在写入前停止并报告具体单元；不得忽略差异、伪造成功或静默使用其他渲染方案。
- 遵守当前用户和项目的环境管理规则，统一复用已确认的 `ipynb_py_conda`；缺失环境或依赖按 Skill 流程和已有授权处理，不擅自安装独立 Conda 软件或更改全局配置。发布内容不绑定本机盘符或用户名。
- Bash/magic 按单元交给 IPython/Jupyter；`!` 使用宿主 shell，`%%bash` 需要可用 Bash。验证工具只执行专门构造的无害单元，不能借此执行用户 notebook。
- 发布内容仅为最终 Skill、必要的 Git 忽略配置及本仓库的 README、AGENTS 文档；不提交测试脚本、中间文件、缓存、日志、样本 notebook、转换结果、研究数据、凭据或个人本机路径。
- 临时验证产物仅使用用户指定的既有 `tmp`，不得把 `test` 当作 `tmp` 替代；没有适用的 `tmp` 时优先以内存或 stdin 验证，不自动创建缺失目录，不擅自清理来源不明文件。
- `README.md` 负责目录与使用索引，`AGENTS.md` 负责目标、架构和进展；后续修改这两类文件须有用户明确授权，不自动创建或分发额外代理指令文档。
- 测试与交付只陈述实际验证范围，区分“转换内容保留”“无害 Bash 测试通过”与“用户原程序运行正确”。
