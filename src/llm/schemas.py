from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

class PricingModelEnum(str, Enum):
    FREE = "FREE"
    FREEMIUM = "FREEMIUM"
    PAID = "PAID"
    ENTERPRISE = "ENTERPRISE"

class SourceInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str
    url: str

class StartupContentData(BaseModel):
    model_config = ConfigDict(extra="ignore")
    employeeCount: Optional[int] = None

class StartupContent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    entityName: str
    data: StartupContentData = Field(default_factory=StartupContentData)

class StartupEntity(BaseModel):
    model_config = ConfigDict(extra="ignore")
    schemaVersion: str = "1.0"
    recordType: str = "STARTUP"
    source: SourceInfo
    content: StartupContent
    collectedAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @field_validator("recordType")
    @classmethod
    def validate_record_type(cls, v: str) -> str:
        if v != "STARTUP":
            raise ValueError("recordType must be fixed to 'STARTUP'")
        return v

class ProductContent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    startupName: str
    pricingModel: PricingModelEnum = PricingModelEnum.FREE

class ProductEntity(BaseModel):
    model_config = ConfigDict(extra="ignore")
    schemaVersion: str = "1.0"
    recordType: str = "PRODUCT"
    source: SourceInfo
    content: ProductContent
    collectedAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @field_validator("recordType")
    @classmethod
    def validate_record_type(cls, v: str) -> str:
        if v != "PRODUCT":
            raise ValueError("recordType must be fixed to 'PRODUCT'")
        return v

class ResearchPaperContent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    title: str
    authors: List[str] = Field(default_factory=list)
    paper_url: str
    github_url: Optional[str] = None
    github_stars: Optional[int] = None
    published_date: str

class ResearchPaperEntity(BaseModel):
    model_config = ConfigDict(extra="ignore")
    schemaVersion: str = "1.0"
    recordType: str = "RESEARCH_PAPER"
    content: ResearchPaperContent
    collectedAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @field_validator("recordType")
    @classmethod
    def validate_record_type(cls, v: str) -> str:
        if v != "RESEARCH_PAPER":
            raise ValueError("recordType must be fixed to 'RESEARCH_PAPER'")
        return v

class JobContent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    company: str
    date: str
    is_remote: bool = False
    role_family: str = "Engineering"

class JobEntity(BaseModel):
    model_config = ConfigDict(extra="ignore")
    schemaVersion: str = "1.0"
    recordType: str = "JOB"
    source_url: str
    source_name: str
    content: JobContent
    collectedAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @field_validator("recordType")
    @classmethod
    def validate_record_type(cls, v: str) -> str:
        if v != "JOB":
            raise ValueError("recordType must be fixed to 'JOB'")
        return v

class NewsContent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    title: str
    published_date: str
    summary: Optional[str] = None

class NewsEntity(BaseModel):
    model_config = ConfigDict(extra="ignore")
    schemaVersion: str = "1.0"
    recordType: str = "NEWS"
    source: SourceInfo
    content: NewsContent
    collectedAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @field_validator("recordType")
    @classmethod
    def validate_record_type(cls, v: str) -> str:
        if v != "NEWS":
            raise ValueError("recordType must be fixed to 'NEWS'")
        return v

class EntityMappingLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    raw_name: str
    canonical_name: str
    method: str
    confidence: float
    source_url: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
