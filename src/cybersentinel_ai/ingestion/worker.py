import argparse
import asyncio
import logging

from cybersentinel_ai.core.config import get_settings
from cybersentinel_ai.db.database import SessionLocal, atomic
from cybersentinel_ai.ingestion.notifications import (
    deliver_notification,
    next_due_deliveries,
)
from cybersentinel_ai.ingestion.realtime import publish_update
from cybersentinel_ai.ingestion.service import (
    mark_job_failed,
    next_due_jobs,
    process_ingestion_job,
)

logger = logging.getLogger(__name__)


async def run_cycle() -> int:
    processed = 0
    with SessionLocal() as database:
        job_ids = next_due_jobs(database)
    for job_id in job_ids:
        try:
            with SessionLocal() as database, atomic(database):
                result = process_ingestion_job(database, job_id)
            await publish_update({"type": "detection.processed", **result})
            if result.get("incident_id"):
                await publish_update({"type": "incident.updated", **result})
            processed += 1
        except Exception as exc:
            logger.exception("Ingestion job %s failed", job_id)
            with SessionLocal() as database:
                status = mark_job_failed(database, job_id, exc)
            await publish_update(
                {"type": "ingestion.failed", "job_id": job_id, "status": status}
            )

    with SessionLocal() as database:
        delivery_ids = next_due_deliveries(database)
    for delivery_id in delivery_ids:
        with SessionLocal() as database:
            status = deliver_notification(database, delivery_id)
        await publish_update(
            {
                "type": "notification.updated",
                "delivery_id": delivery_id,
                "status": status,
            }
        )
        processed += 1
    return processed


async def run_forever() -> None:
    settings = get_settings()
    logger.info("Starting ingestion worker")
    while True:
        await run_cycle()
        await asyncio.sleep(settings.ingestion_worker_poll_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(description="CyberSentinel ingestion worker")
    parser.add_argument("--once", action="store_true", help="Process one queue cycle")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    if args.once:
        asyncio.run(run_cycle())
    else:
        asyncio.run(run_forever())


if __name__ == "__main__":
    main()
