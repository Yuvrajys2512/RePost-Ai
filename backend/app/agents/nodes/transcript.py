from __future__ import annotations

import argparse

from app.schemas.transcript import Transcript
from app.services.transcript import TranscriptService, transcript_from_text


def extract_transcript(youtube_url: str) -> Transcript:
    return TranscriptService().extract(youtube_url)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract a YouTube transcript.")
    parser.add_argument("youtube_url", nargs="?", help="YouTube URL to extract.")
    parser.add_argument(
        "--text",
        help="Use supplied transcript text instead of fetching YouTube. Useful for contract tests.",
    )
    parser.add_argument("--json", action="store_true", help="Print the full Transcript JSON.")
    args = parser.parse_args()

    if args.text:
        transcript = transcript_from_text(args.text)
    elif args.youtube_url:
        transcript = extract_transcript(args.youtube_url)
    else:
        parser.error("Provide youtube_url or --text")

    if args.json:
        print(transcript.model_dump_json(indent=2))
    else:
        print(transcript.text)


if __name__ == "__main__":
    main()
