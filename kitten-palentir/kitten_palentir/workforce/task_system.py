"""Task system definitions."""

from enum import Enum


class OSINTTaskType(str, Enum):
    """OSINT task type enumeration."""

    COMPANY_RECON = "company_recon"
    DOMAIN_ANALYSIS = "domain_analysis"
    SOCIAL_MEDIA = "social_media"
    SOCIAL_INTELLIGENCE = "social_intelligence"
    DATA_AGGREGATION = "data_aggregation"
    NETWORK_ANALYSIS = "network_analysis"
    PERSON_RECON = "person_recon"
    TECHNOLOGY_ANALYSIS = "technology_analysis"

