"""Production-like settings.

Authentication and multi-tenancy remain out of scope for the hackathon, but this
module refuses unsafe defaults and disables local/demo-only features.
"""
from __future__ import annotations

import os

from .base import *  # noqa: F403

DEBUG = False
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
ALLOWED_HOSTS = [host for host in os.environ["DJANGO_ALLOWED_HOSTS"].split(",") if host]
LEDGERPROOF["ENABLE_EVALUATION"] = False  # noqa: F405
