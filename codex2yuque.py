#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Codex → 语雀 公式转换器
======================

把 Codex（或 GitHub/Typora 风格）输出的 Markdown 数学公式，
转成「语雀」能用的格式。

支持识别的公式分隔符：
    $$...$$      块级公式（行间）
    $...$        行内公式
    \[...\]      块级公式（LaTeX 原生）
    \(...\)      行内公式（LaTeX 原生）
    ```math ... ```  块级公式（Codex 代码块语法）

两种输出模式：
    import   —— 统一成 $$...$$ / $...$，导出 .md 给语雀「导入 Markdown」用
    manual   —— 把公式替换成【公式N】占位符 + 单独列出干净 LaTeX 清单，
                供手动插入语雀「公式卡片」（默认）

用法：
    python codex2yuque.py --clip                 # 读剪贴板→转成占位符→写回剪贴板
    python codex2yuque.py input.md -o out.md -m import   # 导出 .md 给语雀导入
"""

import re
import sys
import argparse
import subprocess

# 占位符，用于保护被转义的美元符号 \$ （这是字面 $，不是公式）
DOLLAR_PLACEHOLDER = "\x00DOLLAR\x00"


def protect_escaped_dollars(text):
    """把 \\$ 保护起来，避免被当成公式分隔符"""
    return text.replace("\\$", DOLLAR_PLACEHOLDER)


def restore_escaped_dollars(text):
    """恢复 \\$"""
    return text.replace(DOLLAR_PLACEHOLDER, "\\$")


def extract_formulas(text, mode="import"):
    """
    解析并转换数学公式。

    返回 (转换后的正文, 公式清单列表)：
        - 公式清单里每一项是干净的 LaTeX（不含 $ 分隔符）
        - import 模式下清单为空（公式保留在正文里）
    """
    text = protect_escaped_dollars(text)
    formulas = []  # 干净 LaTeX 列表

    # 单次遍历、按文档顺序匹配五种公式语法。
    # 交替顺序：长分隔符（$$ / \[ / ```math）优先，避免被行内 $ 误匹配。
    # 块级用 .+?（DOTALL 允许跨行）；行内用 [^...\n] 禁止跨行、禁止嵌套。
    formula_re = re.compile(
        r"\$\$(.+?)\$\$"              # group 1: 块级 $$...$$
        r"|\\\[(.+?)\\\]"             # group 2: 块级 \[...\]
        r"|\$([^$\n]+)\$"             # group 3: 行内 $...$
        r"|\\\(([^\\\n]+)\\\)"        # group 4: 行内 \(...\)
        r"|```math\s*\n(.*?)\n```",   # group 5: 块级 ```math ... ```
        re.DOTALL,
    )

    def repl(m):
        # 取第一个非 None 的分组，判断是块级（group 1/2/5）还是行内（group 3/4）
        is_block = (
            m.group(1) is not None
            or m.group(2) is not None
            or m.group(5) is not None
        )
        latex = (
            m.group(1) or m.group(2) or m.group(3)
            or m.group(4) or m.group(5)
        ).strip()
        if mode == "import":
            return ("$$" + latex + "$$") if is_block else ("$" + latex + "$")
        formulas.append(latex)
        return f"【公式{len(formulas)}】"

    text = formula_re.sub(repl, text)
    text = restore_escaped_dollars(text)
    return text, formulas


def build_formula_list(formulas):
    """生成公式清单（干净 LaTeX，按序号）"""
    if not formulas:
        return ""
    lines = ["", "=" * 40, "公式清单（粘贴时按顺序插入语雀「公式卡片」）", "=" * 40]
    for i, latex in enumerate(formulas, 1):
        lines.append(f"{i}. {latex}")
    return "\n".join(lines)


def _clipboard_get():
    """ctypes 读剪贴板（UTF-16，无编码问题），失败返回 None"""
    import ctypes
    from ctypes import wintypes
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        CF_UNICODETEXT = 13

        user32.OpenClipboard.argtypes = [wintypes.HWND]
        user32.OpenClipboard.restype = wintypes.BOOL
        user32.IsClipboardFormatAvailable.argtypes = [wintypes.UINT]
        user32.IsClipboardFormatAvailable.restype = wintypes.BOOL
        user32.GetClipboardData.argtypes = [wintypes.UINT]
        user32.GetClipboardData.restype = wintypes.HANDLE
        user32.CloseClipboard.restype = wintypes.BOOL
        kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalLock.restype = wintypes.LPVOID
        kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalUnlock.restype = wintypes.BOOL

        if not user32.OpenClipboard(None):
            return None
        try:
            if not user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
                return None
            h = user32.GetClipboardData(CF_UNICODETEXT)
            if not h:
                return None
            p = kernel32.GlobalLock(h)
            if not p:
                return None
            try:
                return ctypes.wstring_at(p)
            finally:
                kernel32.GlobalUnlock(h)
        finally:
            user32.CloseClipboard()
    except Exception as e:
        sys.stderr.write(f"[读取剪贴板失败] {e}\n")
        return None


def _clipboard_set(text):
    """ctypes 写剪贴板（UTF-16），成功返回 True"""
    import ctypes
    from ctypes import wintypes
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        CF_UNICODETEXT = 13
        GMEM_MOVEABLE = 0x0042

        user32.OpenClipboard.argtypes = [wintypes.HWND]
        user32.OpenClipboard.restype = wintypes.BOOL
        user32.EmptyClipboard.restype = wintypes.BOOL
        user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
        user32.SetClipboardData.restype = wintypes.HANDLE
        user32.CloseClipboard.restype = wintypes.BOOL
        kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
        kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
        kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalLock.restype = wintypes.LPVOID
        kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalUnlock.restype = wintypes.BOOL
        kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalFree.restype = wintypes.HGLOBAL

        data = text.encode("utf-16-le") + b"\x00\x00"
        h = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
        if not h:
            return False
        p = kernel32.GlobalLock(h)
        if not p:
            kernel32.GlobalFree(h)
            return False
        ctypes.memmove(p, data, len(data))
        kernel32.GlobalUnlock(h)
        if not user32.OpenClipboard(None):
            kernel32.GlobalFree(h)
            return False
        try:
            user32.EmptyClipboard()
            if not user32.SetClipboardData(CF_UNICODETEXT, h):
                kernel32.GlobalFree(h)
                return False
        finally:
            user32.CloseClipboard()
        return True
    except Exception as e:
        sys.stderr.write(f"[写入剪贴板失败] {e}\n")
        return False


def read_clipboard():
    """Windows 下读剪贴板"""
    return _clipboard_get()


def write_clipboard(text):
    """Windows 下写剪贴板"""
    return _clipboard_set(text)


def main():
    ap = argparse.ArgumentParser(description="Codex → 语雀 公式转换器")
    ap.add_argument("input", nargs="?", help="输入 .md 文件（缺省从 stdin 读）")
    ap.add_argument("-o", "--output", help="输出文件（缺省打印到 stdout）")
    ap.add_argument("-m", "--mode", default="manual",
                    choices=["import", "manual"],
                    help="输出模式（默认 manual）")
    ap.add_argument("--clip", action="store_true",
                    help="从剪贴板读取，转换后写回剪贴板")
    args = ap.parse_args()

    # 读取输入
    if args.clip:
        text = read_clipboard()
        if text is None:
            sys.stderr.write("无法读取剪贴板\n")
            sys.exit(1)
    elif args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    # 转换
    converted, formulas = extract_formulas(text, mode=args.mode)

    # 输出
    if args.clip:
        # 剪贴板只放正文（带占位符），公式清单打印到控制台方便对照
        ok = write_clipboard(converted)
        if ok:
            print(f"✅ 正文已写入剪贴板（共 {len(formulas)} 个公式）")
            if formulas:
                print(build_formula_list(formulas))
        else:
            print("❌ 写入剪贴板失败")
    elif args.output:
        out = converted
        if formulas:
            out += build_formula_list(formulas)
        if not out.endswith("\n"):
            out += "\n"
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"✅ 已写入 {args.output}（模式: {args.mode}，公式 {len(formulas)} 个）")
    else:
        sys.stdout.write(converted)
        if formulas:
            sys.stdout.write(build_formula_list(formulas))


if __name__ == "__main__":
    main()
