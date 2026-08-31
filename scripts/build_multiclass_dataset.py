from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from cybersentinel_ai.features.dataset import prepare_multiclass_dataframe
from cybersentinel_ai.features.splitting import multiclass_split_masks
from cybersentinel_ai.ingestion.cicids2017 import (
    get_dataset_root,
    iter_cicids_csv,
)

OUTPUT_DIR = Path("data/processed/cicids2017_multiclass")
CHUNK_SIZE = 100_000


def main() -> None:
    root = get_dataset_root()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_paths = {
        split: OUTPUT_DIR / f"{split}.parquet"
        for split in ("train", "validation", "test")
    }

    for path in output_paths.values():
        if path.exists():
            path.unlink()

    writers: dict[str, pq.ParquetWriter] = {}
    row_counts = {split: 0 for split in output_paths}

    try:
        for csv_path in sorted(root.glob("*.csv")):
            print(f"Processing: {csv_path.name}")

            for chunk in iter_cicids_csv(
                csv_path,
                chunksize=CHUNK_SIZE,
            ):
                prepared = prepare_multiclass_dataframe(chunk)

                train_mask, validation_mask, test_mask = (
                    multiclass_split_masks(prepared)
                )

                split_frames = {
                    "train": prepared.loc[train_mask],
                    "validation": prepared.loc[validation_mask],
                    "test": prepared.loc[test_mask],
                }

                for split, frame in split_frames.items():
                    if frame.empty:
                        continue

                    table = pa.Table.from_pandas(
                        frame,
                        preserve_index=False,
                    )

                    if split not in writers:
                        writers[split] = pq.ParquetWriter(
                            output_paths[split],
                            table.schema,
                            compression="snappy",
                        )

                    writers[split].write_table(table)
                    row_counts[split] += len(frame)

    finally:
        for writer in writers.values():
            writer.close()

    print("\n=== MULTICLASS BUILD COMPLETE ===")

    for split, path in output_paths.items():
        size_mb = path.stat().st_size / (1024**2)
        print(
            f"{split}: rows={row_counts[split]} "
            f"size={size_mb:.2f} MiB"
        )


if __name__ == "__main__":
    main()
