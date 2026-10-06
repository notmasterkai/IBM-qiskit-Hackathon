"""Save the random forest's threat probabilities for the NSL-KDD test records.

Run once, locally (needs the dataset in data/). It reuses src/classifier.py unchanged and the
same settings as the notebook (SEED = 42). The output has NO raw dataset rows: only a record
number, the true label (0 normal, 1 attack) and the forest's probability. The website reads
this file, so it works without the dataset.
"""
import pandas as pd

from src.classifier import (load_nsl_kdd, make_binary_label, preprocess,
                            threat_probability, train_random_forest)

SEED = 42
TRAIN_PATH = "data/KDDTrain+.txt"
TEST_PATH = "data/KDDTest+.txt"
OUT_PATH = "results/threat_probabilities.csv"

train_df = load_nsl_kdd(TRAIN_PATH)
test_df = load_nsl_kdd(TEST_PATH)
X_train, X_test, y_train, y_test = preprocess(train_df, test_df)
forest = train_random_forest(X_train, y_train, SEED)
probs = threat_probability(forest, X_test)

out = pd.DataFrame({"record": range(len(probs)), "true_label": y_test.to_numpy(),
                    "threat_probability": probs.round(4)})
out.to_csv(OUT_PATH, index=False)
print(f"saved {len(out)} rows to {OUT_PATH}")
