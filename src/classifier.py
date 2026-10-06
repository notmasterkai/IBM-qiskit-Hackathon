"""NSL-KDD loading, preprocessing, logistic regression, random forest and threat probabilities."""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.preprocessing import StandardScaler

# The files have no header row: 41 features, then the label, then a difficulty score.
COLUMN_NAMES = [
    "duration", "protocol_type", "service", "flag", "src_bytes", "dst_bytes", "land",
    "wrong_fragment", "urgent", "hot", "num_failed_logins", "logged_in", "num_compromised",
    "root_shell", "su_attempted", "num_root", "num_file_creations", "num_shells",
    "num_access_files", "num_outbound_cmds", "is_host_login", "is_guest_login", "count",
    "srv_count", "serror_rate", "srv_serror_rate", "rerror_rate", "srv_rerror_rate",
    "same_srv_rate", "diff_srv_rate", "srv_diff_host_rate", "dst_host_count",
    "dst_host_srv_count", "dst_host_same_srv_rate", "dst_host_diff_srv_rate",
    "dst_host_same_src_port_rate", "dst_host_srv_diff_host_rate", "dst_host_serror_rate",
    "dst_host_srv_serror_rate", "dst_host_rerror_rate", "dst_host_srv_rerror_rate",
    "label", "difficulty",
]
CATEGORICAL_COLUMNS = ["protocol_type", "service", "flag"]


def load_nsl_kdd(path: str) -> pd.DataFrame:
    """Read one NSL-KDD text file and attach column names."""
    return pd.read_csv(path, header=None, names=COLUMN_NAMES)


def make_binary_label(df: pd.DataFrame) -> pd.Series:
    """Label as 0 for 'normal' and 1 for every attack type."""
    return (df["label"] != "normal").astype(int)


def preprocess(train_df: pd.DataFrame, test_df: pd.DataFrame):
    """One-hot encode categories and scale numbers. Returns X_train, X_test, y_train, y_test.

    Everything is learned from the TRAINING data only, then applied to the test data,
    so the test set never influences the model.
    """
    y_train = make_binary_label(train_df)
    y_test = make_binary_label(test_df)
    features_train = train_df.drop(columns=["label", "difficulty"])
    features_test = test_df.drop(columns=["label", "difficulty"])

    # One-hot: the column set comes from the training data. Test columns are forced
    # to match: a category never seen in training is ignored, a missing one is all zeros.
    onehot_train = pd.get_dummies(features_train, columns=CATEGORICAL_COLUMNS, dtype=float)
    onehot_test = pd.get_dummies(features_test, columns=CATEGORICAL_COLUMNS, dtype=float)
    onehot_test = onehot_test.reindex(columns=onehot_train.columns, fill_value=0.0)

    # Scale only the original numeric columns (not the 0/1 one-hot columns).
    numeric_columns = [c for c in features_train.columns if c not in CATEGORICAL_COLUMNS]
    scaler = StandardScaler().fit(onehot_train[numeric_columns])  # fit on train only
    onehot_train[numeric_columns] = scaler.transform(onehot_train[numeric_columns])
    onehot_test[numeric_columns] = scaler.transform(onehot_test[numeric_columns])
    return onehot_train, onehot_test, y_train, y_test


def train_logistic_regression(X_train, y_train, seed: int) -> LogisticRegression:
    """Baseline classifier."""
    return LogisticRegression(max_iter=1000, random_state=seed).fit(X_train, y_train)


def train_random_forest(X_train, y_train, seed: int) -> RandomForestClassifier:
    """Random forest; its predict_proba is our threat probability."""
    return RandomForestClassifier(n_estimators=100, random_state=seed, n_jobs=-1).fit(X_train, y_train)


def evaluate(model, X_test, y_test) -> dict:
    """Test-set accuracy, precision, recall, F1 (fractions 0 to 1) and confusion matrix."""
    pred = model.predict(X_test)
    return {
        "accuracy": accuracy_score(y_test, pred),
        "precision": precision_score(y_test, pred),
        "recall": recall_score(y_test, pred),
        "f1": f1_score(y_test, pred),
        "confusion_matrix": confusion_matrix(y_test, pred),
    }


def threat_probability(model, X) -> np.ndarray:
    """Probability (0 to 1) that each record is an attack."""
    return model.predict_proba(X)[:, 1]


def window_threat(probabilities: np.ndarray, window_size: int) -> np.ndarray:
    """Average threat probability over consecutive, non-overlapping windows of records.

    A channel's threat is judged from a window of traffic, not one record,
    because a single record is noisy. An incomplete last window is dropped.
    """
    n_windows = len(probabilities) // window_size
    trimmed = np.asarray(probabilities[: n_windows * window_size])
    return trimmed.reshape(n_windows, window_size).mean(axis=1)


def build_window(probabilities: np.ndarray, y_true, attack_share: float, window_size: int,
                 rng: np.random.Generator) -> np.ndarray:
    """Pick window_size test records with a chosen share of real attacks; return their probabilities.

    This builds a scenario's traffic on purpose (for example 'mostly normal') using the
    TRUE labels only to choose which records go in. The threat level still comes from
    the random forest's own probabilities, averaged over the window.
    """
    y_true = np.asarray(y_true)
    n_attack = round(attack_share * window_size)
    attack_idx = rng.choice(np.where(y_true == 1)[0], size=n_attack, replace=False)
    normal_idx = rng.choice(np.where(y_true == 0)[0], size=window_size - n_attack, replace=False)
    return probabilities[np.concatenate([attack_idx, normal_idx])]
