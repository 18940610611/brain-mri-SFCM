# Dataset setup

Raw medical images are intentionally excluded from GitHub. Download them from their official or authorized distribution channels and keep them on your local disk.

## BrainWeb

Official pages:

- Simulated MRI selection: https://brainweb.bic.mni.mcgill.ca/selection_normal.html
- Anatomical model: https://brainweb.bic.mni.mcgill.ca/anatomic_normal.html

The experiments expect the following files in a single directory such as `E:\DATA\BrainWeb`:

```text
t1_icbm_normal_1mm_pn0_rf20.rawb.gz
t1_icbm_normal_1mm_pn3_rf20.rawb.gz
t1_icbm_normal_1mm_pn5_rf20.rawb.gz
t1_icbm_normal_1mm_pn9_rf20.rawb.gz
t1_icbm_normal_1mm_pn3_rf0.rawb.gz
t1_icbm_normal_1mm_pn3_rf40.rawb.gz
phantom_1.0mm_normal_crisp.rawb.gz
```

Use T1, 1 mm slice thickness, the stated noise and RF settings, and the 1 mm crisp/discrete anatomical model.

## OASIS

OASIS data access: https://www.oasis-brains.org/

The local derivative used by `run_oasis.py` has this layout:

```text
E:\DATA\OASIS\
  Test\
    vol\
      <case>_vol.nii.gz
    seg\
      <case>_seg.nii.gz
```

The segmentation derivative used in this project encodes CSF, GM, and WM as labels 33, 22, and 11. If your downloaded derivative uses different labels or filenames, update `tissue_truth()` or convert the data to this layout before running the experiment.

Do not commit raw OASIS files to a public repository unless the applicable data-use terms explicitly permit redistribution.

