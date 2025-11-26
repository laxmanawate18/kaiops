#!/usr/bin/env python3
"""
KaiOPS Retry Wrapper for Google GenAI API

Adds retry logic and better error handling for Google Gemini API overload issues.
"""

import asyncio
import time
import random
from functools import wraps
from typing import Callable, Any, Optional
import logging

# Configure logging
logger = logging.getLogger(__name__)

class GoogleGenAIRetry:
    """Retry wrapper for Google GenAI API calls with exponential backoff."""

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(self.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    # Check if it's a Google GenAI overload error
                    if self._is_overload_error(e):
                        if attempt < self.max_retries:
                            delay = self._calculate_delay(attempt)
                            logger.warning(f"Google GenAI overloaded (attempt {attempt + 1}/{self.max_retries + 1}). "
                                         f"Retrying in {delay:.1f} seconds...")
                            await asyncio.sleep(delay)
                            continue
                        else:
                            logger.error(f"Google GenAI still overloaded after {self.max_retries + 1} attempts")
                            raise self._create_user_friendly_error(e)
                    else:
                        # Not an overload error, re-raise immediately
                        raise e

            # This should never be reached, but just in case
            raise last_exception

        return wrapper

    def _is_overload_error(self, exception: Exception) -> bool:
        """Check if the exception is a Google GenAI overload error."""
        error_str = str(exception).lower()
        return any(keyword in error_str for keyword in [
            '503 unavailable',
            'model is overloaded',
            'service unavailable',
            'too many requests',
            'rate limit exceeded'
        ])

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter."""
        # Exponential backoff: base_delay * 2^attempt
        delay = self.base_delay * (2 ** attempt)

        # Add jitter to prevent thundering herd
        jitter = random.uniform(0.1, 1.0) * delay * 0.1
        delay += jitter

        # Cap at max_delay
        return min(delay, self.max_delay)

    def _create_user_friendly_error(self, original_error: Exception) -> Exception:
        """Create a user-friendly error message."""
        return Exception(
            "🤖 KaiOPS is experiencing high demand right now. "
            "Google's AI service is temporarily overloaded. "
            "Please try again in a few minutes. "
            f"(Original error: {str(original_error)})"
        )

# Global retry instance
genai_retry = GoogleGenAIRetry(max_retries=3, base_delay=2.0, max_delay=30.0)

def with_genai_retry(func: Callable) -> Callable:
    """Decorator to add retry logic to Google GenAI API calls."""
    return genai_retry(func)