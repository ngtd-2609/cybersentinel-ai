from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline


def build_isolation_forest(
    random_state: int = 42,
) -> Pipeline:
    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            (
                "model",
                IsolationForest(
                    n_estimators=300,
                    max_samples="auto",
                    contamination="auto",
                    n_jobs=8,
                    random_state=random_state,
                ),
            ),
        ]
    )
