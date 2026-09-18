from __future__ import annotations
import argparse
from pathlib import Path
import requests

DRYAD_API="https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.12jm63z3t/download"
MENDELEY_PAGES=[
 'https://data.mendeley.com/datasets/wvmw7p76t8/2',
 'https://data.mendeley.com/datasets/8nkcdf6c8y/1',
]

def download(url: str, out: Path):
    out.parent.mkdir(parents=True,exist_ok=True)
    with requests.get(url,stream=True,timeout=60,allow_redirects=True) as r:
        r.raise_for_status()
        with out.open('wb') as f:
            for chunk in r.iter_content(1024*1024):
                if chunk:f.write(chunk)
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out-dir',default='data/raw'); ap.add_argument('--dryad',action='store_true')
    args=ap.parse_args(); out=Path(args.out_dir)
    if args.dryad:
        try:
            p=download(DRYAD_API,out/'dryad_cap_acne.zip'); print('downloaded',p)
        except Exception as e:
            print('Dryad automated download failed:',e)
            print('Open the landing page and download Raw_images_files_of_measurements_Dryad.zip manually:')
            print('https://datadryad.org/dataset/doi:10.5061/dryad.12jm63z3t')
    print('\nMendeley datasets (download from landing pages):')
    for x in MENDELEY_PAGES: print(' -',x)
if __name__=='__main__':main()
