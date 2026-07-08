from __future__ import annotations


class VideoForgeError(Exception):
    pass


class ConfigError(VideoForgeError):
    pass


class TTSConnectionError(VideoForgeError):
    pass


class TTSTimeoutError(VideoForgeError):
    pass


class TTSGenerationError(VideoForgeError):
    pass


class GitHubAuthError(VideoForgeError):
    pass


class GitHubNetworkError(VideoForgeError):
    pass


class GitHubNotFoundError(VideoForgeError):
    pass


class RenderError(VideoForgeError):
    pass


class VideoReviewError(VideoForgeError):
    pass


class PipelineError(VideoForgeError):
    pass


class WebhookAuthError(VideoForgeError):
    pass


class KillSwitchError(VideoForgeError):
    pass
