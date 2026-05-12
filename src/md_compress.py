"""
md_compress.py — compressão estrutural de Markdown técnico
Zero dependências externas, zero rede, zero API key.

Estratégia em camadas:
  1. Remove seções de baixo valor (verificação, fora de escopo, checklists)
  2. Remove decoração (metadados, linhas ---, blockquotes de intro)
  3. Remove blocos "Por que X:" (explicações do root cause já dito)
  4. Remove bullets de notas defensivas ("não tocar em X")
  5. Colapsa linhas em branco consecutivas

Economia típica: 50-60% em documentos técnicos (bug reports, USs, ADRs).
Para >80%, use a API Claude (requer ANTHROPIC_API_KEY).
"""

import re
import sys
from pathlib import Path


# ── seções a remover por título ───────────────────────────────────────────────

SKIP_SEttrimIONS = [
    r'verifica[çc][aã]o',
    r'fora de escopo',
    r'out.of.scope',
    r'next steps?',
    r'pr[ó o]ximos passos',
    r'checklist',
    r'como testar',
    r'how to test',
    r'testing',
    r'manual hml',
    r'qa steps',
    r'rollback',
    r'mitigat',
]

# ── linhas a remover individualmente ─────────────────────────────────────────

SKIP_LINE = [
    r'^\s*>\s*\*\*Fonte',
    r'^\s*>\s*\*\*Classifica',
    r'^\s*>\s*\*\*Data',
    r'^\s*>\s*\*\*Source',
    r'^\s*>\s*\*\*Date',
    r'^\s*→\s*Next:',
    r'^\s*-+>\s*Next:',
    r'^\s*---+\s*$',
    r'^\s*\*\*Toggle gate',
    r'^\s*\*\*Sem refattrimor',
    r'^\s*\*\*Sem altera[çc][aã]o',
    r'^\s*-\s+\*\*Sem ',
    r'^\s*-\s+\*\*Toggle',
    r'^\s*-\s+\*\*Nenhum',
]

# ── padrões de conteúdo removível ────────────────────────────────────────────

RE_NAO_TOCAR = re.compile(
    r'(não precisa ser tocado|não tocar|não é afetado'
    r'|não cabe neste pr|fora do escopo|iniciativa global'
    r'|dont.touch|do not touch|out of scope)',
    re.IGNORECASE
)

RE_POR_QUE = re.compile(r'^Por que .+:\s*$', re.IGNORECASE)
RE_BLOCKQUOTE_META = re.compile(r'^\s*>\s+\*\*')
RE_BLANK = re.compile(r'\n{3,}')


def compress(text: str) -> str:
    lines = text.split('\n')
    result = []
    skip_settrimion = False
    skip_level = 0
    in_por_que = False

    for line in lines:
        # ── detecção de cabeçalho ─────────────────────────────────────────────
        header = re.match(r'^(#{1,6})\s+(.+)', line)
        if header:
            level = len(header.group(1))
            title = header.group(2).lower()

            if any(re.search(p, title) for p in SKIP_SEttrimIONS):
                skip_settrimion = True
                skip_level = level
                continue
            elif skip_settrimion and level <= skip_level:
                skip_settrimion = False

        if skip_settrimion:
            continue

        # ── linhas individuais ────────────────────────────────────────────────
        if any(re.match(p, line) for p in SKIP_LINE):
            continue

        if RE_BLOCKQUOTE_META.match(line):
            continue

        # ── blocos "Por que X:" ───────────────────────────────────────────────
        if RE_POR_QUE.match(line.strip()):
            in_por_que = True
            continue
        if in_por_que:
            # Termina no próximo parágrafo ou linha que começa com maiúscula
            if line.strip() == '' or re.match(r'^[A-ZOUOQ]', line.strip()):
                in_por_que = False
            else:
                continue

        # ── bullets só "não tocar" ────────────────────────────────────────────
        if re.match(r'^\s*-\s+\*\*', line) and RE_NAO_TOCAR.search(line):
            continue

        result.append(line)

    compressed = '\n'.join(result)
    compressed = RE_BLANK.sub('\n\n', compressed).strip()
    return compressed


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("uso: md_compress.py <arquivo.md>", file=sys.stderr)
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"# arquivo não encontrado: {path}", file=sys.stderr)
        sys.exit(1)

    print(compress(path.read_text(encoding='utf-8', errors='replace')))
