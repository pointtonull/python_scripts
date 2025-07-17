from textwrap import dedent

from pytest import mark

from src import text_utils

GOOD_MARK = "(first line marker)"
EXAMPLES = [
    dedent(
        f"""\
        [:~/programacion/python] [p3] {GOOD_MARK} 130
        % mantener pytest --pdb {GOOD_MARK}
        ==================== test session starts {GOOD_MARK} ===================
        platform darwin -- Python 3.10.11, pytest-7.3.0, pluggy-1.0.0

        ============================ short test summary info =====================
        FAILED tests/test__fetch_quickfix.py:test__split_prompts - assert False
        ===================== test session starts {GOOD_MARK} ===================
        platform darwin -- Python 3.10.11, pytest-7.3.0, pluggy-1.0.0
        rootdir: /home/programacion/python
        >>>>>>>>>>>>>> PDB post_mortem (IO-capturing turned off) >>>>>>>>>>>>>
        *** NameError: name 'pdb' is not defined
        > /home/programacion/python/tests/test__fetch_quickfix.py(2)test__split_prompts()
        -> assert False
        (Pdb) chunk
        (Pdb)
        """
    ),
]


@mark.parametrize("text", EXAMPLES)
def test__split_prompts(text):
    lines = text.splitlines()
    chunks = list(text_utils.split_prompts(lines))
    total = 0
    for chunk in chunks:
        total += len(chunk)
        assert GOOD_MARK in chunk[0]
    assert total == len(lines)
    assert text.count(GOOD_MARK) == len(chunks)


TRACEBACKS = [
    (
        dedent(
            """
                Traceback (most recent call last):
                  File "<string>", line 1, in <module>
                  ModuleNotFoundError: No module named...
        """
        ),
        ["<string>:1:<module>:ModuleNotFoundError: No module named..."],
    ),
    (
        dedent(
            """
                Traceback (most recent call last):
                File "/task.py", line 2, in function
                raise SomeError(message)
                common.exceptions.BuildException: test error
        """
        ),
        ["/task.py:2:function:raise SomeError(message)"],
    ),
    (
        dedent(
            """
                Traceback (most recent call last):
                  File "/task.py", line 3, in function
                    raise SomeError(message)
                common.exceptions.BuildException: test error
        """
        ),
        ["/task.py:3:function:raise SomeError(message)"],
    ),
    (
        dedent(
            """
                Traceback (most recent call last):
                  File "/task.py", line 4, in function
                    raise SomeError(message)
                common.exceptions.BuildException: test error
                  File "/task.py", line 5, in function
                    raise SomeError(message)
                common.exceptions.BuildException: test error
        """
        ),
        [
            "/task.py:4:function:raise SomeError(message)",
            "/task.py:5:function:raise SomeError(message)",
        ],
    ),
    (
        dedent(
            """
            src/text_utils.py:6
              /path/file.py:6: DeprecationWarning: invalid escape sequence '\\g'
                line = line + "new"

            -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
        """
        ),
        [
            "/path/file.py:6: :",
        ],
    ),
    (
        dedent(
            """
                Traceback (most recent call last):
                  File "/path/file.py", line 7, in get_frequencies
                    games = list(read_games(pgn_file))
               """
        ),
        ["/path/file.py:7:get_frequencies:games = list(read_games(pgn_file))"],
    ),
    (
        dedent(
            """
                  File "/path/file.py", line 8, in <module>
                  File "/path/file.py", line 9, in main
                    for post_id in profile["posts"]:
                  File "/path/file2.py", line 10, in bar
                    return tqdm(iterable, **settings)
               """
        ),
        [
            "/path/file.py:8:<module>:",
            '/path/file.py:9:main:for post_id in profile["posts"]:',
            "/path/file2.py:10:bar:return tqdm(iterable, **settings)",
        ],
    ),
    (
        dedent(
            """
                  File "/home/.virtualenvs/p3/lib/python3.10/site-packages/IPython/utils/py3compat.py", line 55, in execfile
                    exec(compiler(f.read(), fname, "exec"), glob, loc)
                  File "/path/file.py", line 11, in main
                    for post_id in profile["posts"]:
               """
        ),
        [
            '/path/file.py:11:main:for post_id in profile["posts"]:',
        ],
    ),
    (
        dedent(
            """
                  File "/path/command", line 12
                    return s = S()
                             ^
                SyntaxError: invalid syntax
               """
        ),
        [
            "/path/command:12:return s = S():SyntaxError: invalid syntax",
        ],
    ),
    (
        dedent(
            """
                Traceback (most recent call last)
                  File "/name.surname@mail.com//update.py", line 92, in <module>
                    exit(main())
                PermissionError: [Errno 13] Permission denied: 'user/dotfiles/.zcompdump-macky mac face-5.8.1.zwc'
                """
        ),
        [
            "/name.surname@mail.com//update.py:92:<module>:exit(main())",
        ],
    ),
    (
        dedent(
            """
╷
                │ Error: Reference to undeclared resource
                │ 
                │   on ../../app/apigateawy.tf line 143, in resource "aws_lambda_function" "echo":
                │  143:   source_code_hash = data.archive_file.lambda.output_base64sha256
                │ 
                │ A data resource "archive_file" "lambda" has not been declared in module.app.
                ╵
                ╷
                │ Error: Reference to undeclared resource
                │ 
                │   on ../../app/authorizer.tf line 44, in data "archive_file" "lambda_authorizer":
                │   44:   depends_on = [null_resource.install_dependencies]
                │ 
                │ A managed resource "null_resource" "install_dependencies" has not been declared in module.app.
                ╵
            """
        ),
        [
            '../../app/apigateawy.tf:143:resource "aws_lambda_function" "echo":A data resource "archive_file" "lambda" has not been declared in module.app.',
            '../../app/authorizer.tf:44:data "archive_file" "lambda_authorizer":A managed resource "null_resource" "install_dependencies" has not been declared in module.app.',
        ],
    ),
    (
        dedent(
            """
                tests/test_payload_power_toggle.py:18: 
            """
        ),
        ["tests/test_payload_power_toggle.py:18: :"],
    ),
    (
        dedent(
            """
                Error: 1 error occurred:
                    * all attributes must be indexed. Unused attributes: ["Role"]
                  with module.apigateway.aws_dynamodb_table.tokens,
                  on ../../apigateway/tokens.tf line 1, in resource "aws_dynamodb_table" "tokens":
                   1: resource "aws_dynamodb_table" "tokens" {
                failed to generate plan
            """
        ),
        ['../../apigateway/tokens.tf:1:resource "aws_dynamodb_table" "tokens":'],
    ),
    (
        dedent(
            """

                tests/test_payload_power_toggle.py:28: 
                _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
                tests/utils.py:244: in verify_availability
                        r = task_get(host + "/tasking/availability", headers=auth, params=params)
            """
        ),
        [
            "tests/test_payload_power_toggle.py:28: :",
            "tests/utils.py:244: :",
        ],
    ),
    (
        dedent(
            """
                bf58.7ff84feee640 2023-08-22 23:13:46,063 - botocore.hooks - DEBUG - Changing event name from docs.*.logs.CreateExportTask.complete-section to docs.*.cloudwatch-logs.CreateExportTask.complete-section
            """
        ),
        [
        ],
    ),
    (
        dedent(
            """
                tests/test_payload_power_toggle.py:40: KeyError
            """
        ),
        [
            "tests/test_payload_power_toggle.py:40: :",
        ],
    ),
]


# {filename}:{lineno}:{error}:{message}
@mark.parametrize("seen, expected", TRACEBACKS)
def test__extract_error_lines(seen, expected):
    result = list(text_utils.extract_error_lines(seen))

    result = "\n".join(result)
    expected = "\n".join(expected)

    assert expected == result
