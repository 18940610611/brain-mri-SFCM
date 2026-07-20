from pathlib import Path
import argparse, sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / ".deps"))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import nibabel as nib
from run_brainweb import run_one


def load_pair(vol_path, seg_path):
    image = np.asarray(nib.load(str(vol_path)).dataobj, dtype=np.float32)
    labels = np.asarray(nib.load(str(seg_path)).dataobj)
    if image.shape != labels.shape:
        raise ValueError(f"shape mismatch: {image.shape} vs {labels.shape}")
    return image, labels


def tissue_truth(labels):
    # This local OASIS derivative uses 33/22/11 for CSF/GM/WM.
    truth = np.zeros(labels.shape, dtype=np.uint8)
    truth[labels == 33] = 1
    truth[labels == 22] = 2
    truth[labels == 11] = 3
    return truth


def choose_slices(truth, axis, count):
    roi = np.isin(truth, [1, 2, 3])
    area = roi.sum(axis=tuple(i for i in range(3) if i != axis))
    valid = np.flatnonzero(area >= 0.55 * area.max())
    positions = np.linspace(0, len(valid) - 1, count).round().astype(int)
    return sorted(set(int(valid[i]) for i in positions))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data-dir', default=str(ROOT / 'data' / 'oasis'))
    ap.add_argument('--axis', type=int, default=2, choices=[0, 1, 2])
    ap.add_argument('--slices-per-case', type=int, default=3)
    ap.add_argument('--repeats', type=int, default=3)
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--quick', action='store_true')
    args = ap.parse_args()
    data = Path(args.data_dir)
    vol_dir, seg_dir = data / 'Test' / 'vol', data / 'Test' / 'seg'
    segs = sorted(seg_dir.glob('*_seg.nii.gz'))
    if not segs:
        raise FileNotFoundError(seg_dir)
    if args.limit:
        segs = segs[:args.limit]
    outdir = ROOT / 'results' / 'oasis'; outdir.mkdir(parents=True, exist_ok=True)
    rows = []
    for case_no, seg_path in enumerate(segs):
        stem = seg_path.name.replace('_seg.nii.gz', '')
        vol_path = vol_dir / f'{stem}_vol.nii.gz'
        image, raw_labels = load_pair(vol_path, seg_path)
        truth = tissue_truth(raw_labels)
        slices = choose_slices(truth, args.axis, 1 if args.quick else args.slices_per_case)
        repeats = 1 if args.quick else args.repeats
        for idx in slices:
            for seed in range(repeats):
                for method in ['K-Means', 'FCM', 'SFCM']:
                    score, artifact = run_one(image, truth, args.axis, idx, method, seed)
                    rows.append({'case': stem, 'slice': idx, 'seed': seed, 'method': method, **score})
                    if case_no < 3 and seed == 0 and idx == slices[len(slices)//2]:
                        img, gt, pred, mask, centers, maps, hist = artifact
                        plt.imsave(outdir / f'{stem}_input.png', img, cmap='gray')
                        plt.imsave(outdir / f'{stem}_truth.png', np.where(mask, gt + 1, 0), cmap='viridis', vmin=0, vmax=3)
                        plt.imsave(outdir / f'{stem}_{method}.png', np.where(mask, pred + 1, 0), cmap='viridis', vmin=0, vmax=3)
    df = pd.DataFrame(rows)
    metrics = ['dice_csf','dice_gm','dice_wm','mean_dice','mean_iou','ari','nmi','seconds']
    df.to_csv(outdir / 'raw_metrics.csv', index=False, encoding='utf-8-sig')
    summary = df.groupby('method')[metrics].agg(['mean','std'])
    summary.to_csv(outdir / 'summary.csv', encoding='utf-8-sig')
    df.groupby(['case','method'])[metrics].mean().reset_index().to_csv(outdir / 'per_case.csv', index=False, encoding='utf-8-sig')
    print(summary[['dice_csf','dice_gm','dice_wm','mean_dice','seconds']])
    print(f'Completed {len(segs)} cases and {len(df)} clustering runs. Results: {outdir}')


if __name__ == '__main__':
    main()
