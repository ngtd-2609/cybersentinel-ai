from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from cybersentinel_ai.features.dataset import prepare_binary_dataframe
from cybersentinel_ai.features.splitting import binary_split_for_file
from cybersentinel_ai.ingestion.cicids2017 import (
    get_dataset_root,
    iter_cicids_csv,
)

OUTPUT_DIR = Path("data/processed/cicids2017_binary")
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
            split = binary_split_for_file(csv_path)
            print(f"Processing: {csv_path.name} -> {split}")

            for chunk in iter_cicids_csv(csv_path, chunksize=CHUNK_SIZE):
                prepared = prepare_binary_dataframe(chunk)
                table = pa.Table.from_pandas(prepared, preserve_index=False)

                if split not in writers:
                    writers[split] = pq.ParquetWriter(
                        output_paths[split],
                        table.schema,
                        compression="snappy",
                    )

                writers[split].write_table(table)
                row_counts[split] += len(prepared)

    finally:
        for writer in writers.values():
            writer.close()

    print("\n=== BUILD COMPLETE ===")

    for split, path in output_paths.items():
        size_mb = path.stat().st_size / (1024**2)
        print(
            f"{split}: rows={row_counts[split]} "
            f"size={size_mb:.2f} MiB path={path}"
        )


if __name__ == "__main__":
    main()
