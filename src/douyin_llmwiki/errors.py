class LLMWikiError(Exception):
    """Base class for expected user-facing failures."""


class ConfigError(LLMWikiError):
    """Configuration is missing or invalid."""


class PreflightError(LLMWikiError):
    """A required local tool or package is unavailable."""


class DownloadError(LLMWikiError):
    """Video metadata or audio could not be downloaded."""


class StorageError(LLMWikiError):
    """Audio upload, signed URL generation, or cleanup failed."""


class ASRError(LLMWikiError):
    """DashScope ASR task failed or returned invalid data."""


class SummaryError(LLMWikiError):
    """The summary model failed or returned invalid structured output."""


class ObsidianError(LLMWikiError):
    """The Obsidian vault or note output is not writable."""
