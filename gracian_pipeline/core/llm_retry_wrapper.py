"""
LLM Retry Wrapper with Exponential Backoff

Provides resilient API calling with:
- Exponential backoff (1s, 2s, 4s delays)
- Transient error detection
- Detailed logging with context
- Request ID tracking
"""

import time
import logging
import random
from typing import Any, Dict, Optional, Callable
from openai import OpenAI, OpenAIError, APITimeoutError, APIConnectionError, RateLimitError

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry behavior."""
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 16.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter


def is_retryable_error(error: Exception) -> bool:
    """
    Determine if an error is transient and worth retrying.

    Args:
        error: Exception that occurred

    Returns:
        True if error is retryable (transient)
    """
    # OpenAI-specific transient errors
    if isinstance(error, (APITimeoutError, APIConnectionError, RateLimitError)):
        return True

    # Generic connection errors
    if isinstance(error, (ConnectionError, TimeoutError)):
        return True

    # Check error message for transient indicators
    error_msg = str(error).lower()
    transient_indicators = [
        'connection error',
        'timeout',
        'rate limit',
        'server error',
        '500',
        '502',
        '503',
        '504',
        'temporarily unavailable'
    ]

    return any(indicator in error_msg for indicator in transient_indicators)


def calculate_backoff_delay(
    attempt: int,
    config: RetryConfig
) -> float:
    """
    Calculate exponential backoff delay with optional jitter.

    Args:
        attempt: Current attempt number (0-indexed)
        config: Retry configuration

    Returns:
        Delay in seconds
    """
    # Exponential backoff: base_delay * (2 ^ attempt)
    delay = min(config.base_delay * (2 ** attempt), config.max_delay)

    # Add jitter to prevent thundering herd
    if config.jitter:
        delay = delay * (0.5 + random.random() * 0.5)  # 50-100% of delay

    return delay


def call_llm_with_retry(
    client: OpenAI,
    model: str,
    messages: list,
    temperature: float = 0,
    timeout: int = 30,
    config: Optional[RetryConfig] = None,
    context: Optional[Dict[str, Any]] = None
) -> Any:
    """
    Call OpenAI API with exponential backoff retry logic.

    Args:
        client: OpenAI client instance
        model: Model name (e.g., "gpt-4o")
        messages: Chat messages
        temperature: Sampling temperature
        timeout: Request timeout in seconds
        config: Retry configuration (uses default if None)
        context: Additional context for logging (agent_id, pdf_path, etc.)

    Returns:
        OpenAI API response

    Raises:
        OpenAIError: If all retries exhausted
    """
    if config is None:
        config = RetryConfig()

    if context is None:
        context = {}

    last_error = None

    for attempt in range(config.max_retries):
        try:
            start_time = time.time()

            # Make API call
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                timeout=timeout
            )

            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)

            # Log successful call
            if attempt > 0:
                logger.info(
                    f"✅ LLM call succeeded on attempt {attempt + 1}/{config.max_retries} "
                    f"(latency: {latency_ms}ms, context: {context})"
                )

            return response

        except Exception as e:
            last_error = e
            latency_ms = int((time.time() - start_time) * 1000)

            # Check if error is retryable
            if not is_retryable_error(e):
                # Non-retryable error - fail immediately
                logger.error(
                    f"❌ Non-retryable LLM error: {type(e).__name__}: {e} "
                    f"(latency: {latency_ms}ms, context: {context})"
                )
                raise

            # Check if we have retries left
            if attempt < config.max_retries - 1:
                # Calculate backoff delay
                delay = calculate_backoff_delay(attempt, config)

                # Log retry with context
                logger.warning(
                    f"⚠️  LLM call failed (attempt {attempt + 1}/{config.max_retries}): "
                    f"{type(e).__name__}: {e} "
                    f"(latency: {latency_ms}ms, context: {context}) "
                    f"→ Retrying in {delay:.1f}s..."
                )

                # Wait before retry
                time.sleep(delay)
            else:
                # All retries exhausted
                logger.error(
                    f"❌ LLM call failed after {config.max_retries} attempts: "
                    f"{type(e).__name__}: {e} "
                    f"(latency: {latency_ms}ms, context: {context})"
                )

    # If we get here, all retries failed - raise the last error
    raise last_error


def call_llm_with_retry_graceful(
    client: OpenAI,
    model: str,
    messages: list,
    temperature: float = 0,
    timeout: int = 30,
    config: Optional[RetryConfig] = None,
    context: Optional[Dict[str, Any]] = None
) -> Optional[Any]:
    """
    Call OpenAI API with exponential backoff retry logic (graceful degradation).

    This version returns None on failure instead of raising an exception.
    Useful for non-critical agents where partial extraction is acceptable.

    Args:
        client: OpenAI client instance
        model: Model name (e.g., "gpt-4o")
        messages: Chat messages
        temperature: Sampling temperature
        timeout: Request timeout in seconds
        config: Retry configuration (uses default if None)
        context: Additional context for logging

    Returns:
        OpenAI API response or None on failure
    """
    try:
        return call_llm_with_retry(
            client=client,
            model=model,
            messages=messages,
            temperature=temperature,
            timeout=timeout,
            config=config,
            context=context
        )
    except Exception as e:
        logger.error(f"❌ LLM call failed gracefully: {e} (context: {context})")
        return None


# Convenience function for testing
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()

    print("Testing LLM retry wrapper...")

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Test successful call
    print("\n1. Testing successful call...")
    try:
        response = call_llm_with_retry(
            client=client,
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello' in Swedish."}
            ],
            context={"test": "successful_call"}
        )
        print(f"✅ Success: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ Failed: {e}")

    # Test with invalid API key (will retry but fail)
    print("\n2. Testing retry with invalid API key...")
    bad_client = OpenAI(api_key="invalid_key")
    try:
        response = call_llm_with_retry(
            client=bad_client,
            model="gpt-4o",
            messages=[
                {"role": "user", "content": "Test"}
            ],
            config=RetryConfig(max_retries=2),  # Fast test
            context={"test": "invalid_key"}
        )
        print(f"✅ Unexpected success: {response}")
    except Exception as e:
        print(f"✅ Expected failure after retries: {type(e).__name__}")

    # Test graceful degradation
    print("\n3. Testing graceful degradation...")
    response = call_llm_with_retry_graceful(
        client=bad_client,
        model="gpt-4o",
        messages=[{"role": "user", "content": "Test"}],
        config=RetryConfig(max_retries=2),
        context={"test": "graceful_degradation"}
    )
    if response is None:
        print("✅ Graceful degradation: returned None as expected")
    else:
        print(f"❌ Expected None, got: {response}")

    print("\n✅ All tests complete!")
