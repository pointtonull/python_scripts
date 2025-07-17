import re


PROMPT_SEPARATORS = {
    "zsh": re.compile(r"^[±%] "),
    "bash": re.compile(r"^[^\s]*?@.*?:.*?[#\$] "),
    "mantener": re.compile(r"^-+ retry$"),
    "pytest-watch": re.compile(r"^=+ test session starts"),
}

def split_prompts(lines):
    chunk = []
    for line in lines:
        for separator in PROMPT_SEPARATORS.values():
            if separator.match(line):
                yield chunk
                chunk = [line]
                break
        else:
            chunk.append(line)
    yield chunk


# {filename}:{lineno}:{error}:{message}
RE_WILD_ERRORS = [
        re.compile(  # Standard tracebak without line content
           r"^\s*File \"(?P<filename>.+?)\", line (?P<lineno>\d+), in (?P<context>.*)$",
           flags=re.MULTILINE,
        ),
        re.compile(  # standard traceback with line content
            r"^\s*File \"(?P<filename>.+?)\", line (?P<lineno>\d+), in (?P<context>.*?)\n\s*(?!File)(?P<message>.*)",
            flags=re.MULTILINE,
        ),
        re.compile(  # SyntaxError
            r'^\s*File "(?P<filename>.+?)", line (?P<lineno>\d+)\s'
            r'^\s*(?P<context>.*?)\n'
            r'^[\s^]*\n'
            r'(?P<message>.*)',
            flags=re.MULTILINE,
        ),
        re.compile(  # Pytest warning without context
            # tests/test_payload_power_toggle.py:28: 
            # _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

            # shouldn't match:
            # bf58.7ff84feee640 2023-08-22 23:13:46,063 - botocore.hooks - DEBUG - Changing event name from docs.*.logs.CreateExportTask.complete-section to docs.*.cloudwatch-logs.CreateExportTask.complete-section
            r'^\s*(?P<filename>.+?):(?P<lineno>\d+):[\s\n]+(?P<error>[^\n]*)\n'
            r'(?P<message>)(?P<context>)',
            flags=re.MULTILINE,
        ),
        # re.compile(  # Pytest warning
        #     #   /path/file.py:6: DeprecationWarning: invalid escape sequence '\\g'
        #     #     line = line + "new"
        #     r'^\s*(?P<filename>.+?):(?P<lineno>\d+):\s*(?P<error>[^\n\s]+)\n'
        #     r'(?P<message>.+)(?P<context>)',
        #     flags=re.MULTILINE,
        # ),
        re.compile(  # Terraform
            # │ Error: Reference to undeclared resource
            # │ 
            # │   on ../../app/apigateawy.tf line 143, in resource "aws_lambda_function" "echo":
            # │  143:   source_code_hash = data.archive_file.lambda.output_base64sha256
            # │ 
            # │ A data resource "archive_file" "lambda" has not been declared in module.app.
            # ╵
            r'^\s*│? +?on (?P<filename>.+?) line (?P<lineno>\d+), in (?P<context>.*?):$\n.*?\n.*\n[ │]*(?P<message>.*)',
            flags=re.MULTILINE,
        ),
        re.compile(  # ipdb
            # AttributeError: 'generator' object has no attribute 'as_dict'
            # > /Users/carlos.cabrera/dev/databricks_wt/integration/tools/list_tables.py(80)main()
            #      78         query = f"SELECT * FROM {source_table_name}"
            #      79         response = source.execute(query)
            # ---> 80         data = response.as_dict()["result"]
            #      81 
            #      82         # get the table schema
            r'^>\s*(?P<filename>.+?)\((?P<lineno>\d+)\)(?P<context>.*?)$',
            flags=re.MULTILINE,
        ),
]
def extract_error_lines(text):
    start = 0
    while True:
        matches = list()
        for regex in RE_WILD_ERRORS:
            if match := regex.search(text[start:]):
                matches.append(match)
        if not matches:
            break

        match = min(matches, key=lambda m: (m.start(), -m.end()))

        start += match.end()
        groups = match.groupdict()
        filename = groups.get("filename")
        message = groups.get("message", "")
        context = groups.get("context") or " "
        lineno = groups.get("lineno")

        if "/.virtualenvs/" in filename:
            continue
        if "/usr/local/Cellar" in filename:
            continue

        line = f"{filename}:{lineno}:{context}:{message}"
        yield line
