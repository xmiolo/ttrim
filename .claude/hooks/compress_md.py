#!/usr/bin/env python3
"""
PreToolUse hook — intercepts Read calls for .md files and redirects
to a compressed version produced by md_compress.compress().

Bypass:  include --no-compress anywhere in your message
Stats:   include --metrics anywhere in your message
"""
import json
import os
import sys
import tempfile
from pathlib import Path


_FLAG_BYPASS  = '/tmp/.ttrim_no_compress'
_FLAG_METRICS = '/tmp/.ttrim_metrics'


def _find_compress_module() -> Path | None:
    # 1. sibling: .claude/hooks/ → ../../src/md_compress.py
    here = Path(__file__).resolve().parent
    candidate = here.parent.parent / 'src' / 'md_compress.py'
    if candidate.exists():
        return candidate

    # 2. installed copy
    install_dir = Path(os.environ.get('TOKEN_TRIM_HOME', Path.home() / '.token-trim'))
    candidate = install_dir / 'src' / 'md_compress.py'
    if candidate.exists():
        return candidate

    return None


def _load_compress(path: Path):
    import importlib.util
    spec = importlib.util.spec_from_file_location('md_compress', path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _count_tokens(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.get_encoding('cl100k_base')
        return len(enc.encode(text))
    except Exception:
        import re
        return len(re.findall(r'\w+|[^\w\s]', text))


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    file_path = data.get('tool_input', {}).get('file_path', '')

    if not file_path.lower().endswith(('.md', '.markdown')):
        sys.exit(0)

    # bypass flags
    if os.path.exists(_FLAG_BYPASS):
        sys.exit(0)
    if os.environ.get('TTRIM_NO_COMPRESS', '').lower() in ('1', 'true', 'yes'):
        sys.exit(0)

    if not os.path.exists(file_path):
        sys.exit(0)

    compress_path = _find_compress_module()
    if compress_path is None:
        sys.exit(0)

    try:
        mod      = _load_compress(compress_path)
        original = Path(file_path).read_text(encoding='utf-8', errors='replace')
        compressed = mod.compress(original)

        tmp = tempfile.NamedTemporaryFile(
            mode='w', suffix='_ttrim.md', delete=False, encoding='utf-8'
        )
        tmp.write(compressed)
        tmp.close()

        output: dict = {
            'hookSpecificOutput': {
                'hookEventName': 'PreToolUse',
                'updatedInput': {'file_path': tmp.name},
            }
        }

        show = (
            os.path.exists(_FLAG_METRICS)
            or os.environ.get('TTRIM_METRICS', '').lower() in ('1', 'on', 'true')
        )
        if show:
            orig_t = _count_tokens(original)
            comp_t = _count_tokens(compressed)
            saved  = orig_t - comp_t
            pct    = int(saved / orig_t * 100) if orig_t else 0
            output['systemMessage'] = (
                f'[ttrim] {Path(file_path).name}: '
                f'{orig_t} → {comp_t} tokens ({saved} saved, {pct}% reduction)'
            )

        print(json.dumps(output))

    except Exception:
        sys.exit(0)


main()
