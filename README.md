# Brain MRI Clustering with FCM and Spatial Constraints

This repository contains the reproducible experiments for a course project on prototype-based brain MRI clustering. It compares K-Means, fuzzy C-means (FCM), and spatial fuzzy C-means (SFCM) for clustering cerebrospinal fluid (CSF), gray matter (GM), and white matter (WM).

## Experiments

- BrainWeb noise study: noise levels 0%, 3%, 5%, and 9%, with RF fixed at 20%.
- BrainWeb intensity-inhomogeneity study: RF levels 0%, 20%, and 40%, with noise fixed at 3%.
- SFCM parameter sensitivity: fuzzifier `m`, spatial weight `alpha`, and neighborhood size.
- OASIS external validation: 25 real T1 MRI cases, three slices per case, three random repetitions, and three clustering methods (675 clustering runs).

The committed `results/` directory contains the CSV metrics and representative visualizations produced by the experiments.

## Main results

- At 9% BrainWeb noise, SFCM achieved a mean Dice score of 0.9096, improving FCM by 0.0461.
- On the OASIS validation set, SFCM achieved a mean Dice score of 0.6775, compared with 0.6390 for FCM.
- Spatial constraints improve robustness under difficult conditions, but may over-smooth tissue boundaries when noise is low.

## Repository structure

```text
brain-mri-sfcm/
  fcm_core.py                 # K-Means, FCM, and SFCM implementation
  run_brainweb.py             # BrainWeb experiments
  run_oasis.py                # OASIS experiments
  run_sanity.py               # Small implementation check
  run_all.cmd                 # Windows entry point for BrainWeb
  requirements.txt
  data/
    README.md                 # Dataset access and expected layout
  results/
    noise/                    # BrainWeb noise experiment
    rf/                       # Bias-field experiment
    params/                   # Parameter sensitivity
    oasis/                    # OASIS external validation
```

## Installation

Python 3.10 or 3.11 is recommended.

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Data

The original MRI volumes are not redistributed in this repository because the datasets have their own access terms and are too large for ordinary GitHub storage. Follow [data/README.md](data/README.md) to obtain BrainWeb and OASIS and place them locally.

## Run the experiments

Implementation check:

```bash
python run_sanity.py
```

BrainWeb noise experiment:

```bash
python run_brainweb.py --data-dir "E:\DATA\BrainWeb" --suite noise --axis 2 --slices 70 80 90 100 110 --repeats 5
```

BrainWeb bias-field experiment:

```bash
python run_brainweb.py --data-dir "E:\DATA\BrainWeb" --suite rf --axis 2 --slices 70 80 90 100 110 --repeats 5
```

OASIS external validation:

```bash
python run_oasis.py --data-dir "E:\DATA\OASIS" --axis 2 --slices-per-case 3 --repeats 3
```

## Evaluation protocol

The clustering labels are aligned with tissue labels only during evaluation. The ground-truth CSF/GM/WM union is used as the region of interest, so the experiment evaluates tissue clustering rather than a complete skull-stripping pipeline. Reported metrics include tissue-wise Dice, mean Dice, mean IoU, ARI, NMI, and runtime.

## Reproducibility note

The CSV files are the source of all reported numerical results. Random seeds, selected slices, and method names are recorded in `raw_metrics.csv`. The repository does not claim that fuzzy memberships are calibrated clinical probabilities.

