#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量替换：Waymark→Waymark, Aeroflie→Aeroflie
安全规则：
  - CODE 行（cflib 库引用）不替换 Aeroflie/Aeroflie
  - URL 行删除链接
"""
import os
import re

PROJECT_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
EXTS = {'.py', '.ui', '.json', '.ts', '.md', '.iss', '.spec', '.toml', '.txt', '.yml', '.cfg', '.xml'}
SKIP_DIRS = {'build', 'dist', '.git', '__pycache__', '.claude', 'node_modules', 'memory', '.vscode', 'venv', '.venv'}

def is_cflib_code_line(line):
    """检测是否引用了 cflib 库的 Aeroflie 类（不能替换）"""
    stripped = line.lstrip()
    # 纯注释行 - 不是代码
    if stripped.startswith('#'):
        return False
    # import cflib 的行
    if re.search(r'\b(from|import)\s+cflib\b', line):
        return True
    # 类型标注引用 cflib.crazyflie.Aeroflie
    if 'cflib.crazyflie' in line:
        return True
    # Aeroflie 作为类名使用（实例化、类型标注、参数类型）——不在字符串中
    # Aeroflie(  |  : Aeroflie  |  -> Aeroflie  |  , Aeroflie
    if re.search(r'(?<![ "\'#])\bAeroflie\s*\(', line):
        return True
    if re.search(r':\s*Aeroflie\b', line):
        return True
    return False

def is_url_line(line):
    """检测是否包含 waymark/crazyflie 相关 URL"""
    return bool(re.search(r'(waymark\.(io|se|com)|github\.com/waymark)', line, re.IGNORECASE))

def process_line(line, file_ext):
    """处理单行"""
    orig = line

    # === URL 处理 ===
    if is_url_line(line):
        # Markdown 链接: [text](url) → text
        line = re.sub(r'\[([^\]]*)\]\([^)]*waymark[^)]*\)', r'\1', line, flags=re.IGNORECASE)
        # 裸 URL
        line = re.sub(r'https?://[^\s\'"<>]*waymark[^\s\'"<>]*', '#', line, flags=re.IGNORECASE)
        # HTML href
        line = re.sub(r"href='[^']*waymark[^']*'", "href='#'", line, flags=re.IGNORECASE)
        line = re.sub(r'href="[^"]*waymark[^"]*"', 'href="#"', line, flags=re.IGNORECASE)
        # Docker image
        line = re.sub(r'\bwaymark/[a-zA-Z0-9_-]+', 'waymark/toolbelt', line)

    # === Waymark → Waymark（所有上下文安全） ===
    line = line.replace('Waymark', 'Waymark')
    line = line.replace('waymark', 'waymark')

    # === Aeroflie → Aeroflie（仅非 CODE 行） ===
    if not is_cflib_code_line(orig):
        line = line.replace('Aeroflie', 'Aeroflie')
        # 小写 crazyflie → aeroflie（仅注释/文档/翻译，非模块路径）
        # 小心：cflib.crazyflie 已在 is_cflib_code_line 中被保护
        if file_ext not in ('.py', '.spec'):
            line = line.replace('crazyflie', 'aeroflie')

    return line

def process_file(filepath):
    """处理单个文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        try:
            with open(filepath, 'r', encoding='gbk') as f:
                lines = f.readlines()
        except Exception:
            return False

    ext = os.path.splitext(filepath)[1].lower()
    changed = False
    new_lines = []

    for line in lines:
        new_line = process_line(line, ext)
        if new_line != line:
            changed = True
        new_lines.append(new_line)

    if changed:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        return True
    return False

def main():
    updated = 0
    scanned = 0
    for root, dirs, files in os.walk(PROJECT_DIR):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in EXTS:
                continue
            fpath = os.path.join(root, fname)
            scanned += 1
            if process_file(fpath):
                updated += 1
                print(f"  [OK] {os.path.relpath(fpath, PROJECT_DIR)}")
    print(f"\nDone: scanned {scanned}, updated {updated}")

if __name__ == '__main__':
    main()
