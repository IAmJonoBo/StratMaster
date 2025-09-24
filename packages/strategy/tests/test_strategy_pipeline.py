"""Tests for strategy pipeline components."""

from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

from strategy_pipeline import (
    DocumentProcessor,
    Evidence,
    EvidenceType,
    ICEScorer,
    InitiativePortfolio,
    PIEScorer,
    StrategicInitiative,
    StrategySynthesizer,
    StrategyzerMapper,
)


class TestDocumentProcessor:
    """Test document processing functionality."""

    def test_process_markdown(self):
        """Test markdown document processing."""
        processor = DocumentProcessor()

        # Create temporary markdown file
        md_content = """
# Strategic Analysis

## Market Overview
The market is growing at 15% annually with strong demand.

## Competitive Landscape  
Three main competitors dominate the space with 60% market share.

### Key Facts
- Market size: $2.5B
- Growth rate: 15% CAGR
- Top 3 players: Company A, B, C
        """

        with NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(md_content)
            f.flush()

            doc = processor.process_file(f.name)

            assert doc.filename == Path(f.name).name
            assert doc.file_type == "markdown"
            assert len(doc.sections) >= 2
            assert any("market" in section.content.lower() for section in doc.sections)
            assert any("competitive" in section.content.lower() for section in doc.sections)

        Path(f.name).unlink()  # cleanup

    def test_entity_extraction(self):
        """Test entity extraction from text."""
        processor = DocumentProcessor()

        if processor.nlp:  # Only test if SpaCy model is available
            text = "Apple Inc. reported $100 billion revenue in 2023, competing with Microsoft and Google."
            entities = processor._extract_entities(text)

            # Should extract organizations and money
            org_entities = [e for e in entities if e.label == 'ORG']
            money_entities = [e for e in entities if e.label == 'MONEY']

            assert len(org_entities) >= 1  # At least one organization
            assert len(money_entities) >= 1  # At least one monetary value

    def test_key_facts_extraction(self):
        """Test key facts extraction."""
        processor = DocumentProcessor()

        text = """
        Our revenue grew 25% year-over-year to $50 million in 2023.
        The market size is estimated at $1.2 billion with 12% CAGR.
        We captured 15% market share in our target segment.
        Customer satisfaction scores improved to 4.8/5.0 stars.
        """

        facts = processor._extract_key_facts(text)

        assert len(facts) > 0
        assert any("25%" in fact for fact in facts)
        assert any("$50 million" in fact for fact in facts)


class TestStrategyzerMapper:
    """Test Strategyzer framework mapping."""

    def test_bmc_mapping(self):
        """Test Business Model Canvas mapping."""
        mapper = StrategyzerMapper()

        # Create mock processed document
        from strategy_pipeline.document_processor import (
            DocumentSection,
            ProcessedDocument,
        )

        sections = [
            DocumentSection(
                title="Value Proposition",
                content="Our platform provides unique AI-powered insights that help customers make better strategic decisions. This delivers significant competitive advantage and cost savings.",
                section_type="content"
            ),
            DocumentSection(
                title="Customer Segments",
                content="We target mid-market companies in technology and healthcare sectors. Our primary customers are strategy teams and C-level executives.",
                section_type="content"
            ),
            DocumentSection(
                title="Revenue Model",
                content="Revenue comes from subscription fees, professional services, and licensing. We offer tiered pricing with monthly and annual plans.",
                section_type="content"
            )
        ]

        doc = ProcessedDocument(
            filename="business_plan.md",
            file_type="markdown",
            sections=sections
        )

        bmc = mapper.map_to_bmc([doc])

        assert len(bmc.value_propositions) > 0
        assert len(bmc.customer_segments) > 0
        assert len(bmc.revenue_streams) > 0

        # Check evidence tracking
        assert "value_propositions" in bmc.evidence_sources
        assert "customer_segments" in bmc.evidence_sources
        assert "revenue_streams" in bmc.evidence_sources

    def test_vpc_mapping(self):
        """Test Value Proposition Canvas mapping."""
        mapper = StrategyzerMapper()

        from strategy_pipeline.document_processor import (
            DocumentSection,
            ProcessedDocument,
        )

        sections = [
            DocumentSection(
                title="Customer Jobs",
                content="Customers need to analyze market trends, make strategic decisions, and track competitive intelligence. They want to reduce decision-making time.",
                section_type="content"
            ),
            DocumentSection(
                title="Customer Pains",
                content="Current solutions are too complex, expensive, and time-consuming. Data is scattered across multiple tools causing frustration.",
                section_type="content"
            ),
            DocumentSection(
                title="Our Solution",
                content="Our product integrates all data sources and uses AI to generate insights automatically. This eliminates manual analysis work.",
                section_type="content"
            )
        ]

        doc = ProcessedDocument(
            filename="customer_research.md",
            file_type="markdown",
            sections=sections
        )

        vpc = mapper.map_to_vpc([doc])

        assert len(vpc.customer_jobs) > 0
        assert len(vpc.pains) > 0
        assert len(vpc.products_services) > 0

        # Check fit assessment
        assert "overall_fit" in vpc.fit_assessment
        assert vpc.fit_assessment["overall_fit"] in ["Strong Fit", "Moderate Fit", "Weak Fit"]


class TestPIEScorer:
    """Test PIE scoring system."""

    def test_pie_scoring(self):
        """Test PIE scoring with evidence."""
        scorer = PIEScorer()

        initiative = StrategicInitiative(
            id="init_001",
            title="Launch AI Analytics Platform",
            description="Develop and launch new AI-powered analytics platform",
            category="product"
        )

        evidence = {
            "potential": [
                Evidence(
                    evidence_type=EvidenceType.MARKET_RESEARCH,
                    source="Market Analysis Report 2024",
                    description="TAM of $2.5B with 15% CAGR",
                    confidence=0.8
                ),
                Evidence(
                    evidence_type=EvidenceType.FINANCIAL_DATA,
                    source="Financial Projections",
                    description="Expected ROI of 300% over 3 years",
                    confidence=0.7
                )
            ],
            "importance": [
                Evidence(
                    evidence_type=EvidenceType.STAKEHOLDER_INPUT,
                    source="CEO Strategic Priorities",
                    description="Top 3 strategic priority for 2024",
                    confidence=0.9
                )
            ],
            "ease": [
                Evidence(
                    evidence_type=EvidenceType.TECHNICAL_FEASIBILITY,
                    source="Engineering Assessment",
                    description="Requires 6 months with existing team",
                    confidence=0.6
                )
            ]
        }

        scored_initiative = scorer.score_initiative(initiative, evidence)

        assert scored_initiative.pie_score is not None
        assert 3 <= scored_initiative.pie_score.total_score <= 15
        assert 1.0 <= scored_initiative.pie_score.weighted_score <= 5.0
        assert scored_initiative.pie_score.priority_tier in ["High", "Medium", "Low"]
        assert 0.0 <= scored_initiative.pie_score.evidence_completeness <= 1.0

    def test_ice_scoring(self):
        """Test ICE scoring with evidence."""
        scorer = ICEScorer()

        initiative = StrategicInitiative(
            id="init_002",
            title="Market Expansion",
            description="Expand to European markets",
            category="growth"
        )

        evidence = {
            "impact": [
                Evidence(
                    evidence_type=EvidenceType.MARKET_RESEARCH,
                    source="European Market Study",
                    description="Potential 40% revenue increase",
                    confidence=0.8
                )
            ],
            "confidence": [
                Evidence(
                    evidence_type=EvidenceType.HISTORICAL_DATA,
                    source="Previous Expansion Results",
                    description="Successfully expanded to APAC in 2022",
                    confidence=0.7
                )
            ],
            "ease": [
                Evidence(
                    evidence_type=EvidenceType.STAKEHOLDER_INPUT,
                    source="Operations Team Assessment",
                    description="Moderate complexity, 12-month timeline",
                    confidence=0.6
                )
            ]
        }

        scored_initiative = scorer.score_initiative(initiative, evidence)

        assert scored_initiative.ice_score is not None
        assert 3 <= scored_initiative.ice_score.total_score <= 15
        assert 0.0 <= scored_initiative.ice_score.ice_score <= 1.0
        assert scored_initiative.ice_score.priority_tier in ["High", "Medium", "Low"]


class TestInitiativePortfolio:
    """Test initiative portfolio management."""

    def test_portfolio_ranking(self):
        """Test portfolio ranking functionality."""
        portfolio = InitiativePortfolio(scoring_method="PIE")

        # Create test initiatives with different scores
        from strategy_pipeline.pie_scorer import PIEScore, ScoredCriterion

        init1 = StrategicInitiative(id="1", title="High Priority", description="Test")
        init1.pie_score = PIEScore(
            potential=ScoredCriterion(name="potential", score=5),
            importance=ScoredCriterion(name="importance", score=4),
            ease=ScoredCriterion(name="ease", score=3)
        )
        init1.pie_score.calculate_scores()

        init2 = StrategicInitiative(id="2", title="Low Priority", description="Test")
        init2.pie_score = PIEScore(
            potential=ScoredCriterion(name="potential", score=2),
            importance=ScoredCriterion(name="importance", score=2),
            ease=ScoredCriterion(name="ease", score=2)
        )
        init2.pie_score.calculate_scores()

        portfolio.add_initiative(init1)
        portfolio.add_initiative(init2)

        ranked = portfolio.get_ranked_initiatives()

        assert len(ranked) == 2
        assert ranked[0].title == "High Priority"
        assert ranked[1].title == "Low Priority"

    def test_portfolio_summary(self):
        """Test portfolio summary generation."""
        portfolio = InitiativePortfolio()

        # Add some test initiatives
        init = StrategicInitiative(id="1", title="Test", description="Test")
        portfolio.add_initiative(init)

        summary = portfolio.generate_portfolio_summary()

        assert "total_initiatives" in summary
        assert summary["total_initiatives"] == 1


class TestStrategySynthesizer:
    """Test strategy synthesis functionality."""

    def test_strategy_synthesis(self):
        """Test complete strategy synthesis."""
        synthesizer = StrategySynthesizer()

        # Create mock processed documents
        from strategy_pipeline.document_processor import (
            DocumentSection,
            ProcessedDocument,
        )

        sections = [
            DocumentSection(
                title="Market Analysis",
                content="The market is growing rapidly with strong customer demand. Key trends include digital transformation and AI adoption.",
                section_type="content"
            ),
            DocumentSection(
                title="Competitive Analysis",
                content="Three main competitors exist with different positioning. We have opportunity for differentiation through AI.",
                section_type="content"
            )
        ]

        doc = ProcessedDocument(
            filename="strategic_analysis.md",
            file_type="markdown",
            sections=sections
        )

        brief = synthesizer.synthesize_strategy(
            documents=[doc],
            brief_title="Test Strategy Brief",
            authors=["Test Author"]
        )

        assert brief.title == "Test Strategy Brief"
        assert "Test Author" in brief.authors
        assert len(brief.evidence_sources) == 1
        assert brief.business_model_canvas is not None
        assert brief.value_proposition_canvas is not None
        assert len(brief.executive_summary) > 0
        assert 0.0 <= brief.completeness_score <= 1.0

    def test_markdown_export(self):
        """Test Markdown export functionality."""
        synthesizer = StrategySynthesizer()

        from strategy_pipeline.strategy_synthesizer import StrategyBrief

        brief = StrategyBrief(
            title="Test Brief",
            executive_summary="This is a test summary.",
            key_findings=["Finding 1", "Finding 2"],
            strategic_recommendations=["Recommendation 1", "Recommendation 2"]
        )

        markdown_output = synthesizer.export_brief_markdown(brief)

        assert "# Test Brief" in markdown_output
        assert "This is a test summary" in markdown_output
        assert "Finding 1" in markdown_output
        assert "Recommendation 1" in markdown_output


@pytest.fixture
def sample_documents():
    """Sample processed documents for testing."""
    from strategy_pipeline.document_processor import DocumentSection, ProcessedDocument

    return [
        ProcessedDocument(
            filename="market_research.pdf",
            file_type="pdf",
            sections=[
                DocumentSection(
                    title="Market Size",
                    content="The total addressable market is valued at $5.2 billion with projected 18% CAGR through 2028.",
                    section_type="content"
                )
            ]
        ),
        ProcessedDocument(
            filename="competitive_analysis.docx",
            file_type="docx",
            sections=[
                DocumentSection(
                    title="Competitor Overview",
                    content="Primary competitors include Company A (35% market share), Company B (25% share), and emerging players.",
                    section_type="content"
                )
            ]
        )
    ]


def test_integration_workflow(sample_documents):
    """Test complete integration workflow."""
    # Step 1: Map to frameworks
    mapper = StrategyzerMapper()
    bmc = mapper.map_to_bmc(sample_documents)
    vpc = mapper.map_to_vpc(sample_documents)

    # Step 2: Create strategic initiatives
    initiative = StrategicInitiative(
        id="int_001",
        title="Market Expansion Initiative",
        description="Expand into new market segments based on research findings"
    )

    # Step 3: Score initiatives
    pie_scorer = PIEScorer()
    evidence = {
        "potential": [
            Evidence(
                evidence_type=EvidenceType.MARKET_RESEARCH,
                source="market_research.pdf",
                description="$5.2B TAM with 18% CAGR",
                confidence=0.9
            )
        ],
        "importance": [
            Evidence(
                evidence_type=EvidenceType.STAKEHOLDER_INPUT,
                source="Strategy Team",
                description="Top strategic priority",
                confidence=0.8
            )
        ],
        "ease": [
            Evidence(
                evidence_type=EvidenceType.TECHNICAL_FEASIBILITY,
                source="Implementation Plan",
                description="6-month timeline with current resources",
                confidence=0.7
            )
        ]
    }

    scored_initiative = pie_scorer.score_initiative(initiative, evidence)

    # Step 4: Create portfolio
    portfolio = InitiativePortfolio()
    portfolio.add_initiative(scored_initiative)

    # Step 5: Synthesize strategy
    synthesizer = StrategySynthesizer()
    strategy_brief = synthesizer.synthesize_strategy(
        documents=sample_documents,
        portfolio=portfolio,
        brief_title="Integrated Strategy Analysis"
    )

    # Verify integration
    assert strategy_brief.title == "Integrated Strategy Analysis"
    assert len(strategy_brief.strategic_initiatives) == 1
    assert strategy_brief.strategic_initiatives[0].pie_score is not None
    assert strategy_brief.business_model_canvas is not None
    assert strategy_brief.value_proposition_canvas is not None
    assert len(strategy_brief.executive_summary) > 0
    assert strategy_brief.completeness_score > 0
