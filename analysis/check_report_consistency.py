import csv
import re
import statistics
from collections import defaultdict
from pathlib import Path

root = Path(__file__).resolve().parents[1]
edited = root
def read_csv(path, delimiter=','):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=delimiter))

records = read_csv(root/'report/data/test_record.csv')
extension = read_csv(root/'report/data/extension_record.csv')
assert len(records) == 18 and len(extension) == 180
for row in records + extension:
    log = (root/row['log_file']).read_text()
    assert ('WARNING: DATA RACE' in log) == (row['race_report'] == 'yes'), row['log_file']
    assert ('all goroutines are asleep - deadlock' in log) == (row['deadlock_report'] == 'yes')
    assert row['checker_result'] in log, row['log_file']

table = (edited/'report/tables/test_record.tex').read_text()
lines = [line for line in table.splitlines() if re.match(r'\s+(k8s|docker)\\_', line)]
assert len(lines) == 18
for row, line in zip(records, lines):
    cells = [c.strip() for c in line.split('&')]
    assert cells[:6] == [row['case_id'].replace('_', r'\_'), row['version'], row['run'], row['exit_code'], row['checker_result'].replace('_', r'\_'), row['duration_s']]

groups = defaultdict(list)
for row in extension:
    groups[(row['case_id'], row['version'], row['config'])].append(row)
table = (edited/'report/tables/extension_record.tex').read_text()
lines = [line for line in table.splitlines() if re.match(r'\s+(k8s|docker)\\_', line)]
assert len(lines) == 18
for line in lines:
    cells = [c.strip() for c in line.split('&')]
    rows = groups[(cells[0].replace(r'\_', '_'), cells[1], cells[2])]
    assert len(rows) == 10
    durations = [float(r['duration_s']) for r in rows]
    expected = f'{statistics.mean(durations):.3f} \\pm {statistics.stdev(durations):.3f}'
    assert expected in cells[6], (cells[:3], expected, cells[6])
    assert cells[5] == f"{sum(r['race_report']=='yes' for r in rows)}/10"
    matches = sum(r['checker_result'] == r['expected'] for r in rows)
    assert f'{matches}/10' in cells[4]
    if cells[0] == r'docker\_27037':
        unique = sum(sorted(r['versions'].split(',')) == ['v1.17','v1.18','v1.19','v1.20'] for r in rows)
        assert unique == (0 if cells[1]=='buggy' and cells[2] in ['A','B'] else 10)
        print('Version sets', cells[:3], unique, '/10')

week3 = root/'report/results/week3_full_suite/run-20261116T150500Z-ixxI8j'
summary = read_csv(week3/'summary.tsv', '\t')
assert len(summary) == 18
assert all(r['checker_exit_code']=='0' for r in summary)
counts = read_csv(week3/'race_warning_counts.tsv', '\t')
assert len(counts) == 12
assert sum(int(r['race_warning_count'])>0 for r in counts)==3

all_tex = '\n'.join(p.read_text() for p in (edited/'report').rglob('*.tex'))
labels = re.findall(r'\\label\{([^}]+)\}', all_tex)
assert len(labels) == len(set(labels))
refs = re.findall(r'\\(?:ref|Cref|cref)\{([^}]+)\}', all_tex)
assert not set(refs)-set(labels)
bib = (edited/'report/references.bib').read_text()
for key in re.findall(r'\\cite\{([^}]+)\}', all_tex):
    assert re.search(r'@\w+\{'+key+r',', bib)
for asset in re.findall(r'\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}', all_tex):
    assert (edited/'report'/asset).exists()
print('PASS: 198 CSV records against logs; 18 Week 2 table rows; 18 extension groups and durations; 3 figures; labels and bibliography keys.')
