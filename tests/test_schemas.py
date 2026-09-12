import pytest
from pydantic import ValidationError
from src.llm.schemas import (
    StartupEntity,
    StartupContent,
    StartupContentData,
    SourceInfo,
    ProductEntity,
    ProductContent,
    PricingModelEnum,
    ResearchPaperEntity,
    ResearchPaperContent,
    JobEntity,
    JobContent,
    NewsEntity,
    NewsContent
)

def test_startup_schema_valid():
    startup = StartupEntity(
        schemaVersion="1.0",
        recordType="STARTUP",
        source=SourceInfo(name="Test Source", url="https://test.com/startup"),
        content=StartupContent(
            entityName="OpenAI",
            data=StartupContentData(employeeCount=500)
        )
    )
    assert startup.schemaVersion == "1.0"
    assert startup.recordType == "STARTUP"
    assert startup.content.entityName == "OpenAI"
    assert startup.content.data.employeeCount == 500

def test_startup_schema_invalid_record_type():
    with pytest.raises(ValidationError):
        StartupEntity(
            schemaVersion="1.0",
            recordType="INVALID_TYPE",
            source=SourceInfo(name="Test", url="https://test.com"),
            content=StartupContent(entityName="Test")
        )

def test_product_schema():
    product = ProductEntity(
        schemaVersion="1.0",
        recordType="PRODUCT",
        source=SourceInfo(name="Test Source", url="https://test.com/product"),
        content=ProductContent(
            startupName="Anthropic",
            pricingModel=PricingModelEnum.FREEMIUM
        )
    )
    assert product.recordType == "PRODUCT"
    assert product.content.pricingModel == PricingModelEnum.FREEMIUM

def test_research_paper_schema():
    paper = ResearchPaperEntity(
        schemaVersion="1.0",
        recordType="RESEARCH_PAPER",
        content=ResearchPaperContent(
            title="Attention Is All You Need",
            authors=["Vaswani et al."],
            paper_url="https://arxiv.org/abs/1706.03762",
            github_url="https://github.com/tensorflow/tensor2tensor",
            github_stars=12000,
            published_date="2017-06-12T00:00:00Z"
        )
    )
    assert paper.recordType == "RESEARCH_PAPER"
    assert paper.content.github_stars == 12000

def test_job_schema():
    job = JobEntity(
        schemaVersion="1.0",
        recordType="JOB",
        source_url="https://test.com/job/1",
        source_name="RemoteOK",
        content=JobContent(
            company="DeepMind",
            date="2026-09-12T10:00:00Z",
            is_remote=True,
            role_family="Engineering"
        )
    )
    assert job.recordType == "JOB"
    assert job.content.is_remote is True
