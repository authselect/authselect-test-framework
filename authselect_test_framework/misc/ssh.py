from __future__ import annotations

from functools import wraps
from time import sleep
from typing import Any, Callable, ParamSpec

from pytest_mh.conn import ProcessError, ProcessResult

Param = ParamSpec("Param")


def retry_command(
    max_retries: int = 5,
    delay: float = 1,
    match_stdout: str | list[str] | None = None,
    match_stderr: str | list[str] | None = None,
    check_rc: bool = True,
) -> Callable[[Callable[Param, ProcessResult]], Callable[Param, ProcessResult]]:
    """
    Decorated function will be retried if its return code is non zero.

    :param max_retries: Maximum number of retry attempts, defaults to 5
    :type max_retries: int, optional
    :param delay: Delay in seconds between each retry, defaults to 1
    :type delay: float, optional
    :param match_stdout: If set, retry only of string is found in stdout, defaults to None
    :type match_stdout: str | list[str] | None, optional
    :param match_stderr: If set, retry only of string is found in stderr, defaults to None
    :type match_stderr: str | list[str] | None, optional
    :param check_rc: If True and rc == 0, do not retry.
    :type check_rc: bool
    :return: Decorated function.
    :rtype: Callable
    """

    def decorator(func: Callable[Param, ProcessResult]) -> Callable[Param, ProcessResult]:
        def _match(pattern: str | list[str], where: str) -> bool:
            if isinstance(pattern, str):
                pattern = [pattern]

            for p in pattern:
                if p in where:
                    return True

            return False

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> ProcessResult:
            error: ProcessError | None = None
            retry: int = 0
            result: ProcessResult | None = None
            while True:
                if retry >= max_retries:
                    break

                rc = 0
                stdout = ""
                stderr = ""
                try:
                    error = None
                    result = func(*args, **kwargs)
                    rc = result.rc
                    stdout = result.stdout
                    stderr = result.stderr
                except ProcessError as e:
                    error = e
                    rc = e.rc
                    stdout = e.stdout
                    stderr = e.stderr

                if check_rc and rc == 0:
                    break

                if match_stdout is not None and not _match(match_stdout, stdout):
                    break

                if match_stderr is not None and not _match(match_stderr, stderr):
                    break

                retry += 1
                sleep(delay)

            if error is not None:
                raise error

            assert result is not None
            return result

        return wrapper

    return decorator
