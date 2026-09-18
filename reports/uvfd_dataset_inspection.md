# UVFD dataset inspection and training plan

Dataset: **Data for: Automatic hair removal on ultraviolet-induced fluorescence dermatoscopy images**  
Mendeley Data: `wvmw7p76t8`, version 2  
License: **CC BY 4.0**

## Verified archive structure

The official version-2 ZIP was downloaded from Mendeley's public ZIP endpoint and inspected in GitHub Actions.

- ZIP size: **694,552,024 bytes**
- Total files: **5,600 PNG files**
- UVFD image crops: **2,653**
- Dark-hair/ruler masks: **2,097**
- Light-hair/UV-particle masks: **850**
- Usable image keys with at least one mask: **2,653**
- Dark-mask only: **1,804**
- White-mask only: **556**
- Both mask types: **293**
- Images without masks: **0**
- Mask entries without a matching image: **1**

The archive's real mask counts differ slightly from the prose description on the landing page, which mentions 805 light-hair/particle crops. For training, use the **verified archive contents**, not the prose count.

## Image format

Sample verification shows:

- Images: **512×512 RGB PNG**
- Masks: **512×512 single-channel PNG**
- Masks are binary: pixel values **0 or 255**

## Leakage-safe grouping

The crops were produced from larger original UVFD photographs. Random crop-level splitting would leak nearly identical neighboring tissue into train and test.

Filename normalization yields **121 inferred source-image groups**. Examples:

- `crop_10_p13_IMG_3528` → source group `p13_IMG_3528`
- `crop_10_p15_field1` → source group `p15_field1`
- `image00005_crop_004` → source group `image00005`

This is very close to the publication description of **120 source photographs** and is therefore the correct grouping unit for train/validation/test splitting.

## Recommended first model

Train a **two-channel artifact segmentation target**:

- channel 0: dark hair + ruler
- channel 1: light hair + UV-reflecting particles

Recommended baseline architecture: a small U-Net or SegFormer-B0.

Loss:
`0.5 * BCEWithLogitsLoss + 0.5 * DiceLoss`

Primary metrics:
- Dice per artifact channel
- IoU per artifact channel
- false-positive area on unannotated channel
- recall on thin/light hair

Use source-grouped splits only.

## Role in the larger product

This model is **not the porphyrin detector**. Its job is to identify optical artifacts that could otherwise be mistaken for fluorescence signal. The processing chain should be:

`UV image → artifact segmentation → artifact suppression/masking → porphyrin fluorescence analysis`

The Dryad Visiopor dataset remains the calibration source for porphyrin-related metrics.
