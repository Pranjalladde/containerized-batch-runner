import time

def run_with_retries(operation, max_attempts=3, backoff_seconds=1.0, sleep=time.sleep):
    """Retry an operation using exponential backoff; return (result, attempts)."""
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    if backoff_seconds < 0:
        raise ValueError("backoff_seconds cannot be negative")
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            return operation(), attempt
        except Exception as exc:
            last_error = exc
            if attempt == max_attempts:
                break
            sleep(backoff_seconds * (2 ** (attempt - 1)))
    raise RuntimeError(f"Operation failed after {max_attempts} attempts: {last_error}") from last_error
