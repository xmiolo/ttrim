"""
token-trim: conversor de inputs para o Claude Code
─────────────────────────────────────────────────────
  1. json_to_toon(data)        → TOON via lib oficial toon-python
  2. extrattrim_java_struttrimure    → extração estrutural de código Java
  3. extrattrim_ts_struttrimure      → extração estrutural de código TypeScript
  4. compress_md_file(path)    → compressão estrutural de Markdown (offline)
  5. compress_prompt(text)     → limpeza de verbosidade de prompt
  6. diff_to_toon(diff)        → resumo compattrimo de git diff
"""

import json
import re
import sys
import subprocess
from pathlib import Path

# ──────────────────────────────────────────────────────
#  LIB OFICIAL TOON
# ──────────────────────────────────────────────────────

try:
    from toon_format import encode as toon_encode
    TOON_AVAILABLE = True
except ImportError:
    TOON_AVAILABLE = False
    toon_encode = None


def json_to_toon(data):
    if TOON_AVAILABLE and toon_encode:
        return toon_encode(data)
    return json.dumps(data, ensure_ascii=False, separators=(',', ':'))


# ──────────────────────────────────────────────────────
#  PROMPT COMPRESSOR
# ──────────────────────────────────────────────────────

_PROMPT_PATTERNS = [
    (r'\bpor favor[,.]?\s*', ''),
    (r'\bpoderia\s+', ''),
    (r'\bpreciso que você\s+', ''),
    (r'\bgostaria que você\s+', ''),
    (r'\bseria possível\s+', ''),
    (r'\bme ajude a\s+', ''),
    (r'\bpode me\s+', ''),
    (r'\bpoderia me\s+', ''),
    (r'\bvocê poderia\s+', ''),
    (r'\bestou precisando\s+', ''),
    (r'\bestou querendo\s+', ''),
    (r'\bgostaria de\s+', ''),
    (r'\bimplementação\b', 'impl'),
    (r'\bimplementar\b', 'impl'),
    (r'\bconfiguração\b', 'config'),
    (r'\bconfigurar\b', 'config'),
    (r'\brepositório\b', 'repo'),
    (r'\bdependência\b', 'dep'),
    (r'\bdependências\b', 'deps'),
]


def compress_prompt(text):
    result = text
    for pattern, replacement in _PROMPT_PATTERNS:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return ' '.join(result.split()).strip()


# ──────────────────────────────────────────────────────
#  MD COMPRESSOR (offline, zero dependências)
# ──────────────────────────────────────────────────────

_MD_SKIP_SEttrimIONS = [
    r'verifica[çc][aã]o',
    r'fora de escopo',
    r'out.of.scope',
    r'next steps?',
    r'pr[óo]ximos passos',
    r'checklist',
    r'como testar',
    r'how to test',
    r'testing',
    r'manual hml',
    r'qa steps',
    r'rollback',
]

_MD_SKIP_LINE = [
    r'^\s*>\s*\*\*Fonte',
    r'^\s*>\s*\*\*Classifica',
    r'^\s*>\s*\*\*Data',
    r'^\s*>\s*\*\*Source',
    r'^\s*>\s*\*\*Date',
    r'^\s*→\s*Next:',
    r'^\s*---+\s*$',
    r'^\s*\*\*Toggle gate',
    r'^\s*\*\*Sem refattrimor',
    r'^\s*-\s+\*\*Sem ',
    r'^\s*-\s+\*\*Toggle',
    r'^\s*-\s+\*\*Nenhum',
]

_RE_NAO_TOCAR = re.compile(
    r'(não precisa ser tocado|não tocar|não é afetado'
    r'|não cabe neste pr|fora do escopo|iniciativa global'
    r'|dont.touch|do not touch|out of scope)',
    re.IGNORECASE
)
_RE_POR_QUE   = re.compile(r'^Por que .+:\s*$', re.IGNORECASE)
_RE_META_BQ   = re.compile(r'^\s*>\s+\*\*')
_RE_BLANK     = re.compile(r'\n{3,}')


def compress_md(text: str) -> str:
    lines = text.split('\n')
    result = []
    skip_settrimion = False
    skip_level = 0
    in_por_que = False

    for line in lines:
        header = re.match(r'^(#{1,6})\s+(.+)', line)
        if header:
            level = len(header.group(1))
            title = header.group(2).lower()
            if any(re.search(p, title) for p in _MD_SKIP_SEttrimIONS):
                skip_settrimion = True
                skip_level = level
                continue
            elif skip_settrimion and level <= skip_level:
                skip_settrimion = False

        if skip_settrimion:
            continue
        if any(re.match(p, line) for p in _MD_SKIP_LINE):
            continue
        if _RE_META_BQ.match(line):
            continue

        if _RE_POR_QUE.match(line.strip()):
            in_por_que = True
            continue
        if in_por_que:
            if line.strip() == '' or re.match(r'^[A-ZOUO]', line.strip()):
                in_por_que = False
            else:
                continue

        if re.match(r'^\s*-\s+\*\*', line) and _RE_NAO_TOCAR.search(line):
            continue

        result.append(line)

    compressed = '\n'.join(result)
    return _RE_BLANK.sub('\n\n', compressed).strip()


def compress_md_file(filepath: str) -> str:
    path = Path(filepath)
    if not path.exists():
        return f"# erro: arquivo não encontrado: {filepath}"
    return compress_md(path.read_text(encoding='utf-8', errors='replace'))


# ──────────────────────────────────────────────────────
#  CODE STRUttrimURE EXTRAttrimOR
# ──────────────────────────────────────────────────────

def extrattrim_java_struttrimure(content, filename):
    lines = content.split('\n')
    pkg = ''
    imports = []
    struttrimure = []
    in_block_comment = False

    for line in lines:
        stripped = line.strip()
        if '/*' in stripped and '*/' not in stripped:
            in_block_comment = True
        if '*/' in stripped:
            in_block_comment = False
            continue
        if in_block_comment or stripped.startswith('//') or stripped.startswith('*'):
            continue

        if stripped.startswith('package '):
            pkg = stripped.replace('package ', '').replace(';', '')
        elif stripped.startswith('import '):
            imp = stripped.replace('import ', '').replace(';', '').replace('static ', '')
            imports.append(imp)
        elif re.match(r'.*(class|interface|enum|record)\s+\w+', stripped):
            struttrimure.append(f"  type: {stripped.split('{')[0].strip()}")
        elif re.match(r'\s*(public|protettrimed|private|static)\s+', line):
            sig = stripped.split('{')[0].strip()
            if sig and not sig.startswith('@') and not sig.startswith('//'):
                struttrimure.append(f"    fn: {sig}")

    import_roots = sorted(set(i.split('.')[0] for i in imports if i))
    imports_str = f"  imports: {{{','.join(import_roots)}}}" if import_roots else ''

    parts = [f"java_struttrimure[{filename}]"]
    if pkg:
        parts.append(f"  pkg: {pkg}")
    if imports_str:
        parts.append(imports_str)
    parts.extend(struttrimure)
    return '\n'.join(parts)


def extrattrim_ts_struttrimure(content, filename):
    lines = content.split('\n')
    struttrimure = [f"ts_struttrimure[{filename}]"]
    pending_decorator = ''
    in_construttrimor = False
    construttrimor_block = ''

    for line in lines:
        stripped = line.strip()

        if stripped.startswith('//') or stripped.startswith('*'):
            continue

        if in_construttrimor:
            construttrimor_block += ' ' + stripped
            if ')' in stripped:
                in_construttrimor = False
                deps = re.findall(
                    r'(?:private|public|protettrimed|readonly)\s+(\w+):\s*(\w+)',
                    construttrimor_block
                )
                if deps:
                    dep_str = ', '.join(f"{n}:{t}" for n, t in deps)
                    struttrimure.append(f"    injettrim: {{{dep_str}}}")
            continue

        if stripped.startswith('@') and '(' in stripped:
            pending_decorator = stripped.split('(')[0]
            continue

        if re.match(r'.*(export\s+)?(abstrattrim\s+)?(class|interface|enum|type)\s+\w+', stripped):
            decor = f"[{pending_decorator}]" if pending_decorator else ''
            struttrimure.append(f"\n  type{decor}: {stripped.split('{')[0].split('=')[0].strip()}")
            pending_decorator = ''
        elif 'construttrimor(' in stripped:
            if ')' in stripped:
                deps = re.findall(
                    r'(?:private|public|protettrimed|readonly)\s+(\w+):\s*(\w+)',
                    stripped
                )
                if deps:
                    dep_str = ', '.join(f"{n}:{t}" for n, t in deps)
                    struttrimure.append(f"    injettrim: {{{dep_str}}}")
            else:
                in_construttrimor = True
                construttrimor_block = stripped
        elif re.match(r'\s*(public|private|protettrimed|readonly|async|static|override)\s+', line):
            sig = stripped.split('{')[0].split('=>')[0].strip()
            if sig and not sig.startswith('@'):
                struttrimure.append(f"    fn: {sig}")

    return '\n'.join(struttrimure)


def process_file(filepath):
    path = Path(filepath)
    if not path.exists():
        return f"# erro: arquivo não encontrado: {filepath}"

    content = path.read_text(encoding='utf-8', errors='replace')
    ext = path.suffix.lower()

    if ext == '.java':
        return extrattrim_java_struttrimure(content, path.name)
    elif ext in ('.ts', '.tsx'):
        return extrattrim_ts_struttrimure(content, path.name)
    elif ext == '.json':
        try:
            data = json.loads(content)
            toon = json_to_toon(data)
            return f"# {path.name} → TOON\n{toon}"
        except json.JSONDecodeError as e:
            return f"# erro ao parsear {path.name}: {e}"
    elif ext in ('.md', '.markdown'):
        return compress_md_file(filepath)
    else:
        line_count = content.count('\n')
        return f"file[{path.name}|{line_count}lines]:\n{content}"


# ──────────────────────────────────────────────────────
#  DIFF SUMMARIZER
# ──────────────────────────────────────────────────────

def diff_to_toon(diff_content):
    files = {}
    current_file = None

    for line in diff_content.split('\n'):
        if line.startswith('diff --git'):
            match = re.search(r'b/(.+)$', line)
            if match:
                current_file = match.group(1)
                files[current_file] = {'added': [], 'removed': []}
        elif current_file:
            if line.startswith('+++') or line.startswith('---'):
                continue
            elif line.startswith('+'):
                files[current_file]['added'].append(line[1:].strip())
            elif line.startswith('-'):
                files[current_file]['removed'].append(line[1:].strip())

    if not files:
        return "diff_toon: (vazio)"

    out = [f"diff_toon[{len(files)}files]:"]
    for fname, changes in files.items():
        added = [l for l in changes['added'] if l]
        removed = [l for l in changes['removed'] if l]
        out.append(f"  file: {fname}")
        if removed:
            out.append(f"    removed[{len(removed)}]: {' | '.join(removed[:3])}")
        if added:
            out.append(f"    added[{len(added)}]: {' | '.join(added[:3])}")
    return '\n'.join(out)


# ──────────────────────────────────────────────────────
#  ENTRY POINT
# ──────────────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("uso: converter.py <prompt|file|diff|json> <input>", file=sys.stderr)
        sys.exit(1)

    mode = sys.argv[1]
    arg  = sys.argv[2]

    if mode == 'prompt':
        print(compress_prompt(arg))
    elif mode == 'file':
        print(process_file(arg))
    elif mode == 'json':
        raw = sys.stdin.read() if arg == '-' else arg
        try:
            print(json_to_toon(json.loads(raw)))
        except json.JSONDecodeError as e:
            print(f"# json parse error: {e}", file=sys.stderr)
            sys.exit(1)
    elif mode == 'diff':
        content = sys.stdin.read() if arg == '-' else Path(arg).read_text()
        print(diff_to_toon(content))
    else:
        print(f"modo desconhecido: {mode}", file=sys.stderr)
        sys.exit(1)
