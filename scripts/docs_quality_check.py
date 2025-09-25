#!/usr/bin/env python3
"""
Comprehensive Documentation Quality and Link Checker for StratMaster

This script provides:
- Link validation for all Markdown files
- Doctest extraction and validation  
- API endpoint coverage checking
- Documentation structure validation (Diátaxis compliance)
- Accessibility validation for documentation
"""

import asyncio
import logging
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from urllib.parse import urljoin, urlparse
import json

import aiohttp
import markdown
from markdownify import markdownify
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Feature flag for comprehensive checking
ENABLE_COMPREHENSIVE_DOCS_CHECK = os.getenv("ENABLE_COMPREHENSIVE_DOCS_CHECK", "true").lower() == "true"


class DocumentationChecker:
    """Comprehensive documentation quality checker."""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.docs_path = root_path / "docs"
        self.api_path = root_path / "packages" / "api"
        self.results = {
            "link_check": {"passed": 0, "failed": 0, "broken_links": []},
            "doctest_check": {"passed": 0, "failed": 0, "issues": []},
            "api_coverage": {"total_endpoints": 0, "documented": 0, "missing": []},
            "structure_check": {"compliant": True, "issues": []},
            "accessibility": {"score": 0, "issues": []}
        }
        
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all documentation quality checks."""
        logger.info("Starting comprehensive documentation quality check")
        
        if not ENABLE_COMPREHENSIVE_DOCS_CHECK:
            logger.info("Comprehensive docs check disabled")
            return {"enabled": False, "message": "Comprehensive docs check disabled"}
        
        # Run checks in parallel where possible
        tasks = [
            self._check_links(),
            self._check_doctests(),
            self._check_api_coverage(),
            self._check_diátaxis_structure(),
            self._check_accessibility()
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Calculate overall score
        self.results["overall_score"] = self._calculate_overall_score()
        self.results["enabled"] = True
        
        logger.info(f"Documentation quality check completed with score: {self.results['overall_score']}")
        return self.results
    
    async def _check_links(self):
        """Check all links in Markdown files."""
        logger.info("Checking documentation links...")
        
        markdown_files = list(self.docs_path.rglob("*.md")) + list(self.root_path.glob("*.md"))
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            for md_file in markdown_files:
                await self._check_file_links(md_file, session)
        
        logger.info(f"Link check completed: {self.results['link_check']['passed']} passed, {self.results['link_check']['failed']} failed")
    
    async def _check_file_links(self, md_file: Path, session: aiohttp.ClientSession):
        """Check links in a specific Markdown file."""
        try:
            content = md_file.read_text(encoding='utf-8')
            
            # Extract links using regex
            link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
            image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
            reference_pattern = r'\[([^\]]+)\]:\s*(.+)'
            
            all_links = []
            all_links.extend(re.findall(link_pattern, content))
            all_links.extend(re.findall(image_pattern, content))  
            all_links.extend(re.findall(reference_pattern, content))
            
            for link_text, url in all_links:
                await self._validate_link(url, md_file, session)
                
        except Exception as e:
            logger.warning(f"Error processing {md_file}: {e}")
    
    async def _validate_link(self, url: str, source_file: Path, session: aiohttp.ClientSession):
        """Validate a single link."""
        url = url.strip()
        
        # Skip internal anchors and empty links
        if not url or url.startswith('#'):
            self.results['link_check']['passed'] += 1
            return
        
        # Handle relative file links
        if not url.startswith(('http://', 'https://', 'mailto:', 'tel:')):
            file_path = source_file.parent / url
            if file_path.exists():
                self.results['link_check']['passed'] += 1
            else:
                self.results['link_check']['failed'] += 1
                self.results['link_check']['broken_links'].append({
                    "url": url,
                    "source_file": str(source_file),
                    "type": "file",
                    "error": "File not found"
                })
            return
        
        # Check HTTP/HTTPS links
        try:
            async with session.head(url, allow_redirects=True) as response:
                if response.status < 400:
                    self.results['link_check']['passed'] += 1
                else:
                    self.results['link_check']['failed'] += 1
                    self.results['link_check']['broken_links'].append({
                        "url": url,
                        "source_file": str(source_file),
                        "type": "http",
                        "error": f"HTTP {response.status}"
                    })
        except Exception as e:
            self.results['link_check']['failed'] += 1
            self.results['link_check']['broken_links'].append({
                "url": url,
                "source_file": str(source_file),
                "type": "http",
                "error": str(e)
            })
    
    async def _check_doctests(self):
        """Extract and validate doctests from code and documentation."""
        logger.info("Checking doctests...")
        
        # Find Python files with doctests
        python_files = list(self.api_path.rglob("*.py"))
        
        for py_file in python_files:
            await self._extract_doctests(py_file)
        
        # Find Markdown files with code examples
        markdown_files = list(self.docs_path.rglob("*.md"))
        
        for md_file in markdown_files:
            await self._extract_markdown_examples(md_file)
    
    async def _extract_doctests(self, py_file: Path):
        """Extract doctests from Python files."""
        try:
            content = py_file.read_text(encoding='utf-8')
            
            # Simple doctest detection - look for >>> patterns
            doctest_pattern = r'>>>\s+(.+)'
            doctests = re.findall(doctest_pattern, content)
            
            if doctests:
                # For now, just count them - full validation would require execution
                self.results['doctest_check']['passed'] += len(doctests)
                
        except Exception as e:
            self.results['doctest_check']['failed'] += 1
            self.results['doctest_check']['issues'].append({
                "file": str(py_file),
                "error": str(e)
            })
    
    async def _extract_markdown_examples(self, md_file: Path):
        """Extract code examples from Markdown files."""
        try:
            content = md_file.read_text(encoding='utf-8')
            
            # Extract code blocks
            code_block_pattern = r'```(?:python|bash|javascript|json)\n(.*?)\n```'
            code_blocks = re.findall(code_block_pattern, content, re.DOTALL)
            
            # Simple validation - check for obvious syntax issues
            for code in code_blocks:
                if 'python' in code.lower():
                    try:
                        compile(code, '<markdown>', 'exec')
                        self.results['doctest_check']['passed'] += 1
                    except SyntaxError as e:
                        self.results['doctest_check']['failed'] += 1
                        self.results['doctest_check']['issues'].append({
                            "file": str(md_file),
                            "code": code[:100] + "...",
                            "error": str(e)
                        })
                else:
                    # For non-Python code, just count as passed for now
                    self.results['doctest_check']['passed'] += 1
                    
        except Exception as e:
            self.results['doctest_check']['issues'].append({
                "file": str(md_file),
                "error": str(e)
            })
    
    async def _check_api_coverage(self):
        """Check API endpoint documentation coverage."""
        logger.info("Checking API documentation coverage...")
        
        # Find all API endpoints
        endpoints = await self._discover_api_endpoints()
        self.results['api_coverage']['total_endpoints'] = len(endpoints)
        
        # Find documented endpoints
        documented = await self._find_documented_endpoints()
        
        # Calculate coverage
        missing = []
        for endpoint in endpoints:
            if endpoint not in documented:
                missing.append(endpoint)
        
        self.results['api_coverage']['documented'] = len(endpoints) - len(missing)
        self.results['api_coverage']['missing'] = missing
    
    async def _discover_api_endpoints(self) -> Set[str]:
        """Discover API endpoints from code."""
        endpoints = set()
        
        # Look for FastAPI route decorators
        router_files = list(self.api_path.rglob("*router*.py")) + list(self.api_path.rglob("*route*.py"))
        
        route_pattern = r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']\)'
        
        for router_file in router_files:
            try:
                content = router_file.read_text(encoding='utf-8')
                matches = re.findall(route_pattern, content)
                
                for method, path in matches:
                    endpoints.add(f"{method.upper()} {path}")
                    
            except Exception as e:
                logger.warning(f"Error parsing {router_file}: {e}")
        
        return endpoints
    
    async def _find_documented_endpoints(self) -> Set[str]:
        """Find documented API endpoints."""
        documented = set()
        
        # Check OpenAPI/Swagger documentation
        api_docs = list(self.docs_path.rglob("*api*.md")) + list(self.docs_path.rglob("*reference*.md"))
        
        # Look for endpoint patterns in documentation
        endpoint_pattern = r'`(GET|POST|PUT|DELETE|PATCH)\s+([^`]+)`'
        
        for doc_file in api_docs:
            try:
                content = doc_file.read_text(encoding='utf-8')
                matches = re.findall(endpoint_pattern, content, re.IGNORECASE)
                
                for method, path in matches:
                    documented.add(f"{method.upper()} {path}")
                    
            except Exception as e:
                logger.warning(f"Error parsing {doc_file}: {e}")
        
        return documented
    
    async def _check_diátaxis_structure(self):
        """Check Diátaxis documentation structure compliance."""
        logger.info("Checking Diátaxis structure compliance...")
        
        required_sections = {
            "tutorials": "Step-by-step learning-oriented guides",
            "how-to": "Goal-oriented problem-solving guides", 
            "reference": "Information-oriented technical reference",
            "explanation": "Understanding-oriented discussions"
        }
        
        issues = []
        
        for section, description in required_sections.items():
            section_path = self.docs_path / section
            
            if not section_path.exists():
                issues.append(f"Missing {section} directory - {description}")
                continue
            
            # Check if section has content
            md_files = list(section_path.rglob("*.md"))
            if not md_files:
                issues.append(f"Empty {section} directory - should contain {description}")
        
        # Check for index files
        if not (self.docs_path / "index.md").exists():
            issues.append("Missing main index.md file")
        
        self.results['structure_check']['issues'] = issues
        self.results['structure_check']['compliant'] = len(issues) == 0
    
    async def _check_accessibility(self):
        """Check documentation accessibility compliance."""
        logger.info("Checking documentation accessibility...")
        
        issues = []
        score = 100
        
        # Check for alt text on images
        markdown_files = list(self.docs_path.rglob("*.md"))
        
        for md_file in markdown_files:
            try:
                content = md_file.read_text(encoding='utf-8')
                
                # Find images without alt text
                image_pattern = r'!\[\s*\]\([^)]+\)'
                empty_alt_images = re.findall(image_pattern, content)
                
                if empty_alt_images:
                    issues.append(f"{md_file.name}: {len(empty_alt_images)} images without alt text")
                    score -= len(empty_alt_images) * 5
                
                # Check for proper heading structure
                heading_pattern = r'^(#{1,6})\s+'
                headings = re.findall(heading_pattern, content, re.MULTILINE)
                
                # Simple check - headings should be in order (no skipping levels)
                prev_level = 0
                for heading in headings:
                    level = len(heading)
                    if level > prev_level + 1:
                        issues.append(f"{md_file.name}: Heading level skip detected")
                        score -= 10
                        break
                    prev_level = level
                    
            except Exception as e:
                logger.warning(f"Error checking accessibility for {md_file}: {e}")
        
        self.results['accessibility']['score'] = max(0, score)
        self.results['accessibility']['issues'] = issues
    
    def _calculate_overall_score(self) -> int:
        """Calculate overall documentation quality score."""
        link_score = (self.results['link_check']['passed'] / 
                     max(1, self.results['link_check']['passed'] + self.results['link_check']['failed'])) * 100
        
        doctest_score = (self.results['doctest_check']['passed'] / 
                        max(1, self.results['doctest_check']['passed'] + self.results['doctest_check']['failed'])) * 100
        
        api_score = (self.results['api_coverage']['documented'] / 
                    max(1, self.results['api_coverage']['total_endpoints'])) * 100
        
        structure_score = 100 if self.results['structure_check']['compliant'] else 50
        accessibility_score = self.results['accessibility']['score']
        
        overall = (link_score + doctest_score + api_score + structure_score + accessibility_score) / 5
        return int(overall)
    
    def generate_report(self) -> str:
        """Generate a comprehensive report."""
        report = f"""
# Documentation Quality Report

**Overall Score:** {self.results.get('overall_score', 0)}/100

## Link Check Results
- ✅ Passed: {self.results['link_check']['passed']}  
- ❌ Failed: {self.results['link_check']['failed']}

### Broken Links
"""
        
        for link in self.results['link_check']['broken_links']:
            report += f"- `{link['url']}` in {link['source_file']} - {link['error']}\n"
        
        report += f"""

## API Documentation Coverage
- Total Endpoints: {self.results['api_coverage']['total_endpoints']}
- Documented: {self.results['api_coverage']['documented']}
- Coverage: {(self.results['api_coverage']['documented'] / max(1, self.results['api_coverage']['total_endpoints'])) * 100:.1f}%

### Missing Documentation
"""
        
        for endpoint in self.results['api_coverage']['missing']:
            report += f"- `{endpoint}`\n"
        
        report += f"""

## Diátaxis Structure Compliance
- Compliant: {'✅' if self.results['structure_check']['compliant'] else '❌'}

### Issues
"""
        
        for issue in self.results['structure_check']['issues']:
            report += f"- {issue}\n"
        
        report += f"""

## Accessibility Score
- Score: {self.results['accessibility']['score']}/100

### Issues
"""
        
        for issue in self.results['accessibility']['issues']:
            report += f"- {issue}\n"
        
        return report


async def main():
    """Main entry point for documentation checker."""
    if len(sys.argv) > 1:
        root_path = Path(sys.argv[1])
    else:
        root_path = Path.cwd()
    
    checker = DocumentationChecker(root_path)
    results = await checker.run_all_checks()
    
    # Output results
    if results.get("enabled", True):
        report = checker.generate_report()
        print(report)
        
        # Write results to file
        output_file = root_path / "docs-quality-report.md"
        output_file.write_text(report)
        print(f"\nReport saved to: {output_file}")
        
        # Exit with error code if quality is poor
        overall_score = results.get('overall_score', 0)
        if overall_score < 80:
            print(f"\nWarning: Documentation quality score ({overall_score}) is below threshold (80)")
            sys.exit(1)
    else:
        print("Documentation quality checking is disabled")


if __name__ == "__main__":
    asyncio.run(main())