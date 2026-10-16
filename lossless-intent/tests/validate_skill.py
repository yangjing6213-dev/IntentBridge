#!/usr/bin/env python3
"""Read-only checks for this package. No AI calls, installation, or deletion.
Uses Python 3 standard library. This checks the emitted metadata subset,
not the complete YAML grammar or model behavior.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

REQUIRED = {
    'SKILL.md', 'README.md', 'agents/openai.yaml',
    'references/protocol.md', 'references/examples-and-lessons.md',
    'assets/consensus-template.md', 'tests/acceptance-cases.json',
    'tests/README.md', 'tests/validate_skill.py',
}
CORE_PHRASES = {
    '自动启动及明确任务绕过': ['默认自动介入', '明确任务直接'],
    '整体与局部': ['整体小样', '一个主要分歧'],
    '有范围的确认': ['局部认可', '默认模式'],
    '非互斥选项': ['组合', '全部否定'],
    '反馈分类': ['理解错误', '需求变化', '执行失败'],
    '停止及回放': ['不固定轮数', '整体回放'],
    '权限与隐私': ['不能上传', '安全规则', '敏感信息'],
    '能力及事实边界': ['未验证', '文字示意'],
    '交接及局部恢复': ['共识', '重大变化'],
}

def run_checks(root: Path) -> dict:
    results: list[dict] = []
    def check(label: str, ok: bool, detail: str = '') -> None:
        results.append({'check': label, 'status': 'PASS' if ok else 'FAIL', 'detail': detail})
    check('package directory', root.is_dir(), str(root))
    if not root.is_dir():
        return {'scope': 'STATIC_ONLY', 'status': 'FAIL', 'checks': results}
    entries = list(root.rglob('*'))
    files = {p.relative_to(root).as_posix(): p for p in entries if p.is_file()}
    missing = sorted(REQUIRED - files.keys())
    check('required files', not missing, ', '.join(missing) or 'all required files present')
    check('no symlinks', not any(p.is_symlink() for p in entries))
    unexpected = sorted(set(files) - REQUIRED - {'MANIFEST.sha256'})
    check('no unexpected package files', not unexpected, ', '.join(unexpected))
    texts = {}
    bad_encoding = []
    for name, p in files.items():
        try:
            raw = p.read_bytes()
            text = raw.decode('utf-8')
            if raw.startswith(b'\xef\xbb\xbf'):
                raise ValueError('BOM not expected')
            texts[name] = text
        except (UnicodeDecodeError, ValueError):
            bad_encoding.append(name)
    check('UTF-8 without BOM', not bad_encoding, ', '.join(bad_encoding))
    core = texts.get('SKILL.md', '')
    match = re.match(r'\A---\n(.*?)\n---\n', core, re.S)
    check('frontmatter delimiters', match is not None)
    if match:
        fm = match.group(1)
        n = re.search(r'^name: ([a-z0-9]+(?:-[a-z0-9]+)*)$', fm, re.M)
        name = n.group(1) if n else ''
        check('skill name and folder', 1 <= len(name) <= 64 and name == root.name, name)
        d = re.search(r'^description: (".*")$', fm, re.M)
        try:
            description = json.loads(d.group(1)) if d else ''
        except (ValueError, TypeError):
            description = ''
        check('description format and length', isinstance(description,str) and 1 <= len(description) <= 1024)
        check('trigger description', description.startswith('Use when') and '无损传达' in description)
        check('metadata version', 'version: "1.0.0"' in fm)
        check('no tool preapproval', 'allowed-tools:' not in fm and 'disable-model-invocation:' not in fm)
    check('core under 500 lines', bool(core) and len(core.splitlines()) < 500, str(len(core.splitlines())))
    check('balanced fenced code blocks', bool(core) and sum(l.startswith('```') for l in core.splitlines()) % 2 == 0)
    policy = texts.get('agents/openai.yaml','')
    check('Codex allows implicit invocation', bool(re.search(r'^  allow_implicit_invocation: true$',policy,re.M)))
    check('display name and explicit invocation', 'display_name: "无损传达 Skill"' in policy and '$lossless-intent' in policy)
    broken = []
    for name, text in texts.items():
        if not name.endswith('.md'):
            continue
        for target in re.findall(r'\[[^\]]*\]\(([^\s)]+)\)',text):
            if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',target) or target.startswith('#'):
                continue
            path = (files[name].parent / unquote(target.split('#',1)[0])).resolve()
            if not path.is_relative_to(root.resolve()) or not path.exists():
                broken.append(name + ' -> ' + target)
    check('local Markdown links', not broken, '; '.join(broken))
    for label, phrases in CORE_PHRASES.items():
        check('rule coverage: '+label, all(p in core for p in phrases))
    try:
        suite = json.loads(texts.get('tests/acceptance-cases.json','{}'))
        cases = suite.get('cases',[])
        ids = [c.get('id') for c in cases]
        valid = len(cases) >= 20 and len(set(ids)) == len(ids)
        valid = valid and all(c.get('messages') and c.get('expected') and c.get('failure_signals') for c in cases)
        check('behavioral case structure', bool(valid), str(len(cases))+' cases')
        check('behavioral status remains unclaimed', suite.get('run_status') == 'NOT_RUN' and all(c.get('status') == 'NOT_RUN' for c in cases))
    except (ValueError, TypeError, AttributeError):
        check('behavioral case structure',False,'invalid JSON or case structure')
    secrets = []
    for name,text in texts.items():
        if name.endswith('.py'):
            continue
        if re.search(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\bsk-[A-Za-z0-9_-]{24,}',text):
            secrets.append(name)
    check('basic secret-pattern scan',not secrets,', '.join(secrets) or 'not a comprehensive security audit')
    manifest = texts.get('MANIFEST.sha256')
    if manifest is not None:
        lines = [l for l in manifest.splitlines() if l.strip()]
        listed = {}
        errors=[]
        for line in lines:
            m=re.fullmatch(r'([0-9a-f]{64})  (.+)',line)
            if not m:
                errors.append('invalid manifest line'); continue
            digest, name=m.groups()
            if name in listed: errors.append('duplicate '+name)
            listed[name]=digest
            if name not in files or hashlib.sha256(files[name].read_bytes()).hexdigest()!=digest:
                errors.append('mismatch '+name)
        if set(listed)!=set(files)-{'MANIFEST.sha256'}:
            errors.append('manifest file set differs')
        check('SHA-256 manifest',not errors,'; '.join(errors))
    status='PASS' if all(c['status']=='PASS' for c in results) else 'FAIL'
    return {'scope':'STATIC_ONLY','status':status,'check_count':len(results),'checks':results,
            'behavioral_tests':'NOT_RUN','host_installation':'NOT_RUN'}

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', nargs='?', type=Path, default=Path(__file__).resolve().parent.parent)
    args=parser.parse_args()
    result=run_checks(args.root.resolve())
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['status']=='PASS' else 1

if __name__=='__main__':
    sys.exit(main())
