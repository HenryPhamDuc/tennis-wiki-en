#!/usr/bin/env python3
"""
Build the English tennis-wiki site from the English source vault.

Source:  C:/Users/Henry/Documents/MY VAULT/Documents/Obsidian Vault/tennis-vault/Tennis Wiki - English
Target:  C:/Users/Henry/Documents/tennis-wiki-en/

Strategy:
  - All 743 unique .md files (dedup _1 duplicates)
  - Convert [[Wiki Links]] to MkDocs relative links
  - Categorize into English-named subfolders
  - Add YAML frontmatter (English, no Vietnamese translation)
  - Add nav link to Vietnamese site (https://henryphamduc.github.io/tennis/tennis-wiki/)
  - Build site with mkdocs + Material theme (English UI)
"""
import os
import re
import sys
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
from collections import defaultdict

SOURCE = Path(r"C:\Users\Henry\Documents\MY VAULT\Documents\Obsidian Vault\tennis-vault\Tennis Wiki - English")
REPO = Path(r"C:\Users\Henry\Documents\tennis-wiki-en")
DOCS = REPO / "docs"
DOCS.mkdir(parents=True, exist_ok=True)

# English category mapping (from existing tennis-wiki)
CATEGORY_MAP = {
    'Technique': 'technique',          # ky-thuat equivalent
    'Biomechanics': 'biomechanics',
    'Tactics': 'tactics',
    'Psychology': 'psychology',
    'Fitness': 'fitness',
    'Players': 'players',
    'Handbooks': 'handbooks',
    'References': 'references',
    'Wave Theory': 'wave-theory',
    'System': 'system',
}

# Topic keyword classification
TOPIC_KEYWORDS = {
    'technique': ['forehand', 'backhand', 'volley', 'serve', 'return', 'footwork',
                  'split-step', 'overhead', 'slice', 'topspin', 'grip', 'stroke',
                  'kinetic chain', 'whip', 'lag', 'mechanics', 'technique', 'drill'],
    'biomechanics': ['biomechanic', 'kinetic', 'biomechanics', 'kinesiology',
                     'anatomy', 'physiology', 'skeletal', 'muscle', 'tendon',
                     'fascia', 'biotensegrity', 'tensegrity', 'wave', 'sóng',
                     'biomechanical', 'bio-mechanical'],
    'tactics': ['tactic', 'pattern', 'strategy', 'serve-and-volley', '70% rule',
                '75% rule', 'first strike', 'blitz-chess', 'decision tree',
                'winning pattern', 'percentage tennis', 'ranking'],
    'psychology': ['mental', 'psycholog', 'mindset', 'focus', 'concentration',
                   'pressure', 'flow state', 'soft zone', 'choking', 'anxiety',
                   'breathing', 'pre-performance', 'cognitive load', 'retrospective'],
    'fitness': ['fitness', 'conditioning', 'flexibility', 'endurance',
                'recovery', 'injury', 'aging athlete', 'tendon', 'stretch',
                'proprioception', 'spiral chain', 'tai chi', 'thái cực'],
    'players': ['federer', 'nadal', 'djokovic', 'alcaraz', 'sinner', 'rublev',
                'shelton', 'sampras', 'agassi', 'medvedev', 'tsitsipas',
                'wimbledon', 'us open', 'french open', 'roland garros', 'australian open'],
    'handbooks': ['handbook', 'manual', 'framework', 'tfl', 'rpm',
                  'mastery system', '5-year', '12-week', 'modern tennis',
                  'golf', 'pitching'],
    'wave-theory': ['wave', 'sóng', 'standing wave', 'spatial wave',
                    'wave transmission', 'wave field', 'wave theory'],
    'system': ['system', 'framework', 'control system', 'tfl',
               'ranking system', 'elo', 'integrated'],
}

# Stop words to ignore
STOP = {'the', 'and', 'for', 'with', 'from', 'how', 'your', 'into', 'all',
        'new', 'top', 'best', 'guide', 'one', 'two', 'three', 'introduction',
        'part', 'chapter', 'tips', 'plan', 'level', 'modern', 'advanced',
        'volume', 'session', 'training', 'practice', 'tactic', 'tactic-',
        'openweb', 'gemini', 'chatgpt', 'claude', 'ollama', 'grok', 'meta',
        'openai', 'pdf', 'docx', 'image', 'photo', 'magazine', 'issue',
        'edition', 'library'}


def slugify(text):
    """Make URL/filesystem-safe slug."""
    text = re.sub(r'[\\/*?:"<>|]', '', text)
    text = re.sub(r'[\s_]+', '-', text.strip())
    text = re.sub(r'-{2,}', '-', text)
    return text.strip('-').lower()


def categorize(name, content):
    """Determine category from name + content."""
    text = (name + ' ' + content).lower()
    scores = defaultdict(int)
    for cat, kws in TOPIC_KEYWORDS.items():
        for kw in kws:
            if kw in text:
                scores[cat] += 1
    if not scores:
        return 'references'
    # Highest score
    return max(scores.items(), key=lambda x: x[1])[0]


def extract_title(text, fallback):
    """Extract clean H1 from source."""
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("# "):
            t = line[2:].strip()
            t = re.sub(r"^(chapter|chương|chuong)\s*\d+[:\.\-]\s*", "", t, flags=re.IGNORECASE)
            if t and len(t) < 200:
                return t
    return fallback


def main():
    # 1. Find all unique .md files (dedup _1)
    print("=== Loading source files ===")
    all_files = sorted([p for p in SOURCE.glob("*.md") if p.is_file()])
    print(f"  Total: {len(all_files)}")

    # Hash for dedup
    seen_hash = {}
    unique_files = []
    for p in all_files:
        try:
            text = p.read_text(encoding='utf-8', errors='replace')
            norm = re.sub(r'\s+', ' ', text).strip()
            h = hashlib.md5(norm.encode('utf-8', errors='ignore')).hexdigest()
            if h in seen_hash:
                continue
            seen_hash[h] = p
            unique_files.append(p)
        except Exception as e:
            print(f"  err: {p}: {e}")

    print(f"  Unique after dedup: {len(unique_files)}")

    # 2. Build page index for wiki-link resolution
    print("=== Building page index ===")
    page_index = {}
    for p in unique_files:
        try:
            text = p.read_text(encoding='utf-8', errors='replace')
            # Strip frontmatter if any
            if text.startswith('---\n'):
                end = text.find('\n---\n', 4)
                if end > 0:
                    text = text[end + 5:]
            title = extract_title(text, p.stem)
            slug = slugify(p.stem)
            cat = categorize(p.stem, text)
            page_index[slug] = {
                'title': title,
                'source': str(p),
                'category': cat,
            }
        except Exception as e:
            print(f"  err indexing: {p}: {e}")
    print(f"  Indexed {len(page_index)} pages")

    # 3. Process each file
    print("=== Converting files ===")
    written = []
    for i, p in enumerate(unique_files, 1):
        try:
            text = p.read_text(encoding='utf-8', errors='replace')
            # Strip existing frontmatter
            body = text
            if body.startswith('---\n'):
                end = body.find('\n---', 4)
                if end > 0:
                    body = body[end + 4:].lstrip('\n')

            # Get title + slug
            title = extract_title(body, p.stem.replace('-', ' ').title())
            slug = slugify(p.stem)

            # Category
            cat = page_index[slug]['category']

            # Rewrite wiki-links
            def repl(m):
                inner = m.group(1)
                if '|' in inner:
                    target, alias = inner.split('|', 1)
                else:
                    target, alias = inner, None
                # target may have subdir prefix like "tech/foo" or just "foo"
                target_name = os.path.basename(target).replace('.md', '')
                target_slug = slugify(target_name)
                if target_slug in page_index:
                    target_cat = page_index[target_slug]['category']
                    # Use relative path from current file's category
                    if target_cat == cat:
                        # Same category: relative
                        target_path = f"{target_slug}.md"
                    else:
                        # Different category: go up + into
                        target_path = f"../{target_cat}/{target_slug}.md"
                    display = alias if alias else target_name
                    return f'[{display}]({target_path})'
                else:
                    return f'_{target_name}_'
            body = re.sub(r'\[\[([^\]]+)\]\]', repl, body)

            # Rewrite image embeds
            body = re.sub(
                r'!\[\[([^\]]+)\]\]',
                lambda m: f'![{os.path.basename(m.group(1).split("|")[0])}](images/{os.path.basename(m.group(1).split("|")[0])}){{ .missing-image }}',
                body,
            )

            # YAML frontmatter (English)
            fm_lines = ['---']
            fm_lines.append(f'title: "{title}"')
            fm_lines.append('language: en')
            fm_lines.append('vault: Tennis Wiki-English')
            fm_lines.append(f'category: "{cat}"')
            fm_lines.append(f'created: {datetime.now().strftime("%Y-%m-%d")}')
            fm_lines.append('---')
            frontmatter = '\n'.join(fm_lines) + '\n\n'

            # Cross-link to Vietnamese site
            vn_link = '\n---\n\n> 🌐 **[Read in Tiếng Việt](https://henryphamduc.github.io/tennis/tennis-wiki/)** — Vietnamese version of this wiki\n\n'

            full = frontmatter + body + vn_link

            out_path = DOCS / cat / f'{slug}.md'
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(full, encoding='utf-8')
            written.append((slug, cat, out_path))
            if i % 100 == 0 or i == len(unique_files):
                print(f"  [{i}/{len(unique_files)}] processed", flush=True)
        except Exception as e:
            print(f"  err: {p.name}: {e}")

    # 4. Stats
    from collections import Counter
    cat_count = Counter(w[1] for w in written)
    print(f"\n=== Summary ===")
    print(f"  Written: {len(written)}")
    for cat, count in cat_count.most_common():
        print(f"    {cat:20s} {count:3d}")

    # Save index
    import json
    with open(REPO / 'page_index.json', 'w', encoding='utf-8') as f:
        json.dump([{'slug': s, 'category': c, 'path': str(p)} for s, c, p in written], f, ensure_ascii=False, indent=2)
    print(f"\n  page_index.json saved ({len(written)} entries)")

    return written


if __name__ == "__main__":
    main()
