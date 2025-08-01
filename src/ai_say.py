#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "openai",
#     "openai[voice_helpers]",
#     "click",
# ]
# ///

import time
import sys
import asyncio
import click

from openai import AsyncOpenAI
from openai.helpers import LocalAudioPlayer

openai = AsyncOpenAI()


async def main(input_text: str) -> None:
    start_time = time.time()

    print(f"Reading: {input_text}")
    async with openai.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="coral",
        response_format="pcm",
        input=input_text,
        instructions="Speak in a way that makes the content easy to remember.",
    ) as response:
        print(f"Time to first byte: {int((time.time() - start_time) * 1000)}ms")
        await LocalAudioPlayer().play(response)
        print(f"Time to play: {int((time.time() - start_time) * 1000)}ms")


@click.command(context_settings={"ignore_unknown_options": True})
@click.argument("text", required=False)
def cli(text):
    """
    Synthesize speech from input text via OpenAI TTS.

    TEXT is the input to synthesize. If not provided, reads from stdin.
    """
    if text:
        input_text = text
    else:
        if not sys.stdin.isatty():
            input_text = sys.stdin.read()
        else:
            raise click.UsageError(
                "No input provided. Provide text as argument or via stdin."
            )
    asyncio.run(main(input_text))


if __name__ == "__main__":
    cli()

