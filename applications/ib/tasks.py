from celery import shared_task
from applications.ib.services.snapshot_service import sync_ib_snapshot


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3})
def sync_ib_snapshot_task(self):
    sync_ib_snapshot()
