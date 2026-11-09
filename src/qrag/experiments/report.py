"""Regenerate statistics and compact Markdown tables from saved predictions."""
import argparse
import json
from pathlib import Path
from qrag.evaluation import analyze,latest_records
from qrag.experiments.artifacts import atomic_text,write_json


def report(run:Path,output:Path,reference=None):
    manifest=json.loads((run/'manifest.json').read_text())
    if manifest['status'] not in {'completed','completed_with_errors'}:
        raise ValueError('Cannot present an unfinished run as a complete evaluation')
    rows=latest_records(run/'predictions.jsonl')
    methods=manifest['identity']['spec']['methods']
    expected={(q,m['name']) for q in manifest['identity']['question_ids'] for m in methods}
    if {(r['question_id'],r['method']) for r in rows}!=expected:
        raise ValueError('Missing or unexpected question/method records')
    result=analyze(rows,reference)
    write_json(output.with_suffix('.json'),result)
    lines=['| Method | Questions | Answer F1 | Evidence recall | Actual context tokens | Failed records |',
           '| --- | ---: | ---: | ---: | ---: | ---: |']
    for method,values in result['table'].items():
        def fmt(key):
            value=values[key]
            return '—' if value is None else f'{value:.4f}'
        lines.append(f"| {method} | {values['questions']} | {fmt('answer_f1')} | {fmt('document_recall_successful_only')} | {fmt('context_tokens_successful_only')} | {values['failures']} |")
    lines+=['','Paired differences are method minus '+result['reference']+'; 95% question bootstrap intervals.',
            '','| Method | Mean F1 difference | 95% interval |','| --- | ---: | --- |']
    for method,diff in sorted(result['paired_differences_to_reference'].items()):
        lines.append(f"| {method} | {diff['mean_difference']:.4f} | [{diff['ci95'][0]:.4f}, {diff['ci95'][1]:.4f}] |")
    atomic_text(output.with_suffix('.md'),'\n'.join(lines)+'\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--reference')
    args=parser.parse_args()
    report(args.run_dir,args.output,args.reference)
