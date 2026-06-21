#!/usr/bin/env python3
"""Regenerate section index.md files for English tennis-wiki-en."""
import re
from pathlib import Path
from datetime import datetime

DOCS = Path(r"C:\Users\Henry\Documents\tennis-wiki-en\docs")

SECTION_META = {
    'technique': ('🎾', 'Technique', 'Forehand, backhand, serve, volley, footwork — fundamentals to advanced'),
    'biomechanics': ('🦴', 'Biomechanics', 'Kinetic chain, tensegrity, wave theory, proprioception'),
    'tactics': ('🎯', 'Tactics', '70% Rule, 3-shot patterns, serve & volley'),
    'psychology': ('🧠', 'Psychology', 'Pre-performance routine, breathing, pressure management'),
    'fitness': ('🏃', 'Fitness', 'Proprioception programs, spiral chain, age-50+ safety'),
    'players': ('👤', 'Players', 'Analyses of the world\'s top tennis players'),
    'handbooks': ('📚', 'Handbooks', 'Complete handbooks and frameworks'),
    'references': ('📖', 'References', 'Wave theory, biomechanics, advanced methodology'),
    'system': ('⚙️', 'System', 'Tennis Control System, ranking systems, integrated frameworks'),
}

for section, (emoji, title, desc) in SECTION_META.items():
    d = DOCS / section
    if not d.exists():
        d.mkdir(parents=True, exist_ok=True)
    md_files = sorted([f for f in d.iterdir() if f.suffix == '.md' and f.name != 'index.md'])
    # Sort by title
    def sort_key(f):
        try:
            raw = f.read_text(encoding='utf-8', errors='replace')[:500]
            if raw.startswith('---\n'):
                end = raw.find('\n---\n', 4)
                if end > 0:
                    fm = raw[4:end]
                    m = re.search(r'^title:\s*"?(.+?)"?$', fm, re.MULTILINE)
                    if m:
                        return m.group(1).lower()
            return f.stem.lower()
        except Exception:
            return f.stem.lower()
    md_files = sorted(md_files, key=sort_key)

    lines = [
        f'# {emoji} {title}',
        '',
        f'*{desc}*',
        '',
        f'**Total articles:** {len(md_files)}',
        '',
        '## Article list',
        '',
    ]
    for f in md_files:
        try:
            raw = f.read_text(encoding='utf-8', errors='replace')
            title_hint = None
            body = raw
            if body.startswith('---\n'):
                end = body.find('\n---\n', 4)
                if end > 0:
                    body = body[end + 5:]
            for ln in body.split('\n'):
                m = re.match(r'^#\s+(.+)$', ln)
                if m:
                    title_hint = m.group(1).strip()
                    break
            display = title_hint or f.stem.replace('-', ' ').title()
        except Exception:
            display = f.stem.replace('-', ' ').title()
        lines.append(f'- [{display}]({f.name})')
    (d / 'index.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f"  {section:15s} → {len(md_files)} articles")

print(f"\nDone")
