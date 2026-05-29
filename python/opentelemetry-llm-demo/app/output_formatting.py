import re


MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+)\)")
BARE_URL_RE = re.compile(r"https?://\S+")
SOURCE_PAREN_RE = re.compile(r"\s*\((?:[A-Za-z0-9.-]+\.[A-Za-z]{2,}|source:[^)]+)\)\s*")
EXTRA_BLANK_LINES_RE = re.compile(r"\n{3,}")
SPACE_BEFORE_PUNCT_RE = re.compile(r"\s+([.,;:!?])")
MULTISPACE_RE = re.compile(r"[ \t]{2,}")
DANGLING_AND_RE = re.compile(r"\b(?:and|or)\s+([.,;:!?])")
DANGLING_SOURCE_SENTENCE_RE = re.compile(
    r"(?:^|(?<=\s))(?:more at|see also|source|sources)(?:[: ]+)?[.?!]",
    re.IGNORECASE,
)


def sanitize_agent_message(message: str) -> str:
    # keep the human-readable label from markdown links, but drop the URL itself
    sanitized = MARKDOWN_LINK_RE.sub(r"\1", message)

    # strip any bare URLs the model may still emit
    sanitized = BARE_URL_RE.sub("", sanitized)

    # clean up leftover source-only parentheticals after link removal
    sanitized = SOURCE_PAREN_RE.sub(" ", sanitized)

    # normalize spacing that gets awkward after the removals above
    sanitized = MULTISPACE_RE.sub(" ", sanitized)
    sanitized = DANGLING_AND_RE.sub(r"\1", sanitized)
    sanitized = SPACE_BEFORE_PUNCT_RE.sub(r"\1", sanitized)
    sanitized = DANGLING_SOURCE_SENTENCE_RE.sub("", sanitized)
    sanitized = EXTRA_BLANK_LINES_RE.sub("\n\n", sanitized)

    return sanitized.strip()
