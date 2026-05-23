from pathlib import Path

from app.models import Base
from app.schemas.generation import GeneratedContentKit
from app.services.jobs import LocalVideoJobStore


def test_local_video_job_store_persists_between_instances(tmp_path: Path) -> None:
    store_path = tmp_path / "jobs.json"
    first_store = LocalVideoJobStore(store_path)
    job = first_store.create(
        "https://www.youtube.com/watch?v=abc123XYZ_9",
        transcript_text="A useful transcript.",
    )

    first_store.update(job.job_id, progress=100)
    second_store = LocalVideoJobStore(store_path)

    restored = second_store.get(job.job_id)
    assert restored is not None
    assert restored.progress == 100
    assert restored.transcript_text == "A useful transcript."


def test_phase2_models_are_registered() -> None:
    assert {"video_jobs", "generated_content"}.issubset(Base.metadata.tables.keys())


def test_generated_content_schema_accepts_json_payload() -> None:
    payload = {
        "twitter": {
            "platform": "twitter",
            "standalone_tweets": [{"text": f"Tweet {index}"} for index in range(5)],
            "thread": [{"text": f"Thread {index}"} for index in range(5)],
        },
        "linkedin": {
            "platform": "linkedin",
            "posts": [
                {
                    "hook": "A strong hook",
                    "body": (
                        "This body has enough words to pass the LinkedIn contract because it "
                        "describes a useful content repurposing insight with specific structure "
                        "and gives the reader a practical reason to keep watching."
                    ),
                    "cta": "What would you try next?",
                },
                {
                    "hook": "Another strong hook",
                    "body": (
                        "This second body also contains enough words to validate that JSON "
                        "payloads can round trip through the schema used by stored jobs "
                        "without losing the platform specific fields."
                    ),
                    "cta": "Where does this apply?",
                },
            ],
        },
    }

    assert GeneratedContentKit.model_validate(payload).twitter.thread[0].text == "Thread 0"
