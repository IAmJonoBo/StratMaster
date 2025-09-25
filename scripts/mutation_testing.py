#!/usr/bin/env python3
"""
Mutation Testing Implementation
Implements mutation testing and architecture quality gates as identified in GAP_ANALYSIS.md
"""

import ast
import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import argparse
import logging
import tempfile
import shutil
import random


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MutationOperator:
    """Base class for mutation operators."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.mutations_applied = 0
    
    def apply_mutation(self, node: ast.AST, source: str) -> Optional[str]:
        """Apply mutation to AST node. Return mutated source or None if not applicable."""
        raise NotImplementedError
    
    def can_mutate(self, node: ast.AST) -> bool:
        """Check if this operator can mutate the given node."""
        raise NotImplementedError


class ArithmeticOperatorMutation(MutationOperator):
    """Mutate arithmetic operators (+, -, *, /, %, **)."""
    
    MUTATIONS = {
        ast.Add: [ast.Sub, ast.Mult],
        ast.Sub: [ast.Add, ast.Mult],
        ast.Mult: [ast.Add, ast.Sub, ast.Div],
        ast.Div: [ast.Mult, ast.Sub],
        ast.Mod: [ast.Mult, ast.Div],
        ast.Pow: [ast.Mult, ast.Div]
    }
    
    def __init__(self):
        super().__init__(
            "AOR", 
            "Arithmetic Operator Replacement: Replace +, -, *, /, %, ** with each other"
        )
    
    def can_mutate(self, node: ast.AST) -> bool:
        return isinstance(node, ast.BinOp) and type(node.op) in self.MUTATIONS
    
    def apply_mutation(self, node: ast.AST, source: str) -> Optional[str]:
        if not self.can_mutate(node):
            return None
        
        original_op = type(node.op)
        possible_mutations = self.MUTATIONS[original_op]
        
        if not possible_mutations:
            return None
        
        # Choose random mutation
        new_op_class = random.choice(possible_mutations)
        node.op = new_op_class()
        
        self.mutations_applied += 1
        return ast.unparse(node) if hasattr(ast, 'unparse') else source


class ComparisonOperatorMutation(MutationOperator):
    """Mutate comparison operators (<, <=, >, >=, ==, !=)."""
    
    MUTATIONS = {
        ast.Lt: [ast.Le, ast.Gt, ast.Ge, ast.Eq, ast.NotEq],
        ast.Le: [ast.Lt, ast.Gt, ast.Ge, ast.Eq, ast.NotEq],
        ast.Gt: [ast.Ge, ast.Lt, ast.Le, ast.Eq, ast.NotEq],
        ast.Ge: [ast.Gt, ast.Lt, ast.Le, ast.Eq, ast.NotEq],
        ast.Eq: [ast.NotEq, ast.Lt, ast.Le, ast.Gt, ast.Ge],
        ast.NotEq: [ast.Eq, ast.Lt, ast.Le, ast.Gt, ast.Ge],
    }
    
    def __init__(self):
        super().__init__(
            "ROR", 
            "Relational Operator Replacement: Replace <, <=, >, >=, ==, != with each other"
        )
    
    def can_mutate(self, node: ast.AST) -> bool:
        return isinstance(node, ast.Compare) and len(node.ops) == 1 and type(node.ops[0]) in self.MUTATIONS
    
    def apply_mutation(self, node: ast.AST, source: str) -> Optional[str]:
        if not self.can_mutate(node):
            return None
        
        original_op = type(node.ops[0])
        possible_mutations = self.MUTATIONS[original_op]
        
        if not possible_mutations:
            return None
        
        # Choose random mutation
        new_op_class = random.choice(possible_mutations)
        node.ops[0] = new_op_class()
        
        self.mutations_applied += 1
        return ast.unparse(node) if hasattr(ast, 'unparse') else source


class BooleanOperatorMutation(MutationOperator):
    """Mutate boolean operators (and, or)."""
    
    def __init__(self):
        super().__init__(
            "LOR", 
            "Logical Operator Replacement: Replace 'and' with 'or' and vice versa"
        )
    
    def can_mutate(self, node: ast.AST) -> bool:
        return isinstance(node, ast.BoolOp) and isinstance(node.op, (ast.And, ast.Or))
    
    def apply_mutation(self, node: ast.AST, source: str) -> Optional[str]:
        if not self.can_mutate(node):
            return None
        
        if isinstance(node.op, ast.And):
            node.op = ast.Or()
        elif isinstance(node.op, ast.Or):
            node.op = ast.And()
        
        self.mutations_applied += 1
        return ast.unparse(node) if hasattr(ast, 'unparse') else source


class ConditionalBoundaryMutation(MutationOperator):
    """Mutate conditional boundaries (< to <=, > to >=, etc.)."""
    
    def __init__(self):
        super().__init__(
            "COR", 
            "Conditional Operator Replacement: Replace < with <=, > with >=, etc."
        )
    
    def can_mutate(self, node: ast.AST) -> bool:
        return isinstance(node, ast.Compare) and len(node.ops) == 1 and \
               isinstance(node.ops[0], (ast.Lt, ast.Le, ast.Gt, ast.Ge))
    
    def apply_mutation(self, node: ast.AST, source: str) -> Optional[str]:
        if not self.can_mutate(node):
            return None
        
        op = node.ops[0]
        if isinstance(op, ast.Lt):
            node.ops[0] = ast.Le()
        elif isinstance(op, ast.Le):
            node.ops[0] = ast.Lt()
        elif isinstance(op, ast.Gt):
            node.ops[0] = ast.Ge()
        elif isinstance(op, ast.Ge):
            node.ops[0] = ast.Gt()
        
        self.mutations_applied += 1
        return ast.unparse(node) if hasattr(ast, 'unparse') else source


class UnaryOperatorMutation(MutationOperator):
    """Mutate unary operators (not, -, +)."""
    
    def __init__(self):
        super().__init__(
            "UOR", 
            "Unary Operator Replacement: Insert/delete 'not', '-', '+' operators"
        )
    
    def can_mutate(self, node: ast.AST) -> bool:
        return isinstance(node, (ast.UnaryOp, ast.expr))
    
    def apply_mutation(self, node: ast.AST, source: str) -> Optional[str]:
        if isinstance(node, ast.UnaryOp):
            if isinstance(node.op, ast.Not):
                # Remove 'not' operator
                return ast.unparse(node.operand) if hasattr(ast, 'unparse') else source
            elif isinstance(node.op, ast.UAdd):
                # Change + to -
                return ast.unparse(ast.UnaryOp(op=ast.USub(), operand=node.operand)) if hasattr(ast, 'unparse') else source
            elif isinstance(node.op, ast.USub):
                # Change - to +
                return ast.unparse(ast.UnaryOp(op=ast.UAdd(), operand=node.operand)) if hasattr(ast, 'unparse') else source
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            # Add 'not' operator to boolean expressions
            return f"not {ast.unparse(node)}" if hasattr(ast, 'unparse') else f"not {source}"
        
        return None


class MutationTester:
    """Mutation testing framework."""
    
    def __init__(self, source_dir: str, test_command: str, test_dir: str = None):
        self.source_dir = Path(source_dir)
        self.test_command = test_command
        self.test_dir = Path(test_dir) if test_dir else None
        
        # Mutation operators
        self.operators = [
            ArithmeticOperatorMutation(),
            ComparisonOperatorMutation(),
            BooleanOperatorMutation(),
            ConditionalBoundaryMutation(),
            UnaryOperatorMutation()
        ]
        
        # Results
        self.results = {
            "total_mutants": 0,
            "killed_mutants": 0,
            "survived_mutants": 0,
            "timed_out_mutants": 0,
            "error_mutants": 0,
            "mutation_score": 0.0,
            "operators": {},
            "mutant_details": []
        }
    
    def find_python_files(self) -> List[Path]:
        """Find all Python files in source directory."""
        python_files = []
        for ext in ["*.py"]:
            python_files.extend(self.source_dir.rglob(ext))
        
        # Filter out test files and __pycache__
        filtered_files = []
        for file_path in python_files:
            if ("test" in file_path.name.lower() or
                "__pycache__" in str(file_path) or
                ".pyc" in file_path.suffix):
                continue
            filtered_files.append(file_path)
        
        return filtered_files
    
    def parse_file(self, file_path: Path) -> Optional[ast.AST]:
        """Parse Python file to AST."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            return ast.parse(source), source
        except (SyntaxError, UnicodeDecodeError, FileNotFoundError) as e:
            logger.warning(f"Could not parse {file_path}: {e}")
            return None, None
    
    def generate_mutants(self, file_path: Path) -> List[Dict[str, Any]]:
        """Generate all possible mutants for a file."""
        tree, source = self.parse_file(file_path)
        if not tree:
            return []
        
        mutants = []
        
        # Walk AST and apply mutations
        for node in ast.walk(tree):
            for operator in self.operators:
                if operator.can_mutate(node):
                    try:
                        # Create a copy of the tree for mutation
                        mutant_tree = ast.parse(source)
                        
                        # Find the corresponding node in the copy
                        for mutant_node in ast.walk(mutant_tree):
                            if (type(mutant_node) == type(node) and
                                getattr(mutant_node, 'lineno', 0) == getattr(node, 'lineno', 0) and
                                getattr(mutant_node, 'col_offset', 0) == getattr(node, 'col_offset', 0)):
                                
                                # Apply mutation
                                try:
                                    mutated_source = operator.apply_mutation(mutant_node, source)
                                    if mutated_source:
                                        mutants.append({
                                            "file": str(file_path),
                                            "operator": operator.name,
                                            "line": getattr(node, 'lineno', 0),
                                            "column": getattr(node, 'col_offset', 0),
                                            "original_source": source,
                                            "mutated_source": ast.unparse(mutant_tree) if hasattr(ast, 'unparse') else mutated_source,
                                            "description": f"{operator.description} at line {getattr(node, 'lineno', 0)}"
                                        })
                                        break
                                except Exception as e:
                                    logger.debug(f"Failed to apply {operator.name} mutation: {e}")
                                    
                    except Exception as e:
                        logger.debug(f"Failed to generate mutant with {operator.name}: {e}")
        
        return mutants
    
    def run_tests(self, timeout: int = 60) -> Dict[str, Any]:
        """Run test suite and return results."""
        try:
            # Run test command with timeout
            result = subprocess.run(
                self.test_command.split(),
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.source_dir.parent
            )
            
            return {
                "status": "passed" if result.returncode == 0 else "failed",
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "timed_out": False
            }
            
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "returncode": -1,
                "stdout": "",
                "stderr": "Test execution timed out",
                "timed_out": True
            }
        except Exception as e:
            return {
                "status": "error",
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "timed_out": False
            }
    
    def test_mutant(self, mutant: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
        """Test a single mutant by applying mutation and running tests."""
        file_path = Path(mutant["file"])
        
        # Create backup of original file
        backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
        
        try:
            # Backup original file
            shutil.copy2(file_path, backup_path)
            
            # Apply mutation
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(mutant["mutated_source"])
            
            # Run tests
            test_result = self.run_tests(timeout)
            
            # Determine mutant status
            if test_result["timed_out"]:
                status = "timeout"
            elif test_result["status"] == "error":
                status = "error"
            elif test_result["status"] == "failed":
                status = "killed"  # Test failed, mutant was killed
            else:
                status = "survived"  # Test passed, mutant survived
            
            return {
                "status": status,
                "test_result": test_result,
                "mutant": mutant
            }
            
        except Exception as e:
            logger.error(f"Error testing mutant {mutant['file']}:{mutant['line']}: {e}")
            return {
                "status": "error",
                "test_result": {"stderr": str(e)},
                "mutant": mutant
            }
        
        finally:
            # Restore original file
            try:
                if backup_path.exists():
                    shutil.copy2(backup_path, file_path)
                    backup_path.unlink()
            except Exception as e:
                logger.error(f"Error restoring {file_path}: {e}")
    
    def run_mutation_testing(self, max_mutants: int = None, timeout: int = 30) -> Dict[str, Any]:
        """Run complete mutation testing process."""
        logger.info("🧬 Starting mutation testing...")
        
        # First, verify tests pass on original code
        logger.info("🧪 Running baseline tests...")
        baseline_result = self.run_tests(timeout=60)
        
        if baseline_result["status"] != "passed":
            logger.error("❌ Baseline tests failed. Cannot proceed with mutation testing.")
            return {
                "error": "Baseline tests failed",
                "baseline_result": baseline_result
            }
        
        logger.info("✅ Baseline tests passed")
        
        # Find all Python files
        python_files = self.find_python_files()
        logger.info(f"Found {len(python_files)} Python files to mutate")
        
        # Generate all mutants
        all_mutants = []
        for file_path in python_files:
            file_mutants = self.generate_mutants(file_path)
            all_mutants.extend(file_mutants)
            logger.info(f"Generated {len(file_mutants)} mutants for {file_path.name}")
        
        total_mutants = len(all_mutants)
        if max_mutants and total_mutants > max_mutants:
            # Randomly sample mutants
            all_mutants = random.sample(all_mutants, max_mutants)
            logger.info(f"Randomly selected {max_mutants} mutants from {total_mutants} total")
        
        logger.info(f"Testing {len(all_mutants)} mutants...")
        
        # Test each mutant
        killed = 0
        survived = 0
        timeouts = 0
        errors = 0
        
        for i, mutant in enumerate(all_mutants):
            logger.info(f"Testing mutant {i+1}/{len(all_mutants)}: {mutant['operator']} in {Path(mutant['file']).name}:{mutant['line']}")
            
            result = self.test_mutant(mutant, timeout)
            
            if result["status"] == "killed":
                killed += 1
                logger.debug(f"✅ Mutant killed: {mutant['description']}")
            elif result["status"] == "survived":
                survived += 1
                logger.warning(f"🚨 Mutant survived: {mutant['description']}")
            elif result["status"] == "timeout":
                timeouts += 1
                logger.warning(f"⏰ Mutant timed out: {mutant['description']}")
            else:  # error
                errors += 1
                logger.error(f"❌ Mutant error: {mutant['description']}")
            
            # Store detailed result
            self.results["mutant_details"].append({
                "mutant": mutant,
                "status": result["status"],
                "test_output": result.get("test_result", {}).get("stderr", "")[:200]  # Truncate
            })
        
        # Calculate mutation score
        valid_mutants = killed + survived  # Exclude timeouts and errors
        mutation_score = (killed / valid_mutants * 100) if valid_mutants > 0 else 0
        
        # Update results
        self.results.update({
            "total_mutants": len(all_mutants),
            "killed_mutants": killed,
            "survived_mutants": survived,
            "timed_out_mutants": timeouts,
            "error_mutants": errors,
            "mutation_score": mutation_score,
            "valid_mutants": valid_mutants
        })
        
        # Operator statistics
        for operator in self.operators:
            self.results["operators"][operator.name] = {
                "name": operator.name,
                "description": operator.description,
                "mutations_applied": operator.mutations_applied
            }
        
        logger.info(f"\n🧬 Mutation Testing Results:")
        logger.info(f"  Total Mutants: {len(all_mutants)}")
        logger.info(f"  Killed: {killed}")
        logger.info(f"  Survived: {survived}")
        logger.info(f"  Timeouts: {timeouts}")
        logger.info(f"  Errors: {errors}")
        logger.info(f"  Mutation Score: {mutation_score:.1f}%")
        
        return self.results


class ArchitectureQualityGates:
    """Architecture quality gates implementation."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.thresholds = {
            "mutation_score": 75.0,          # Minimum mutation score %
            "test_coverage": 80.0,           # Minimum test coverage %
            "cyclomatic_complexity": 10,     # Maximum complexity per function
            "dependency_cycles": 0,          # Maximum dependency cycles
            "security_issues": 0,            # Maximum security issues
            "code_duplication": 5.0          # Maximum code duplication %
        }
    
    def check_mutation_score(self, mutation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Check mutation score against threshold."""
        score = mutation_results.get("mutation_score", 0)
        threshold = self.thresholds["mutation_score"]
        
        return {
            "metric": "mutation_score",
            "value": score,
            "threshold": threshold,
            "passed": score >= threshold,
            "description": f"Mutation score: {score:.1f}% (threshold: {threshold}%)"
        }
    
    def check_test_coverage(self) -> Dict[str, Any]:
        """Check test coverage using coverage.py."""
        try:
            # Run coverage report
            result = subprocess.run(
                ["python", "-m", "coverage", "report", "--show-missing"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            # Parse coverage percentage
            coverage_percent = 0.0
            for line in result.stdout.split('\n'):
                if 'TOTAL' in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        coverage_str = parts[-1].rstrip('%')
                        try:
                            coverage_percent = float(coverage_str)
                        except ValueError:
                            pass
                    break
            
            threshold = self.thresholds["test_coverage"]
            
            return {
                "metric": "test_coverage",
                "value": coverage_percent,
                "threshold": threshold,
                "passed": coverage_percent >= threshold,
                "description": f"Test coverage: {coverage_percent:.1f}% (threshold: {threshold}%)"
            }
            
        except Exception as e:
            return {
                "metric": "test_coverage",
                "value": 0,
                "threshold": self.thresholds["test_coverage"],
                "passed": False,
                "error": str(e),
                "description": f"Failed to check test coverage: {e}"
            }
    
    def run_quality_gates(self, mutation_results: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run all architecture quality gates."""
        logger.info("🏗️ Running architecture quality gates...")
        
        gates = []
        
        # Mutation testing gate
        if mutation_results:
            gates.append(self.check_mutation_score(mutation_results))
        
        # Test coverage gate
        gates.append(self.check_test_coverage())
        
        # Calculate overall status
        passed_gates = sum(1 for gate in gates if gate.get("passed", False))
        total_gates = len(gates)
        
        overall_status = {
            "gates": gates,
            "passed_gates": passed_gates,
            "total_gates": total_gates,
            "success_rate": passed_gates / total_gates * 100 if total_gates > 0 else 0,
            "overall_passed": passed_gates == total_gates,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Quality gates: {passed_gates}/{total_gates} passed")
        for gate in gates:
            status = "✅" if gate.get("passed") else "❌"
            logger.info(f"  {status} {gate['description']}")
        
        return overall_status


def main():
    """Main mutation testing runner."""
    parser = argparse.ArgumentParser(description='Run mutation testing and quality gates')
    parser.add_argument('--source-dir', required=True, help='Source directory to test')
    parser.add_argument('--test-command', required=True, help='Command to run tests')
    parser.add_argument('--max-mutants', type=int, help='Maximum number of mutants to test')
    parser.add_argument('--timeout', type=int, default=30, help='Timeout per mutant test in seconds')
    parser.add_argument('--output', help='Output JSON file for results')
    parser.add_argument('--quality-gates', action='store_true', help='Run architecture quality gates')
    
    args = parser.parse_args()
    
    logger.info("🧬 Starting Mutation Testing & Quality Gates")
    logger.info("=" * 50)
    
    try:
        # Run mutation testing
        tester = MutationTester(
            source_dir=args.source_dir,
            test_command=args.test_command
        )
        
        mutation_results = tester.run_mutation_testing(
            max_mutants=args.max_mutants,
            timeout=args.timeout
        )
        
        results = {
            "mutation_testing": mutation_results,
            "timestamp": datetime.now().isoformat()
        }
        
        # Run quality gates if requested
        if args.quality_gates:
            gates = ArchitectureQualityGates(args.source_dir)
            quality_results = gates.run_quality_gates(mutation_results)
            results["quality_gates"] = quality_results
        
        # Save results
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"📁 Results saved to: {output_path}")
        
        # Determine exit code
        mutation_score = mutation_results.get("mutation_score", 0)
        quality_passed = results.get("quality_gates", {}).get("overall_passed", True)
        
        if mutation_score >= 75 and quality_passed:
            logger.info("✅ All quality gates passed")
            return 0
        else:
            logger.warning("❌ Some quality gates failed")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Mutation testing failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())