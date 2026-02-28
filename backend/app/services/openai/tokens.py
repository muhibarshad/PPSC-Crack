"""
Token Counting Utilities (tiktoken)
====================================
Provides accurate token counting for context-window management.
"""

from __future__ import annotations

import logging
from functools import lru_cache

import tiktoken

logger = logging.getLogger(__name__)

# ── Encoder Cache ────────────────────────────────────────────

@lru_cache(maxsize=8)
def _get_encoding(model: str) -> tiktoken.Encoding:
    """Return the tiktoken encoding for *model*, with fallback to cl100k_base."""
    try:
        return tiktoken.encoding_for_model(model)
    except KeyError:
        logger.warning("tiktoken: no encoding for model %r — using cl100k_base", model)
        return tiktoken.get_encoding("cl100k_base")


# ── Public API ───────────────────────────────────────────────

def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """Count the number of tokens in *text* for the given *model*.

    Parameters
    ----------
    text:
        Raw text string (user prompt, system message, etc.).
    model:
        OpenAI model name — used to select the correct BPE encoding.

    Returns
    -------
    int
        Number of tokens.
    """
    enc = _get_encoding(model)
    return len(enc.encode(text))


def count_messages_tokens(
    messages: list[dict[str, str]],
    model: str = "gpt-4o",
) -> int:
    """Estimate token count for a chat-completion *messages* array.

    Follows the OpenAI token-counting recipe:
    - every message: ``<|start|>{role/name}\\n{content}<|end|>\\n``  → +4 tokens
    - every reply is primed with ``<|start|>assistant<|message|>``   → +3 tokens
    """
    enc = _get_encoding(model)

    tokens_per_message = 4  # <|start|>{role/name}\n{content}<|end|>\n
    tokens_per_reply = 3    # <|start|>assistant<|message|>

    total = 0
    for msg in messages:
        total += tokens_per_message
        for key, value in msg.items():
            total += len(enc.encode(str(value)))
            if key == "name":
                total += -1  # role is omitted when name is present
    total += tokens_per_reply
    return total


def truncate_to_token_limit(
    text: str,
    max_tokens: int,
    model: str = "gpt-4o",
    *,
    suffix: str = "\n…[truncated]",
) -> str:
    """Truncate *text* so it fits within *max_tokens*.

    If the text already fits, it is returned unchanged.
    Otherwise it is sliced at the token boundary and *suffix* is appended.
    """
    enc = _get_encoding(model)
    token_ids = enc.encode(text)

    if len(token_ids) <= max_tokens:
        return text

    suffix_ids = enc.encode(suffix)
    keep = max_tokens - len(suffix_ids)
    if keep < 1:
        return suffix

    truncated = enc.decode(token_ids[:keep])
    return truncated + suffix
