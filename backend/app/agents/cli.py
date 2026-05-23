from __future__ import annotations

import argparse

from app.agents.graph import PipelineResult, run_pipeline, run_pipeline_for_transcript
from app.services.transcript import transcript_from_text


def format_pipeline_result(result: PipelineResult) -> str:
    lines = [
        "# Analysis",
        f"Hook: {result.analysis.hook}",
        f"Takeaway: {result.analysis.audience_takeaway}",
        "",
        "# Twitter Standalone",
    ]
    lines.extend(f"- {tweet.text}" for tweet in result.content.twitter.standalone_tweets)
    lines.extend(["", "# Twitter Thread"])
    lines.extend(f"{index}. {tweet.text}" for index, tweet in enumerate(result.content.twitter.thread, start=1))
    lines.extend(["", "# LinkedIn"])
    for index, post in enumerate(result.content.linkedin.posts, start=1):
        lines.extend([f"## Post {index}", post.text, ""])
    return "\n".join(lines).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the RePost AI CLI pipeline.")
    parser.add_argument("youtube_url", nargs="?", help="YouTube URL to process.")
    parser.add_argument(
        "--text",
        help="Use supplied transcript text instead of fetching YouTube. Useful before API wiring.",
    )
    parser.add_argument("--json", action="store_true", help="Print the full PipelineResult JSON.")
    args = parser.parse_args()

    if args.text:
        result = run_pipeline_for_transcript(transcript_from_text(args.text))
    elif args.youtube_url:
        result = run_pipeline(args.youtube_url)
    else:
        parser.error("Provide youtube_url or --text")

    if args.json:
        print(result.model_dump_json(indent=2))
    else:
        print(format_pipeline_result(result))


if __name__ == "__main__":
    main()

