#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "openai",
#     "typer",
#     "diskcache",
# ]
# ///

from subprocess import Popen, PIPE
from textwrap import wrap
import json
import os
import shutil
import sys

import openai
import typer
from diskcache import Cache

app = typer.Typer()
CACHE = Cache("~/.cache/openai")
MAX_DIFF_CHARS = 4000

client = openai.OpenAI()
DEFAULT_MODEL = "gpt-4o"
DEFAULT_SYSTEM_PROMPT = "You are an artificial intelligence assistant and you need to engage in a helpful conversation with a user."

color_option = typer.Option("auto", help="When to use color")
COLOR = "auto"


@app.callback()
def main(color: str = color_option):
    global COLOR
    COLOR = color


@CACHE.memoize(expire=60 * 60 * 48)
def _simple(
    question, model=DEFAULT_MODEL, system_prompt=DEFAULT_SYSTEM_PROMPT, temperature=None
) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    if not response.choices:
        raise RuntimeError("No response received")
    return response.choices[0].message.content or ""


def format_python_code(code_block):
    try:
        import black

        return black.format_str(code_block, mode=black.mode.Mode(line_length=100))
    except Exception:
        return code_block


def get_terminal_width():
    try:
        return os.get_terminal_size().columns
    except AttributeError:
        try:
            fd = os.open("/dev/tty", os.O_RDONLY)
            size = shutil.get_terminal_size(fd)
            os.close(fd)
            return size.columns
        except Exception:
            return 80


@CACHE.memoize(expire=60 * 60 * 24)
def _summarize(text, model="auto"):
    model = model if model != "auto" else DEFAULT_MODEL
    question = f"rewrite this text making it as short as possible:\n\n{text}"
    return _simple(question, model=model)


@CACHE.memoize(expire=60 * 60 * 24)
def _split_task(task, model="auto"):
    model = model if model != "auto" else DEFAULT_MODEL

    tool = {
        "type": "function",
        "function": {
            "name": "split_task",
            "description": "Split a complex task into smaller, up to 30-minute subtasks formatted with prefixes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "subtasks": {
                        "type": "array",
                        "items": {"type": "string", "pattern": r"^- \\[ \\] .+?: .+"},
                        "description": "List of subtasks in markdown checkbox format.",
                    }
                },
                "required": ["subtasks"],
            },
        },
    }

    messages = [
        {"role": "system", "content": "You are my efficiency coach."},
        {
            "role": "user",
            "content": (
                "Split the following task into subtasks, each doable in 30 minutes or less.\n"
                "Format each like this: `- [ ] category: detail`\n"
                "All subtasks must share a common category.\n\n"
                f"Task:\n{task}"
            ),
        },
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=[tool],
        tool_choice="auto",
    )

    tool_call = response.choices[0].message.tool_calls[0]
    args = json.loads(tool_call.function.arguments)
    return "\n".join(args["subtasks"])


def bat(content, language="python"):
    bat_path = shutil.which("bat")
    proc = Popen([bat_path, "--color", COLOR, "-ppl", language], stdin=PIPE)
    proc.communicate(input=content.encode())


@app.command()
def code(
    question: str = typer.Option("", "-q", help="Specify the question or problem."),
    language: str = typer.Option("python", "-l", help="Programming language."),
    model: str = typer.Option("", "-m", help="Model to use."),
):
    """Answer a code question, optionally reading from stdin."""
    input_text = question
    if not sys.stdin.isatty():
        input_text += "\n\n" + sys.stdin.read().strip()

    model = model or DEFAULT_MODEL

    tool = {
        "type": "function",
        "function": {
            "name": "generate_code",
            "description": "Generate code based on the user's input.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "A complete solution in the given programming language.",
                    }
                },
                "required": ["code"],
            },
        },
    }

    messages = [
        {
            "role": "system",
            "content": f"You are a coding assistant for {language}. Output only valid code. Do not include explanations or comments.",
        },
        {"role": "user", "content": input_text},
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=[tool],
        tool_choice="auto",
    )

    tool_call = response.choices[0].message.tool_calls[0]
    args = json.loads(tool_call.function.arguments)
    print(format_python_code(args["code"]))


@app.command()
def summarize(model: str = typer.Option("auto", "-m", help="Model to use")):
    """Summarize text from stdin as briefly as possible."""
    text = sys.stdin.read()
    print(_summarize(text, model=model))


@app.command()
def split_task(model: str = typer.Option("auto", "-m", help="Model to use")):
    """Split a task into smaller tasks."""
    task = sys.stdin.read()
    print(_split_task(task, model=model))


@app.command()
def ask(
    question: str,
    model: str = typer.Option("", "-m", help="Model to use"),
):
    """Ask a question with optional stdin context."""
    if not sys.stdin.isatty():
        context = sys.stdin.read()
    else:
        context = "(asked from terminal)"
    model = model or DEFAULT_MODEL
    print(_simple(question + "\n\n" + context, model=model))


@app.command()
def prepare_commit_msg() -> None:
    """Generate a short commit message from a git diff read from stdin."""
    diff = sys.stdin.read().strip()
    truncated_diff = diff[:MAX_DIFF_CHARS]
    prompt = "\n".join(
        (
            "You are a meticulous software engineer writing a Git commit message from a code diff. Follow these rules **and** prepend the subject line with a relevant emoji that matches the nature of the change, for example:",
            "",
            "*   🐞, when it does a bug fix",
            "*   🔧, when it does a configuration change",
            "*   ✅, when it does add or update tests",
            "*   🔄, when it does a refactor",
            "*   ✨, when it does add a new feature",
            "*   📝, when it does add or update documentation",
            "*   🔥, when it does remove or deprecate code",
            "*   ❤️‍🩹, when it does minor tweaks / clean-up",
            "*   🚑, when it does critical hotfix",
            "*   🚀, when it does deploy stuff",
            "*   🎉, when it does begin a project",
            "",
            "**Commit message format:**",
            "",
            "*   First line (subject): Emoji + imperative sentence, max 50 characters",
            "*   Follow with a blank line",
            "*   Body (optional): Wrap at 72 characters, describe:",
            "    *   *What* the change is",
            "    *   *Why* it was made",
            "    *   *How* it works (if not obvious)",
            "Do **not** reference issue numbers or include diff summaries.",
            "Here is the diff:",
            "```",
            truncated_diff,
            "```",
        )
    )
    message = _simple(prompt, temperature=0.3)
    print(message.strip())


if __name__ == "__main__":
    app()
