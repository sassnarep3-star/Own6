"""Session d713b52f — dated independent re-verification pack.

Public modules:

    capture    hash the raw transcripts, verify the capture log, and hold the
               official-source probe answers
    derive     turn the raw transcripts into the published tables. Every value
               traces back to a raw file that is hashed in the capture log.
    audit      recompute inherited published numbers from the inherited ledgers
               instead of asserting them
    model      the frozen, pre-registered baseline re-run over 121 games and the
               three Week 11 forecasts still open

No module touches the network. Network reads happen out-of-band and are
transcribed into ``data/nfl_d713b52f/raw/``; the transcription is hashed.
"""

__all__ = ["audit", "capture", "derive", "model"]
