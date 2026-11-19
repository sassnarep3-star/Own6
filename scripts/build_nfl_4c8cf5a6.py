#!/usr/bin/env python3
'''Build the nfl-4c8cf5a6 pack site: GitHub Pages pages from committed CSVs.

Deterministic: no network, no arguments that change output. A re-run must
produce byte-identical files (asserted by tests). Data CSVs are committed;
this script only renders them.

Usage
-----
    python3 scripts/build_nfl_4c8cf5a6.py            # write HTML pages
    python3 scripts/build_nfl_4c8cf5a6.py --check    # build, then run the verifier
'''
from __future__ import annotations

import argparse
import csv
import html
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, 'data', 'nfl_4c8cf5a6')
DOCS = os.path.join(REPO, 'docs', 'nfl-4c8cf5a6')
DQ = chr(34)
AP = chr(39)
US = chr(95)
SP = chr(32)
MONO = 'mono'
SRC = 'source'
BLANK = 'blank'
NOTE = 'note'

NAV = [
    ('index.html', 'Decision readiness'),
    ('requirements.html', 'Requirements'),
    ('gates.html', 'Gates'),
    ('questions.html', 'Questions & answers'),
    ('gaps.html', 'Information gaps'),
    ('suggestions.html', 'Suggestions'),
    ('strategies.html', 'Strategies'),
    ('leaderboard.html', 'Leaderboard'),
    ('price-snapshot.html', 'Price snapshot store'),
    ('results-feed.html', 'Verified results feed'),
    ('originated-lines.html', 'Originated lines'),
    ('depth.html', 'Depth & availability'),
    ('injuries.html', 'Injuries'),
    ('correlations.html', 'Correlations & luck'),
    ('validation.html', 'Validation gates'),
    ('snapshot-ledger.html', 'Snapshot ledger'),
    ('flagged.html', 'Flagged for review'),
    ('sources.html', 'Sources & reads'),
    ('repo-review.html', 'Repo review'),
    ('executive-summary.html', 'Executive summary'),
]

CSS = '''
:root{--bg:#f6f7f9;--card:#ffffff;--ink:#1a1d21;--muted:#5f6672;--line:#e2e5ea;--accent:#1b5e9c;--ok:#1a7f45;--warn:#9a6400;--bad:#a32b2b;--blank:#9aa1ab}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif}
header{background:#10161d;color:#fff;padding:20px 24px}
header h1{margin:0 0 6px;font-size:21px;font-weight:650;letter-spacing:-.2px}
header p{margin:0;color:#b6c0cc;font-size:13px;max-width:1050px}
nav{background:#fff;border-bottom:1px solid var(--line);padding:0 24px;display:flex;flex-wrap:wrap;gap:2px;position:sticky;top:0;z-index:5}
nav a{color:var(--muted);text-decoration:none;font-size:12.5px;padding:11px 10px;border-bottom:2px solid transparent}
nav a:hover{color:var(--ink)}
nav a.on{color:var(--accent);border-bottom-color:var(--accent);font-weight:600}
main{padding:22px 24px 60px;max-width:1400px}
h2{font-size:16px;margin:26px 0 8px;padding-bottom:6px;border-bottom:1px solid var(--line)}
h2:first-child{margin-top:4px}
h3{font-size:14px;margin:18px 0 6px}
p{max-width:1000px;margin:8px 0}
.note{color:var(--muted);font-size:12.5px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(184px,1fr));gap:12px;margin:16px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px 14px}
.card span{display:block;color:var(--muted);font-size:11.5px;text-transform:uppercase;letter-spacing:.4px}
.card strong{display:block;font-size:22px;margin-top:4px;font-weight:650}
.card small{display:block;color:var(--muted);font-size:11.5px;margin-top:3px}
.tw{overflow:auto;border:1px solid var(--line);border-radius:8px;background:var(--card);margin:10px 0 20px;max-height:78vh}
table{border-collapse:collapse;width:100%;font-size:12.5px}
th,td{border-bottom:1px solid var(--line);padding:7px 9px;text-align:left;vertical-align:top}
th{background:#eef1f5;position:sticky;top:0;font-weight:600;white-space:nowrap;z-index:2}
tbody tr:nth-child(even){background:#fafbfc}
tbody tr:hover{background:#f0f5fa}
td a{color:var(--accent);text-decoration:none}
td a:hover{text-decoration:underline}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px}
.blank{color:var(--blank);font-style:italic}
.tag{display:inline-block;padding:1px 7px;border-radius:10px;font-size:11px;font-weight:600;white-space:nowrap}
.t-cleared{background:#e4f5ea;color:var(--ok)}
.t-cleared_repo{background:#eef3f8;color:#2b5a86}
.t-partially{background:#eef0f5;color:#4a5260}
.t-structural{background:#fdf3e0;color:var(--warn)}
.t-blocked{background:#fbe9e9;color:var(--bad)}
.t-open{background:#f1f2f4;color:#5f6672}
.t-rejected{background:#efeaf4;color:#64468a}
.t-needs{background:#fdf3e0;color:var(--warn)}
.t-progress{background:#e6f0f8;color:#1b5e9c}
.t-info{background:#f1f2f4;color:#5f6672}
.t-medium{background:#fdf3e0;color:var(--warn)}
.t-high{background:#fbe9e9;color:var(--bad)}
.t-low{background:#f1f2f4;color:#5f6672}
.t-out{background:#fbe9e9;color:var(--bad)}
.t-questionable{background:#fdf3e0;color:var(--warn)}
.t-doubtful{background:#f3ecf9;color:#64468a}
ul{max-width:1000px}
li{margin:4px 0}
code{background:#eef1f5;padding:1px 5px;border-radius:4px;font-size:12px}
footer{padding:20px 24px;border-top:1px solid var(--line);color:var(--muted);font-size:12px}
footer a{color:var(--accent)}
'''


def esc(x) -> str:
    return html.escape('' if x is None else str(x), quote=False)


def read(name: str) -> list[dict]:
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return []
    with open(path, newline='', encoding='utf-8') as fh:
        return list(csv.DictReader(fh))


def link(url: str, label: str = SRC, blank_label: str = 'no source') -> str:
    url = (url or '').strip()
    if not url:
        return f'<span class={DQ}{BLANK}{DQ}>{esc(blank_label)}</span>'
    return (f'<a href={DQ}{esc(url)}{DQ} rel={DQ}noopener noreferrer{DQ} target={DQ}_blank{DQ}>'
            f'{esc(label)} &#8599;</a>')


def cell(val: str, cls: str = '') -> str:
    v = (val or '').strip()
    if not v:
        return f'<td class={DQ}{BLANK}{DQ}>blank</td>'
    return f'<td class={DQ}{cls}{DQ}>{esc(v)}</td>' if cls else f'<td>{esc(v)}</td>'


def table(header: list[str], rows: list[str]) -> str:
    th = ''.join(f'<th>{esc(h)}</th>' for h in header)
    body_rows = ''.join(rows)
    return (f'<div class={DQ}tw{DQ}><table><thead><tr>{th}</tr></thead>'
            f'<tbody>{body_rows}</tbody></table></div>')


def tag(status: str) -> str:
    s = (status or '').strip().lower()
    key = {'cleared': 'cleared', 'cleared_repo': 'cleared_repo',
           'partially cleared': 'partially', 'structural': 'structural',
           'blocked': 'blocked', 'open': 'open', 'rejected': 'rejected',
           'needs review': 'needs', 'in progress': 'progress', 'info': 'info',
           'medium': 'medium', 'high': 'high', 'low': 'low',
           'declared': 'progress', 'unanswered': 'open',
           'answered': 'cleared'}.get(s, '')
    return f'<span class={DQ}tag t-{key}{DQ}>{esc(status)}</span>' if key else esc(status)


def page(title: str, subtitle: str, body: str, active: str) -> str:
    parts = []
    for href, label in NAV:
        on = f' class={DQ}on{DQ}' if href == active else ''
        parts.append(f'<a href={DQ}{href}{DQ}{on}>{esc(label)}</a>')
    nav = ''.join(parts)
    return f'''<!DOCTYPE html>
<html lang={DQ}en{DQ}><head><meta charset={DQ}utf-8{DQ}>
<meta name={DQ}viewport{DQ} content={DQ}width=device-width, initial-scale=1{DQ}>
<title>{esc(title)} — NFL Decision 4C8CF5A6</title>
<style>{CSS}</style></head><body>
<header><h1>{esc(title)}</h1><p>{esc(subtitle)}</p></header>
<nav>{nav}</nav>
<main>
{body}
</main>
<footer>Research only. No prices, no profitability claim, and no wagers. Statistical validation
can reduce uncertainty; it can never remove luck. Every value on this site was read from the
official page named in its row, inherited from another pack and labelled as a claim, or left
blank and flagged. <a href={DQ}flagged.html{DQ}>Flagged for review &#8599;</a></footer>
</body></html>
'''


def write(name: str, content: str) -> None:
    path = os.path.join(DOCS, name)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(content)
    print(f'wrote docs/nfl-4c8cf5a6/{name}')


# --------------------------------------------------------------------------- builders
def build_index() -> None:
    reqs = read('requirements.csv')
    gates = {g['gate_id']: g for g in read('gates.csv')}
    by_status: dict[str, int] = {}
    for r in reqs:
        by_status[r['status']] = by_status.get(r['status'], 0) + 1
    cards = ''.join(
        f'<div class={DQ}card{DQ}><span>{esc(k)}</span><strong>{v}</strong></div>'
        for k, v in sorted(by_status.items(), key=lambda kv: -kv[1]))
    cards += (
        f'<div class={DQ}card{DQ}><span>requirements</span><strong>{len(reqs)}</strong>'
        f'<small>owner brief</small></div>'
        f'<div class={DQ}card{DQ}><span>gates</span><strong>{len(gates)}</strong>'
        f'<small>each with a clearing number</small></div>')
    rows = []
    for r in reqs:
        g = gates.get(r['blocking_gate'], {})
        rid = r['req_id']
        cat = r['category']
        text = r['requirement_text']
        st = r['status']
        bg = r['blocking_gate']
        cn = r['clearing_number']
        src = r['source_url']
        rows.append(
            '<tr>'
            + cell(rid, MONO)
            + cell(cat)
            + f'<td>{esc(text)}</td>'
            + f'<td>{tag(st)}</td>'
            + cell(bg, MONO)
            + cell(cn)
            + f'<td>{link(src)}</td>'
            + '</tr>')
    body = (f'<p>This is the decision-readiness table the owner asked for: one row per requirement, '
            f'the gate that blocks it, and the number that would clear it. The requirement text is '
            f'the owner{AP}s own wording from the brief. Nothing here is a pack{AP}s idea.</p>'
            f'<div class={DQ}cards{DQ}>{cards}</div>'
            '<h2>Decision readiness — every requirement, the gate that blocks it, '
            'the number that clears it</h2>'
            f'<p class={DQ}note{DQ}>A blank clearing-number cell means the requirement is already cleared. '
            f'A blank gate cell means no gate blocks it. Rows are in the order the owner wrote them. '
            f'Values that cannot be confirmed from an official source are left blank and flagged, '
            f'never inferred.</p>'
            + table(['ID', 'Category', 'Requirement', 'Status', 'Blocking gate',
                     'The number that would clear it', SRC], rows))
    write('index.html', page(
        'NFL decision gate — what blocks each requirement, and what clears it',
        'Session 4c8cf5a6 · every row source-linked, nothing inferred',
        body, 'index.html'))


def build_requirements() -> None:
    reqs = read('requirements.csv')
    rows = []
    for r in reqs:
        rid = r['req_id']
        cat = r['category']
        text = r['requirement_text']
        st = r['status']
        bg = r['blocking_gate']
        cn = r['clearing_number']
        vts = r['verified_this_session']
        note = r['note']
        src = r['source_url']
        rows.append(
            '<tr>'
            + cell(rid, MONO)
            + cell(cat)
            + f'<td>{esc(text)}</td>'
            + f'<td>{tag(st)}</td>'
            + cell(bg, MONO)
            + cell(cn)
            + cell(vts)
            + f'<td>{esc(note)}</td>'
            + f'<td>{link(src)}</td>'
            + '</tr>')
    body = (f'<p>The full register: every requirement from the owner{AP}s brief, the gate that blocks '
            f'it, and the number that would clear it. <em>verified_this_session</em> is populated '
            f'only where the value was read from an official page this session. This session cannot '
            f'reach nfl.com, so verified cells are empty and prior reads are inherited as labelled '
            f'repo claims.</p>'
            + table(['ID', 'Category', 'Requirement', 'Status', 'Blocking gate',
                     'The number that would clear it', 'Verified this session',
                     NOTE, SRC], rows))
    write('requirements.html', page(
        'Requirement register',
        f'{len(reqs)} requirements from the owner{AP}s brief', body, 'requirements.html'))


def build_gates() -> None:
    gates = read('gates.csv')
    rows = []
    for g in gates:
        gid = g['gate_id']
        gname = g['gate_name']
        definition = g['definition']
        state = g['state']
        cn = g['clearing_number']
        co = g['current_observation']
        rows.append('<tr>' + cell(gid, MONO) + cell(gname)
                    + f'<td>{esc(definition)}</td>'
                    + f'<td>{tag(state)}</td>'
                    + cell(cn) + cell(co) + '</tr>')
    body = (f'<p>A gate is a named condition. A gate is only ever closed by the observation written '
            f'in its {DQ}clearing number{DQ} column, which is deliberately measurable so it cannot '
            f'be argued away after the fact.</p>'
            + table(['Gate', 'Name', 'Definition', 'State', 'The number that clears it',
                     'Current observation'], rows))
    write('gates.html', page(
        'Gates',
        'Named conditions, each with the observation that closes it',
        body, 'gates.html'))


def build_questions() -> None:
    qia = read('qia.csv')
    rows = []
    for q in qia:
        qid = q['question_id']
        question = q['question']
        have = q['what_we_have']
        lack = q['what_we_lack']
        answer = q['answer']
        astatus = q['answer_status']
        route = q['discovery_route']
        bg = q['blocking_gate']
        src = q['source_url']
        rows.append(
            '<tr>'
            + cell(qid, MONO)
            + f'<td>{esc(question)}</td>'
            + cell(have)
            + cell(lack)
            + cell(answer)
            + f'<td>{tag(astatus)}</td>'
            + cell(route)
            + cell(bg, MONO)
            + f'<td>{link(src)}</td>'
            + '</tr>')
    answered = sum(1 for q in qia if q['answer_status'].startswith('answered'))
    body = (f'<p>The questions that must be answered before a decision is reasonable: what we have, '
            f'what we lack, the answer, and the route that closes each. <strong>{answered} of '
            f'{len(qia)}</strong> are answered by an official source read in a prior session '
            f'(inherited as a repo claim). The rest are left blank rather than filled in.</p>'
            + table(['ID', 'Question', 'What we have', 'What we lack', 'Answer',
                     'Answer status', 'Discovery route', 'Gate', SRC], rows))
    write('questions.html', page(
        'Questions, information, answers',
        f'{len(qia)} questions with what we have, what we lack, and the route that closes each',
        body, 'questions.html'))


def build_gaps() -> None:
    gaps = read('information_gaps.csv')
    rows = []
    for g in gaps:
        gid = g['gap_id']
        dataset = g['missing_dataset']
        why = g['why_it_blocks']
        route = g['acquisition_route']
        cn = g['clearing_number']
        host = g['official_host']
        status = g['status']
        reqs = g['req_ids_blocked']
        src = g['source_url']
        rows.append(
            '<tr>'
            + cell(gid, MONO)
            + f'<td>{esc(dataset)}</td>'
            + cell(why)
            + cell(route)
            + cell(cn)
            + cell(host, MONO)
            + f'<td>{tag(status)}</td>'
            + cell(reqs, MONO)
            + f'<td>{link(src)}</td>'
            + '</tr>')
    body = ('<p>Every gap carries the exact acquisition route and the number that clears it. '
            f'These are the rows that generate suggestions: what we do not have, and the concrete '
            f'way to go and get it.</p>'
            + table(['ID', 'Missing dataset', 'Why it blocks', 'Acquisition route',
                     'The number that clears it', 'Official host', 'Status',
                     'Requirements blocked', SRC], rows))
    write('gaps.html', page(
        'Information gaps', 'What we do not have, and the route to get it',
        body, 'gaps.html'))


def build_suggestions() -> None:
    sug = read('suggestions.csv')
    opts: dict[str, list[dict]] = {}
    for o in read('suggestion_options.csv'):
        opts.setdefault(o['suggestion_id'], []).append(o)
    rows = []
    for s in sug:
        sid = s['suggestion_id']
        title = s['title']
        improves = s['what_it_improves']
        cat = s['category']
        bg = s['blocking_gate']
        reqs = s['req_ids']
        dec_lbl = 'owner decides — blank by design'
        rows.append(
            '<tr>'
            + cell(sid, MONO)
            + f'<td><strong>{esc(title)}</strong><br>'
            f'<span class={DQ}{NOTE}{DQ}>{esc(improves)}</span></td>'
            + cell(cat)
            + cell(bg, MONO)
            + cell(reqs, MONO)
            + f'<td class={DQ}{BLANK}{DQ}>{dec_lbl}</td>'
            + '</tr>')
    body = (f'<h2>Suggestions — review before implementing</h2>'
            f'<p>Each suggestion carries two or more option paths below. The <strong>decision column '
            f'is deliberately blank</strong>: the whole point of this section is that the owner '
            f'chooses a path before anything is built. Nothing on this page has been implemented.</p>'
            + table(['ID', 'Suggestion', 'Category', 'Blocking gate', 'Requirements',
                     'Owner decision'], rows))
    body += f'<h2>Option paths — pick one, then implement</h2>'
    for s in sug:
        rows = []
        for o in opts.get(s['suggestion_id'], []):
            oid = o['option_id']
            path = o['path_label']
            does = o['what_it_does']
            cost = o['cost']
            risk = o['risk']
            ev = o['evidence_needed']
            cn = o['clearing_number']
            ch_lbl = 'owner chooses — blank by design'
            rows.append(
                '<tr>'
                + cell(oid, MONO)
                + cell(path)
                + cell(does)
                + cell(cost)
                + cell(risk)
                + cell(ev)
                + cell(cn)
                + f'<td class={DQ}{BLANK}{DQ}>{ch_lbl}</td>'
                + '</tr>')
        sid = s['suggestion_id']
        title = s['title']
        body += (f'<h3>{esc(sid)} — {esc(title)}</h3>'
                 + table(['Option', 'Path', 'What it does', 'Cost', 'Risk',
                          'Evidence needed', 'Clearing number', 'Choice'], rows))
    write('suggestions.html', page(
        'Suggestions — review before implementing',
        f'{len(sug)} suggestions with {len(opts)} option paths, decision columns blank by design',
        body, 'suggestions.html'))


def build_strategies() -> None:
    strat = read('strategies.csv')
    rows = []
    for s in strat:
        sid = s['strategy_id']
        stype = s['strategy_type']
        status = s['status']
        regc = s['registration_commit']
        regpred = s['registration_commit_predates_kickoff']
        fk = s['first_kickoff']
        note = s['note']
        rows.append(
            '<tr>'
            + cell(sid, MONO)
            + cell(stype)
            + f'<td>{tag(status)}</td>'
            + cell(regc)
            + cell(regpred)
            + cell(fk)
            + f'<td>{esc(note)}</td>'
            + '</tr>')
    body = (f'<p>Pre-registered strategy declarations. A strategy is registered only when its rule '
            f'text, sample window and gates are committed before the first kickoff of its '
            f'evaluation window; the commit hash is the registration. Zero strategies are '
            f'registered, so none can qualify.</p>'
            + table(['ID', 'Type', 'Status', 'Registration commit',
                     'Commit predates kickoff', 'First kickoff', NOTE], rows))
    write('strategies.html', page(
        'Pre-registered strategies',
        f'{len(strat)} declared strategies, 0 registered', body, 'strategies.html'))


def build_leaderboard() -> None:
    lb = read('leaderboard.csv')
    strat = read('strategies.csv')
    rows = []
    for l in lb:
        sid = l['strategy_id']
        div = l['division']
        ss = l['signal_score']
        slb = l['signal_lower_bound']
        sts = l['staking_score']
        strp = l['staking_reported']
        qual = l['qualified']
        rew = l['reward']
        note = l['note']
        rows.append('<tr>' + cell(sid, MONO) + cell(div)
                    + cell(ss) + cell(slb) + cell(sts) + cell(strp)
                    + f'<td>{tag(qual)}</td>'
                    + cell(rew) + cell(note) + '</tr>')
    body = (f'<p>Proper-score leaderboard, split into singles, game parlays, same-game parlays and '
            f'prop-combo divisions. Signal is ranked on benchmark-relative Brier skill with a '
            f'game-cluster lower bound and a multiplicity adjustment; staking is reported beside '
            f'it and never used for rank. Backtest numbers are forbidden from appearing here. '
            f'Empty by design: 0 qualified strategies.</p>'
            + table(['Strategy', 'Division', 'Signal score', 'Signal lower bound',
                     'Staking score', 'Staking reported', 'Qualified', 'Reward', NOTE], rows))
    srows = []
    for s in strat:
        sid = s['strategy_id']
        stype = s['strategy_type']
        status = s['status']
        note = s['note']
        srows.append(
            '<tr>'
            + cell(sid, MONO)
            + cell(stype)
            + f'<td>{tag(status)}</td>'
            + f'<td>{esc(note)}</td>'
            + '</tr>')
    body += (f'<h2>Strategy declarations</h2>'
             + table(['ID', 'Type', 'Status', NOTE], srows))
    write('leaderboard.html', page(
        'Proper-score leaderboard — signal vs staking',
        f'{len(strat)} declared strategies, 0 qualified', body, 'leaderboard.html'))


def build_price_snapshot() -> None:
    rows = read('price_snapshot_store.csv')
    out = []
    for r in rows:
        out.append('<tr>' + ''.join(cell(r.get(c, '')) for c in
             ['snapshot_id', 'market_id', 'fixture', 'market_type', 'originated_at',
              'open_price', 'open_captured_at', 'open_source_url', 'close_price',
              'close_captured_at', 'close_source_url', 'sha256_hash', 'hash_chain_prev',
              'status', NOTE]) + '</tr>')
    body = (f'<p>Price-snapshot store: records opening and closing numbers for every market we '
            f'originate, hash-chained per market. Every cell is blank because no official source '
            f'publishes book prices (the NFL publishes no odds page; '
            f'https://www.nfl.com/odds/ is the NFL 404 page). The market and difference columns '
            f'stay blank with the capture attempt logged.</p>'
            + table(['Snapshot', 'Market', 'Fixture', 'Type', 'Originated at', 'Open price',
                     'Open captured at', 'Open source', 'Close price', 'Close captured at',
                     'Close source', 'SHA-256', 'Hash chain prev', 'status', NOTE], out))
    write('price-snapshot.html', page(
        'Price-snapshot store — opening and closing numbers',
        'Every market we originate; blank where no official price source exists',
        body, 'price-snapshot.html'))


def build_results_feed() -> None:
    rows = read('results_feed.csv')
    out = []
    for r in rows:
        out.append('<tr>' + ''.join(cell(r.get(c, '')) for c in
             ['game_id', 'season', 'week', 'game_date', 'away_team', 'home_team',
              'away_score', 'home_score', 'winner', 'result_source_url', 'read_date', NOTE]) + '</tr>')
    body = (f'<p>Verified results feed: game-level results read from an official source at a dated '
            f'commit, so backtests and ROI can be computed. No rows re-read by this session; prior '
            f'packs publish a 136-150 game corpus inherited as a repo claim.</p>'
            + table(['Game', 'Season', 'Week', 'Date', 'Away', 'Home', 'Away score',
                     'Home score', 'Winner', SRC, 'Read date', NOTE], out))
    write('results-feed.html', page(
        'Verified results feed',
        'Game-level results read from an official source at a dated commit',
        body, 'results-feed.html'))


def build_originated_lines() -> None:
    rows = read('originated_lines.csv')
    out = []
    for r in rows:
        out.append('<tr>' + ''.join(cell(r.get(c, '')) for c in
             ['line_id', 'fixture', 'market_type', 'stage_order', 'fair_line',
              'fair_inputs', 'market_line', 'difference', 'derivation',
              'market_capture_url', NOTE]) + '</tr>')
    body = (f'<p>Origination order: side first, then total, then moneyline. The model{AP}s fair line, '
            f'the market line, and the difference are published as three separate columns, with the '
            f'model output stored as a probability plus its inputs. The market line and difference '
            f'are blank where no market capture exists.</p>'
            + table(['Line', 'Fixture', 'Market type', 'Stage order', 'Fair line',
                     'Fair inputs', 'Market line', 'Difference', 'Derivation',
                     'Market capture', NOTE], out))
    write('originated-lines.html', page(
        'Originated lines — side, total, moneyline',
        'Fair line / market line / difference as separate columns',
        body, 'originated-lines.html'))


def build_depth() -> None:
    depth = read('depth_model.csv')
    register = read('depth_chart_register.csv')
    drows = []
    for r in depth:
        drows.append('<tr>' + ''.join(cell(r.get(c, '')) for c in
         ['slot_id', 'club', 'unit', 'position', 'rank', 'players', 'shared_slot',
          'empty_slot', 'depth_source_url', 'depth_read_date', NOTE]) + '</tr>')
    rrows = []
    for r in register:
        rrows.append('<tr>' + ''.join(cell(r.get(c, '')) for c in
         ['register_id', 'club', 'unit', 'position', 'slot', 'player', 'date',
          'source_url', NOTE]) + '</tr>')
    body = (f'<h2>Depth model — slots as groups, not a single starter</h2>'
            f'<p>Depth slots are modelled as groups; column 1 is not treated as '
            f'the starter. Shared slots and empty slots are represented faithfully and are '
            f'distinguishable from a ranked list. Depth is never derived from jersey number, '
            f'experience or salary (rejected by policy). The Texans image-only depth and the Packers '
            f'jersey-prefix failures are unresolved.</p>'
            + table(['Slot', 'Club', 'Unit', 'Position', 'Rank', 'Players', 'Shared slot',
                     'Empty slot', SRC, 'Read date', NOTE], drows)
            + f'<h2>Official depth-chart register</h2>'
            f'<p>One register row per slot with date and source. Not built.</p>'
            + table(['Register', 'Club', 'Unit', 'Position', 'Slot', 'Player', 'Date',
                     SRC, NOTE], rrows))
    write('depth.html', page(
        'Depth & availability — replacement depth tracked',
        'Depth slots as groups; shared and empty slots represented faithfully',
        body, 'depth.html'))


def build_injuries() -> None:
    inj = read('injury_tracking.csv')
    rows = []
    for r in inj:
        rows.append('<tr>' + ''.join(cell(r.get(c, '')) for c in
         ['read_id', 'club', 'player', 'position', 'injuries', 'practice_status',
          'game_status', 'capture_timestamp', 'delta_vs_previous', SRC, NOTE])
            + '</tr>')
    body = (f'<p>Every injury-hub read stored with its clock time; the delta is published, never '
            f'the level. The injury report is treated as a timestamped series captured Wednesday '
            f'to kickoff. Single capture exists today; no dated Wed/Thu/Fri history yet.</p>'
            + table(['Read', 'Club', 'Player', 'Position', 'Injuries', 'Practice status',
                     'Game status', 'Capture timestamp', 'Delta vs previous', SRC, NOTE], rows))
    write('injuries.html', page(
        'Injuries — timestamped reads, delta never level',
        'Injury-hub reads with clock time; delta published', body, 'injuries.html'))


def build_correlations() -> None:
    rows = read('correlations.csv')
    out = []
    for r in rows:
        out.append('<tr>' + ''.join(cell(r.get(c, '')) for c in
             ['corr_id', 'variable_a', 'variable_b', 'correlation', 'n', SRC, NOTE]) + '</tr>')
    body = (f'<p>Correlations computed only from officially sourced numbers, with n published '
            f'beside each value. No official price/results feed exists to correlate, so every '
            f'correlation cell is blank.</p>'
            + table(['ID', 'Variable A', 'Variable B', 'Correlation', 'n', SRC, NOTE], out))
    write('correlations.html', page(
        'Correlations & luck',
        'Official-source numbers only; n published with each value',
        body, 'correlations.html'))


def build_validation() -> None:
    gates = read('validation_gates.csv')
    rows = []
    for g in gates:
        gid = g['gate_id']
        gname = g['gate_name']
        applies = g['applies_to']
        definition = g['definition']
        threshold = g['threshold']
        state = g['state']
        note = g['note']
        rows.append('<tr>' + cell(gid, MONO) + cell(gname)
                    + cell(applies) + f'<td>{esc(definition)}</td>'
                    + cell(threshold) + f'<td>{tag(state)}</td>'
                    + f'<td>{esc(note)}</td></tr>')
    body = (f'<p>Validation gates every strategy must pass before appearing on the leaderboard. '
            f'Pre-registration, train/validation/holdout, proper-score qualification, '
            f'joint-evidence gate for combos, signal/staking separation, control baselines, '
            f'two-stage skill, demotion gate, no backtest numbers on the leaderboard, and '
            f'correlation sourcing.</p>'
            + table(['Gate', 'Name', 'Applies to', 'Definition', 'Threshold', 'State', NOTE], rows))
    write('validation.html', page(
        'Validation gates',
        'Every strategy must pass all gates before appearing on the leaderboard',
        body, 'validation.html'))


def build_snapshot_ledger() -> None:
    rows = read('snapshot_ledger.csv')
    out = []
    for r in rows:
        out.append('<tr>' + ''.join(cell(r.get(c, '')) for c in
             ['ledger_id', 'capture_type', 'club', 'fixture', 'capture_timestamp',
              'sha256_hash', 'previous_hash', SRC, NOTE]) + '</tr>')
    body = (f'<p>Point-in-time snapshot ledger for injuries, depth charts and inactives: '
            f'pre-kickoff replacement certainty with no lookahead leakage, retained hashes, and '
            f'immutable captures outside the static site. Not built (durable snapshot storage '
            f'pending S-01/S-08).</p>'
            + table(['Ledger', 'Capture type', 'Club', 'Fixture', 'Capture timestamp',
                     'SHA-256', 'Previous hash', SRC, NOTE], out))
    write('snapshot-ledger.html', page(
        'Point-in-time snapshot ledger',
        'Pre-kickoff replacement certainty; no lookahead leakage',
        body, 'snapshot-ledger.html'))


def build_flagged() -> None:
    flags = read('flagged.csv')
    rows = []
    for f in flags:
        fid = f['flag_id']
        scope = f['flag_scope']
        severity = f['severity']
        area = f['area']
        item = f['item']
        value = f['value_if_known']
        reqs = f['req_ids']
        src = f['source_url']
        rows.append(
            '<tr>'
            + cell(fid, MONO)
            + cell(scope)
            + f'<td>{tag(severity)}</td>'
            + cell(area)
            + f'<td><strong>{esc(item)}</strong></td>'
            + cell(value)
            + cell(reqs, MONO)
            + f'<td>{link(src)}</td>'
            + '</tr>')
    body = (f'<p>Flagged irregularities and unverified items do not block the merge — they are '
            f'published here with their source links so they can be reviewed once the site is live. '
            f'A blank <em>value if known</em> cell means the honest value is unknown.</p>'
            + table(['Flag', 'Scope', 'Severity', 'Area', 'Item', 'Value if known',
                     'Requirements', SRC], rows))
    write('flagged.html', page(
        'Flagged for review',
        'Irregularities and unverified items, with source links', body, 'flagged.html'))


def build_sources() -> None:
    srcs = read('sources.csv')
    reads = read('official_reads.csv')
    srows = []
    for s in srcs:
        sid = s['source_id']
        url = s['requested_url']
        canon = s['canonical_url']
        title = s['page_title']
        used = s['used_for']
        rd = s['read_date']
        note = s['note']
        open_lbl = 'open'
        srows.append(
            '<tr>'
            + cell(sid, MONO)
            + f'<td>{link(url, open_lbl)}</td>'
            + cell(canon, MONO)
            + cell(title)
            + cell(used)
            + cell(rd, MONO)
            + f'<td>{esc(note)}</td>'
            + '</tr>')
    rrows = []
    for r in reads:
        rid = r['read_id']
        sid = r['source_id']
        canon = r['canonical_url']
        rd = r['read_date']
        rows_t = r['rows_transcribed']
        sha = r['sha256_transcript']
        scope = r['hash_scope']
        note = r['note']
        rurl = r['requested_url']
        rrows.append(
            '<tr>'
            + cell(rid, MONO)
            + cell(sid, MONO)
            + cell(canon, MONO)
            + cell(rd, MONO)
            + cell(rows_t, MONO)
            + cell(sha, MONO)
            + cell(scope)
            + cell(note)
            + f'<td>{link(rurl)}</td>'
            + '</tr>')
    body = (f'<h2>Official sources</h2>'
            f'<p>Every value published by this pack comes from one of these pages, or is inherited '
            f'from another pack and labelled as a claim. This session could not reach nfl.com, so '
            f'it performed <strong>no new NFL official-source reads</strong>.</p>'
            + table(['ID', 'Requested URL', 'Canonical URL', 'Page title', 'Used for',
                     'Read date', NOTE], srows)
            + f'<h2>Read log</h2>'
            f'<p class={DQ}note{DQ}>The SHA-256 is computed over the exact text transcribed from the '
            f'page. It is a tamper check on the committed data, not a fingerprint of the page{AP}s '
            f'own bytes.</p>'
            + table(['Read', 'Source', 'Canonical URL', 'Read date', 'Rows',
                     'SHA-256 of transcript', 'Hash scope', NOTE, 'Link'], rrows))
    write('sources.html', page(
        'Sources & read log',
        'Official sources and the dated read log', body, 'sources.html'))


def build_repo_review() -> None:
    findings = read('repo_findings.csv')
    stats = {r['metric']: r['value'] for r in read('repo_stats.csv')}
    rows = []
    for f in findings:
        fid = f['finding_id']
        severity = f['severity']
        path = f['path']
        finding = f['finding']
        evidence = f['evidence']
        status = f['status']
        repo_url = 'https://github.com/sassnarep3-star/Own6'
        repo_lbl = 'repo'
        rows.append(
            '<tr>'
            + cell(fid, MONO)
            + f'<td>{tag(severity)}</td>'
            + cell(path, MONO)
            + f'<td>{esc(finding)}</td>'
            + cell(evidence)
            + f'<td>{tag(status)}</td>'
            + f'<td>{link(repo_url, repo_lbl)}</td>'
            + '</tr>')
    cards = ''.join(
        f'<div class={DQ}card{DQ}><span>{esc(k.replace(US, SP))}</span>'
        f'<strong>{esc(v)}</strong></div>'
        for k, v in stats.items() if not k.endswith('commit'))
    bc = stats.get('base_commit', '')
    body = (f'<p>Line-by-line repo review computed against the pinned base commit '
            f'<code>{esc(bc)}</code>. Every finding is produced by '
            f'scanning the tracked files; nothing is hand-written.</p>'
            f'<div class={DQ}cards{DQ}>{cards}</div>'
            f'<h2>Findings</h2>'
            + table(['Finding', 'Severity', 'Path', 'What was found', 'Evidence',
                     'Status', 'Link'], rows))
    write('repo-review.html', page(
        'Repository review',
        'Line-by-line, computed at a pinned base commit', body, 'repo-review.html'))


def build_exec() -> None:
    reqs = read('requirements.csv')
    gates = read('gates.csv')
    sug = read('suggestions.csv')
    opts = read('suggestion_options.csv')
    qia = read('qia.csv')
    gaps = read('information_gaps.csv')
    flags = read('flagged.csv')
    strat = read('strategies.csv')
    status: dict[str, int] = {}
    for r in reqs:
        status[r['status']] = status.get(r['status'], 0) + 1
    cleared = status.get('cleared', 0)
    cleared_repo = status.get('cleared_repo', 0)
    structural = status.get('structural', 0)
    blocked_count = status.get('blocked', 0)
    rejected = status.get('rejected', 0)
    open_count = status.get('open', 0)
    cards = ''.join(
        f'<div class={DQ}card{DQ}><span>{esc(k)}</span><strong>{v}</strong></div>'
        for k, v in sorted(status.items(), key=lambda kv: -kv[1]))
    blocked: dict[str, int] = {}
    for r in reqs:
        if r['blocking_gate']:
            blocked[r['blocking_gate']] = blocked.get(r['blocking_gate'], 0) + 1
    top = sorted(blocked.items(), key=lambda kv: -kv[1])[:6]
    parts = []
    parts.append(f'<h2>Where the programme actually stands</h2>')
    parts.append(f'<div class={DQ}cards{DQ}>{cards}</div>')
    parts.append(f'<p>The owner{AP}s brief contains {len(reqs)} requirements across prices & results, ')
    parts.append(f'origination, leaderboard, depth & availability, injuries, correlation & luck, and ')
    parts.append(f'site & data. Of those, <strong>{cleared} are cleared</strong>, ')
    parts.append(f'{cleared_repo} are inherited from earlier packs as claims, ')
    parts.append(f'{structural} exist as schema or code with no data behind them, ')
    parts.append(f'{blocked_count} are blocked by a named gate, ')
    parts.append(f'{rejected} were rejected by policy, and ')
    parts.append(f'{open_count} are open.</p>')
    parts.append('<h2>The binding blockers</h2>')
    parts.append('<ol>')
    parts.append('<li><strong>No official market-price source exists.</strong> Until one does, the ')
    parts.append('residual, closing-line value and the vig decomposition cannot be published, and ')
    parts.append('neither can any backtest that uses prices. The owner{AP}s own ordering rule (R-20) says ')
    parts.append('decide the price policy first.</li>')
    parts.append('<li><strong>No verified depth-order source for all 32 clubs.</strong> Fourteen ')
    parts.append('requirements sit behind this, including the entire backup-deficiency feature. ')
    parts.append('Resolved before the feature is built, per the owner{AP}s order.</li>')
    parts.append('<li><strong>No official inactive list captured.</strong> The injury register is ')
    parts.append('verifiable weekly, but whether the player actually played is unanswerable without ')
    parts.append('inactives, so Questionable cannot be calibrated and no designation may become a ')
    parts.append('model feature.</li>')
    parts.append('<li><strong>Zero strategies pre-registered.</strong> No rule text, sample window and ')
    parts.append('gates are committed before any evaluation window, so no strategy can qualify and the ')
    parts.append('leaderboard stays empty.</li>')
    parts.append('</ol>')
    parts.append('<h2>What this session verified from official pages</h2>')
    parts.append('<ul>')
    parts.append('<li>This session cannot reach nfl.com (sandbox outbound limit: github.com, ')
    parts.append('api.github.com, registry.npmjs.org, pypi.org, files.pythonhosted.org only), so it ')
    parts.append('performed <strong>no new NFL official-source reads</strong>.</li>')
    parts.append('<li>Verified cells are empty; prior session reads are inherited as labelled repo ')
    parts.append('claims.</li>')
    parts.append('<li>Everything not confirmed is left blank and flagged — never inferred, never filled ')
    parts.append('in.</li>')
    parts.append('</ul>')
    parts.append('<h2>Gates that block the most requirements</h2>')
    parts.append(table(['Gate', 'Requirements blocked'],
                       [f'<tr>{cell(g, MONO)}{cell(str(n), MONO)}</tr>' for g, n in top]))
    parts.append(f'<h2>The decision board</h2>')
    parts.append(f'<p>{len(sug)} suggestions with {len(opts)} option paths, {len(qia)} questions with ')
    parts.append(f'what we have and what we lack, and {len(gaps)} information gaps with the route that ')
    parts.append(f'closes each. The decision columns are blank by design: the owner picks the path ')
    parts.append(f'before anything is implemented.</p>')
    parts.append(f'<h2>Strategies</h2>')
    parts.append(f'<p>{len(strat)} declared strategies, 0 registered (no pre-window commit hash), ')
    parts.append(f'0 qualified.</p>')
    parts.append(f'<h2>Flagged</h2>')
    parts.append(f'<p>{len(flags)} items are published on the ')
    parts.append(f'<a href={DQ}flagged.html{DQ}>Flagged for review</a> page with their source links. None ')
    parts.append(f'blocks the merge.</p>')
    parts.append('<h2>What is deliberately missing</h2>')
    parts.append('<p>No prices, no odds, no closing-line value, no vig decomposition, no leaderboard ')
    parts.append('rows, no profitability claim, and no statement that any strategy is skillful. Those ')
    parts.append('cells are blank because the evidence does not exist yet — filling them would be the ')
    parts.append('exact failure mode this project is built to avoid.</p>')
    body = ''.join(parts)
    write('executive-summary.html', page(
        'Executive summary',
        'Read this first — the state of the programme in one page', body, 'executive-summary.html'))


# --------------------------------------------------------------------------- main
BUILDERS = [
    build_index, build_requirements, build_gates, build_questions, build_gaps,
    build_suggestions, build_strategies, build_leaderboard, build_price_snapshot,
    build_results_feed, build_originated_lines, build_depth, build_injuries,
    build_correlations, build_validation, build_snapshot_ledger, build_flagged,
    build_sources, build_repo_review, build_exec,
]


def main() -> int:
    os.makedirs(DOCS, exist_ok=True)
    for b in BUILDERS:
        b()
    print(f'built {len(NAV)} pages in docs/nfl-4c8cf5a6/')
    return 0


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    rc = main()
    if args.check and rc == 0:
        rc = subprocess.call([sys.executable, 'scripts/check_nfl_4c8cf5a6.py'], cwd=REPO)
    raise SystemExit(rc)