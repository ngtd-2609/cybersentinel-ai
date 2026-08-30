from xgboost import XGBClassifier


def build_xgboost_classifier(
    random_state: int = 42,
) -> XGBClassifier:
    return XGBClassifier(
        n_estimators=300,
        max_depth=8,
        learning_rate=0.08,
        subsample=0.9,
        colsample_bytree=0.9,
        min_child_weight=3,
        reg_lambda=1.0,
        objective="binary:logistic",
        eval_metric="logloss",
        tree_method="hist",
        n_jobs=8,
        random_state=random_state,
    )
