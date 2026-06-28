"""A gloriously old-school visitor counter.

Persists a single integer as an object in the engine-cache S3 bucket (no extra
infra). Best-effort: increments are a plain read-modify-write, so under heavy
concurrency a hit might occasionally be lost — which is exactly how the 1998
counters worked too. Returns None if the store is unavailable so the UI can
just hide the widget rather than break.
"""
import os

_BUCKET = os.environ.get("HCL_CACHE_BUCKET")
_KEY = "meta/hits"


def bump():
    if not _BUCKET:
        return None
    try:
        import boto3

        client = boto3.client("s3")
        try:
            obj = client.get_object(Bucket=_BUCKET, Key=_KEY)
            count = int(obj["Body"].read().decode("utf-8").strip() or "0")
        except Exception:  # noqa: BLE001 - first hit / transient read miss
            count = 0
        count += 1
        client.put_object(
            Bucket=_BUCKET, Key=_KEY, Body=str(count).encode("utf-8"),
            ContentType="text/plain",
        )
        return count
    except Exception:  # noqa: BLE001 - never let the counter break a page load
        return None
