from sklearn.ensemble import HistGradientBoostingClassifier


def build_hist_gradient_boosting_classifier(
    random_state: int = 42,
) -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(
        learning_rate=0.08,
        max_iter=150,
        max_leaf_nodes=31,
        min_samples_leaf=30,
        l2_regularization=1.0,
        class_weight="balanced",
        random_state=random_state,
    )
