# Data: NSL-KDD

The dataset is **not committed** to Git (it is large). Download it yourself and place the files in this folder.

**Source:** NSL-KDD (Tavallaee et al., 2009), from Kaggle or the University of New Brunswick page. Link: https://www.kaggle.com/datasets/hassan06/nslkdd

## Files the project uses

| Role | File name | Rows | Columns |
|---|---|---|---|
| Training | `KDDTrain+.txt` | 125,973 | 43 |
| Test | `KDDTest+.txt` | 22,544 | 43 |

- Plain comma-separated text with **no header row**.
- The 43 columns are 41 features, then the label (`normal` or an attack name), then a difficulty score.
- Other files in the download (`*_20Percent`, `KDDTest-21`, `.arff`, images) are not used.
- The settings cell in the notebook holds the exact paths: `TRAIN_PATH` and `TEST_PATH`.
