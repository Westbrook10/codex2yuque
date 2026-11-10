# codex2yuque

一个**零第三方依赖**的 Python 小工具：把 Codex / ChatGPT 生成的 Markdown 数学公式，自动转换成语雀、MarkText、GitHub 等目标应用能正常显示的格式。

## 这是什么

用 Codex（或 ChatGPT、Claude 等 AI）生成带数学公式的 Markdown 文档时，公式用 LaTeX 语法书写，但**分隔符五花八门**：

| 分隔符 | 类型 | 示例 |
|---|---|---|
| `$$...$$` | 块级 | `$$f(x)=x^2$$` |
| `$...$` | 行内 | `$x$` |
| `\[...\]` | 块级（LaTeX 原生） | `\[\int_a^b f(x)\,dx\]` |
| `\(...\)` | 行内（LaTeX 原生） | `\(E=mc^2\)` |
| ```` ```math ...``` ```` | 块级（代码块） | ```` ```math y = mx + b``` ```` |

而不同的目标应用**只认其中一两种**：

| 目标 | 能识别的公式语法 |
|---|---|
| 语雀 | 纯 LaTeX（不带 `$`），走「公式卡片」或「导入 Markdown」 |
| MarkText / Typora | `$$...$$`、`$...$` |
| GitHub | `$$...$$`、`$...$` |

`codex2yuque.py` 帮你**在几种语法之间自动转换**，省去手工改分隔符的麻烦。

## 功能

- 识别**五种**公式分隔符（见上表），单次遍历、按文档顺序处理
- 两种输出模式：
  - `import`：统一成 `$$...$$` / `$...$`，导出 .md 给语雀「导入 Markdown」或 MarkText
  - `manual`：把公式替换成 `【公式N】` 占位符，并单独列出干净 LaTeX 清单，供手动插入语雀「公式卡片」
- **剪贴板模式**（Windows）：复制 → 转换 → 写回剪贴板
- 自动保护被转义的 `\$`（字面美元符，不误判为公式）
- 无第三方依赖：文件模式仅用 Python 标准库；剪贴板模式用 Windows 自带 ctypes

## 环境要求

- **Python 3.6+**（文件模式跨平台：Windows / macOS / Linux）
- **Windows**（剪贴板模式 `--clip` 需要）
- 不需要 `pip install`，没有第三方依赖

## 安装

### 方式一：直接下载（推荐，适合不熟悉 git 的用户）

1. 点击本仓库右上角 **Code → Download ZIP**，解压到任意目录
2. Windows 用户：确认 Python 已安装并加入 PATH（安装时勾选 **"Add Python to PATH"**）

### 方式二：git clone

```bash
git clone https://github.com/Westbrook10/codex2yuque.git
cd codex2yuque
```

## 使用方法

### 方法一：剪贴板模式（Windows，最简单）

适合把 AI 内容贴到语雀，需要手动插公式卡片的场景：

1. 在 Codex / ChatGPT 里复制带公式的内容
2. 双击 `codex2yuque.bat`
3. 正文已写回剪贴板（公式变成 `【公式N】`），公式清单显示在黑色窗口里
4. 粘贴正文到语雀，对照窗口里的清单，逐个插入「公式卡片」

### 方法二：文件转换（给语雀「导入 Markdown」或 MarkText）

```bash
python codex2yuque.py 输入.md -o 输出.md -m import
```

导出后的 .md 里公式统一成 `$$...$$`，可直接用语雀「导入 Markdown」，或 MarkText 打开查看。

### 方法三：拖拽转换（给 MarkText 查看）

1. 把 .md 文件**拖到** `convert_md_for_marktext.bat` 图标上松开
2. 公式自动转成 MarkText 能渲染的 `$$...$$`（原地覆盖）
3. 双击 .md 即可在 MarkText 正常查看

### 命令行参数

| 参数 | 说明 |
|---|---|
| `input` | 输入 .md 文件（缺省从 stdin 读） |
| `-o, --output` | 输出文件（缺省打印到 stdout） |
| `-m, --mode` | `import` 或 `manual`（默认 `manual`） |
| `--clip` | 从剪贴板读取，转换后写回剪贴板 |

## 常见问题

**Q：双击 .bat 报「不是内部或外部命令」？**
A：Python 没加入 PATH。重新安装 Python 并勾选 "Add Python to PATH"，或直接在命令行运行 `python codex2yuque.py ...`。

**Q：语雀里公式还是显示不了？**
A：语雀不认 `$...$` / `$$...$$` 分隔符。用 `manual` 模式（剪贴板）走「公式卡片」，或用 `-m import` 走「导入 Markdown」。

**Q：MarkText 里 `\[...\]` 或 ```` ```math ```` 不渲染？**
A：MarkText 只认 `$$...$$`。用 `convert_md_for_marktext.bat` 拖拽转换，或 `python codex2yuque.py 文件.md -m import -o 文件.md`。

**Q：公式里的 `\$` 被当成公式了？**
A：不会。程序会自动保护转义的 `\$`，恢复后仍是字面美元符。

## 许可证

[MIT](LICENSE)
