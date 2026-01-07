"""
ASSET SNIPER - Data Refinery for B2B Tesla Leads
Version: 1.0.0

Inspired by Palantir Foundry architecture.
Transforms raw CEIDG data into precision-targeted B2B sales opportunities.

Author: BigDInc Team
"""

__version__ = "1.0.0"
__author__ = "BigDInc Team"

from .config import *
from .lead_refinery import LeadRefinery
from .gotham_engine import GothamEngine
from .scoring_matrix import ScoringMatrix
from .bigdecoder_lite import BigDecoderLite
from .main import AssetSniper

__all__ = [
    "LeadRefinery",
    "GothamEngine",
    "ScoringMatrix",
    "BigDecoderLite",
    "AssetSniper",
]
