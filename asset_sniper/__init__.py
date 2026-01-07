"""
ASSET SNIPER - Data Refinery for B2B Tesla Leads
Version: 5.0.0 (Unified Intelligence Platform)

Inspired by Palantir Foundry architecture.
Transforms raw CEIDG data into precision-targeted B2B sales opportunities.

MODULES:
- LeadRefinery: Data cleaning and normalization
- GothamEngine: Market intelligence (M², Tax, Charger, Leasing)
- ScoringMatrix: 8-tier lead classification (S-E)
- BigDecoderLite: Template-based message generation
- UnifiedPipeline: Orchestrator for all modules

Author: BigDInc Team
"""

__version__ = "5.0.0"
__author__ = "BigDInc Team"

from .config import *
from .lead_refinery import LeadRefinery
from .gotham_engine import GothamEngine
from .scoring_matrix import ScoringMatrix, LeadDNA, generate_lead_dna
from .bigdecoder_lite import BigDecoderLite
from .unified_platform import (
    UnifiedPipeline,
    PipelineConfig,
    PipelineStats,
    ProcessingLevel,
    DNAType,
    EnrichedLead,
    process_csv_file,
)

# Backward compatibility - import from main.py
from .main import AssetSniper

__all__ = [
    # Core modules
    "LeadRefinery",
    "GothamEngine",
    "ScoringMatrix",
    "BigDecoderLite",
    # Unified platform
    "UnifiedPipeline",
    "PipelineConfig",
    "PipelineStats",
    "ProcessingLevel",
    "DNAType",
    "EnrichedLead",
    "process_csv_file",
    # DNA profiling
    "LeadDNA",
    "generate_lead_dna",
    # Legacy
    "AssetSniper",
]
