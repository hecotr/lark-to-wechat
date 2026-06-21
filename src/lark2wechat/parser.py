"""飞书 markdown → 中间表示 IR（blocks 列表）。

块类型：
  现有：heading / paragraph / olist / ulist / code / hr / callout / grid / table / whiteboard
  Phase 1 新增：quote（> 与 <quote-container>）/ image（markdown 与 <image token>）/ equation / todo
"""

import re
import html


def parse_feishu_markdown(md_text):
    """解析飞书导出的 markdown（含私有标签）为结构化 blocks 列表。"""
    blocks, lines, i = [], md_text.split('\n'), 0
    while i < len(lines):
        line = lines[i]
        # ---- 飞书私有块标签 ----
        if '<callout' in line:
            c, i = _pc(lines, i); blocks.append(c); continue
        if '<grid' in line:
            g, i = _pg(lines, i); blocks.append(g); continue
        if '<lark-table' in line:
            t, i = _pt(lines, i); blocks.append(t); continue
        if '<whiteboard' in line:
            m = re.search(r'token="([^"]+)"', line)
            blocks.append({"type": "whiteboard", "token": m.group(1) if m else ""}); i += 1; continue
        if '<image' in line and 'token=' in line:
            m = re.search(r'token="([^"]+)"', line)
            blocks.append({"type": "image", "token": m.group(1) if m else ""}); i += 1; continue
        if '<quote-container' in line:
            q, i = _pqc(lines, i); blocks.append(q); continue
        if '<equation>' in line:
            e, i = _peq(lines, i); blocks.append(e); continue
        # ---- 标准标记 ----
        if line.strip() == '---':
            blocks.append({"type": "hr"}); i += 1; continue
        if line.startswith('#'):
            lv = len(re.match(r'^#+', line).group())
            blocks.append({"type": "heading", "level": lv, "text": line.lstrip('#').strip()}); i += 1; continue
        if line.strip().startswith('```'):
            c, i = _pcd(lines, i); blocks.append(c); continue
        if '|' in line and i + 1 < len(lines) and _is_table_separator(lines[i + 1]):
            t, i = _pstd(lines, i); blocks.append(t); continue
        if re.match(r'^\d+\.\s', line.strip()):
            o, i = _po(lines, i); blocks.append(o); continue
        if re.match(r'^-\s+\[[ xX]\]\s+', line.strip()):
            t, i = _ptd(lines, i); blocks.append(t); continue
        if line.strip().startswith('- '):
            u, i = _pu(lines, i); blocks.append(u); continue
        if line.lstrip().startswith('> '):
            q, i = _pq(lines, i); blocks.append(q); continue
        if re.match(r'^!\[[^\]]*\]\([^)]+\)', line.strip()):
            m = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)', line.strip())
            blocks.append({"type": "image", "alt": m.group(1), "src": m.group(2)}); i += 1; continue
        if line.strip() == '':
            i += 1; continue
        blocks.append({"type": "paragraph", "text": line.strip()}); i += 1
    return blocks


def _pc(lines, start):
    fl = lines[start]
    em = re.search(r'emoji="([^"]*)"', fl); bgm = re.search(r'background-color="([^"]*)"', fl)
    emoji = em.group(1) if em else ""; bg = bgm.group(1) if bgm else "light-blue"
    cl, i = [], start + 1
    while i < len(lines) and '</callout>' not in lines[i]: cl.append(lines[i]); i += 1
    return {"type": "callout", "emoji": emoji, "bg_color": bg, "content": '\n'.join(cl).strip()}, i + 1


def _pg(lines, start):
    cm = re.search(r'cols="(\d+)"', lines[start]); cols_n = int(cm.group(1)) if cm else 2
    columns, cur, i = [], None, start + 1
    while i < len(lines) and '</grid>' not in lines[i]:
        if '<column' in lines[i]:
            wm = re.search(r'width="(\d+)"', lines[i]); w = int(wm.group(1)) if wm else 50
            cur = {"width": w, "items": []}
        elif '</column>' in lines[i]:
            if cur: columns.append(cur); cur = None
        elif cur is not None:
            if '<callout' in lines[i]: c, i = _pc(lines, i); cur["items"].append(c); continue
            s = lines[i].strip()
            if s: cur["items"].append({"type": "paragraph", "text": s})
        i += 1
    return {"type": "grid", "columns": columns}, i + 1


def _pt(lines, start):
    """解析 lark-table。正则版，兼容紧凑（同行多 td）与松散（每标签一行）两种格式。"""
    text = '\n'.join(lines[start:])
    end = text.find('</lark-table>')
    table_text = text[:end] if end != -1 else text
    ws_m = re.search(r'column-widths="([^"]*)"', table_text)
    ws = [int(w) for w in ws_m.group(1).split(',')] if ws_m else []
    hm = re.search(r'header-row="(true|false)"', table_text)
    has_header = hm.group(1) == 'true' if hm else False
    rows = []
    for tr in re.findall(r'<lark-tr>(.*?)</lark-tr>', table_text, re.DOTALL):
        cells = [c.strip() for c in re.findall(r'<lark-td>(.*?)</lark-td>', tr, re.DOTALL)]
        rows.append(cells)
    consumed = (text[:end].count('\n') + 1) if end != -1 else (len(lines) - start)
    return {"type": "table", "rows": rows, "widths": ws, "has_header": has_header}, start + consumed


def _is_table_separator(line):
    """识别 markdown 表格分隔行 |---|---|。"""
    s = line.strip()
    return bool(s) and '-' in s and '|' in s and re.match(r'^\|?[\s:|-]+\|?$', s) is not None


def _pstd(lines, start):
    """标准 markdown 表格：| a | b | + |---|---| + 数据行。"""
    def parse_row(line):
        return [c.strip() for c in line.strip().strip('|').split('|')]
    rows = [parse_row(lines[start])]
    i = start + 1
    if i < len(lines) and _is_table_separator(lines[i]):
        i += 1  # 跳过分隔行
    while i < len(lines):
        s = lines[i].strip()
        if s.startswith('|') or s.endswith('|'):
            rows.append(parse_row(lines[i])); i += 1
        else:
            break
    return {"type": "table", "rows": rows, "widths": [], "has_header": True}, i


def _pcd(lines, start):
    lm = re.match(r'```(\w*)', lines[start].strip()); lang = lm.group(1) if lm else ""
    cl, i = [], start + 1
    while i < len(lines) and not lines[i].strip().startswith('```'): cl.append(html.escape(lines[i])); i += 1
    return {"type": "code", "lang": lang, "content": '\n'.join(cl)}, i + 1


def _po(lines, start):
    items, i = [], start
    while i < len(lines):
        m = re.match(r'^(\d+)\.\s+(.*)', lines[i].strip())
        if m: items.append(m.group(2)); i += 1
        else: break
    return {"type": "olist", "items": items}, i


def _pu(lines, start):
    items, i = [], start
    while i < len(lines):
        s = lines[i].strip()
        if s.startswith('- '): items.append(s[2:]); i += 1
        else: break
    return {"type": "ulist", "items": items}, i


def _pq(lines, start):
    """markdown 引用块：连续 > 行合并。"""
    items, i = [], start
    while i < len(lines):
        m = re.match(r'^>\s?(.*)', lines[i].strip())
        if m: items.append(m.group(1)); i += 1
        else: break
    return {"type": "quote", "content": '\n'.join(items).strip()}, i


def _pqc(lines, start):
    """飞书 <quote-container> 引用块。"""
    cl, i = [], start + 1
    while i < len(lines) and '</quote-container>' not in lines[i]:
        cl.append(lines[i]); i += 1
    return {"type": "quote", "content": '\n'.join(cl).strip()}, i + 1


def _peq(lines, start):
    """块级公式：<equation>latex</equation>（同行）。"""
    line = lines[start]
    m = re.search(r'<equation>(.*?)</equation>', line, re.DOTALL)
    latex = m.group(1).strip() if m else ""
    return {"type": "equation", "latex": latex}, start + 1


def _ptd(lines, start):
    """任务列表：- [ ] / - [x] 连续项合并。"""
    items, i = [], start
    while i < len(lines):
        m = re.match(r'^-\s+\[([ xX])\]\s+(.*)', lines[i].strip())
        if m:
            items.append({"text": m.group(2), "checked": m.group(1) in ('x', 'X')}); i += 1
        else: break
    return {"type": "todo", "items": items}, i
