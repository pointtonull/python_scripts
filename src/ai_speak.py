#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "openai",
#     "openai[voice_helpers]",
# ]
# ///

import time
import sys
import argparse
import asyncio

from openai import AsyncOpenAI
from openai.helpers import LocalAudioPlayer

# gets OPENAI_API_KEY from your environment variables
openai = AsyncOpenAI()


async def main(input_text: str) -> None:
    start_time = time.time()

    async with openai.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice="alloy",
        response_format="pcm",  # similar to WAV, but without a header chunk at the start.
        input=input_text,
    ) as response:
        print(f"Time to first byte: {int((time.time() - start_time) * 1000)}ms")
        await LocalAudioPlayer().play(response)
        print(f"Time to play: {int((time.time() - start_time) * 1000)}ms")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Synthesize speech from input text via OpenAI TTS."
    )
    parser.add_argument(
        "text",
        nargs="?",
        help="Text to synthesize. If not provided, read from stdin.",
    )
    args = parser.parse_args()
    if args.text:
        input_text = args.text
    else:
        if not sys.stdin.isatty():
            input_text = sys.stdin.read()
        else:
            parser.error(
                "No input provided. Provide text as argument or via stdin."
            )
    asyncio.run(main(input_text))
