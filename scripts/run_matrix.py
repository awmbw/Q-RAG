"""Run recorded configurations sequentially without competing for GPU memory."""
import argparse
from pathlib import Path
import subprocess
import sys


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--configs',type=Path,nargs='+',required=True)
    parser.add_argument('--root',type=Path,default=Path('results'))
    args=parser.parse_args()
    args.root.mkdir(parents=True,exist_ok=True)
    failures=[]
    for config in args.configs:
        directory=args.root/config.stem
        command=[sys.executable,'-m','qrag.experiments.study','--config',str(config),'--output',str(directory)]
        if directory.exists():command.append('--resume')
        print('Starting',config,flush=True)
        with (args.root/(config.stem+'.log')).open('a') as log:
            result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
        print('Finished',config,'exit',result.returncode,flush=True)
        if result.returncode:failures.append(config.name)
    if failures:
        raise SystemExit('Runs with errors: '+', '.join(failures))


if __name__=='__main__':
    main()
