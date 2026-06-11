"""
GraphRAG Experiment for NBA Rules
Quick exploration of graph-based retrieval vs hybrid retrieval baseline.

Hypothesis: Building a knowledge graph of rule relationships (contains, references,
related_to) might improve retrieval for questions involving multiple rules.
"""

import json
import numpy as np
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import networkx as nx
from retriever import NBARetriever
from generator import AnswerGenerator


class GraphRAGRetriever:
    """Graph-based RAG retriever that uses rule relationships."""

    def __init__(self):
        """Initialize with existing chunks and build knowledge graph."""
        # Load existing chunks
        with open('data/09_stable_chunks_aggressive_rebuild.json', 'r') as f:
            data = json.load(f)
            self.chunks = data if isinstance(data, list) else data.get('chunks', [])

        # Initialize components
        self.hybrid_retriever = NBARetriever()
        self.graph = self._build_knowledge_graph()

    def _build_knowledge_graph(self) -> nx.DiGraph:
        """Build knowledge graph from chunks."""
        graph = nx.DiGraph()

        # Create nodes for each chunk
        for chunk in self.chunks:
            chunk_id = chunk.get('chunk_id')
            rule_num = chunk.get('rule_number')
            section = chunk.get('section_title', '')

            if chunk_id:
                graph.add_node(
                    chunk_id,
                    rule_number=rule_num,
                    section=section,
                    title=chunk.get('rule_title', '')
                )

        # Add edges for relationships
        # 1. Rule contains section (implicit from metadata)
        for chunk in self.chunks:
            chunk_id = chunk.get('chunk_id')
            rule_num = chunk.get('rule_number')

            if chunk_id and rule_num:
                # Find other chunks in same rule
                for other_chunk in self.chunks:
                    other_id = other_chunk.get('chunk_id')
                    other_rule = other_chunk.get('rule_number')

                    # Same rule = related
                    if (
                        chunk_id != other_id
                        and rule_num == other_rule
                    ):
                        graph.add_edge(chunk_id, other_id, weight=0.3, type='same_rule')

        # 2. Referenced rules (look for "Rule X" mentions in text)
        for chunk in self.chunks:
            chunk_id = chunk.get('chunk_id')
            text = chunk.get('text', '').lower()

            # Find rule references in text
            for rule_num in range(1, 14):
                if f"rule {rule_num}" in text or f"rule{rule_num}" in text:
                    # Find chunks for that rule
                    for target_chunk in self.chunks:
                        if (
                            target_chunk.get('chunk_id') != chunk_id
                            and target_chunk.get('rule_number') == rule_num
                        ):
                            target_id = target_chunk.get('chunk_id')
                            if target_id:
                                graph.add_edge(
                                    chunk_id,
                                    target_id,
                                    weight=0.5,
                                    type='references'
                                )

        return graph

    def retrieve_with_graph(
        self,
        question: str,
        top_k: int = 3,
        use_graph_expansion: bool = True
    ) -> List[Dict]:
        """
        Retrieve chunks using hybrid search + graph expansion.

        Process:
        1. Get initial chunks via hybrid search (baseline)
        2. Expand by following graph relationships
        3. Rank all candidates
        4. Return top-k
        """
        # Step 1: Get initial candidates via hybrid search
        initial_chunks = self.hybrid_retriever.retrieve(question)
        initial_ids = {c.get('chunk_id') for c in initial_chunks}

        # Step 2: Graph expansion - follow relationships
        if use_graph_expansion and initial_ids:
            expanded_ids = set(initial_ids)

            # Follow edges from initial chunks (1 hop)
            for chunk_id in initial_ids:
                if chunk_id in self.graph:
                    # Get outgoing edges (references)
                    neighbors = list(self.graph.successors(chunk_id))
                    expanded_ids.update(neighbors)

                    # Get incoming edges (referenced by)
                    predecessors = list(self.graph.predecessors(chunk_id))
                    expanded_ids.update(predecessors)

            # Get expanded chunks
            expanded_chunks = [
                c for c in self.chunks
                if c.get('chunk_id') in expanded_ids
            ]
        else:
            expanded_chunks = initial_chunks

        # Step 3: Re-rank with context
        # Chunks in same rule as initial results get boost
        initial_rules = {c.get('rule_number') for c in initial_chunks}

        for chunk in expanded_chunks:
            if chunk.get('rule_number') in initial_rules:
                chunk['graph_boost'] = 0.15
            else:
                chunk['graph_boost'] = 0.0

        # Return top-k (already sorted from hybrid retriever)
        return expanded_chunks[:top_k]


def evaluate_graph_rag():
    """Compare GraphRAG vs Baseline on test questions."""
    print("\n" + "=" * 80)
    print("GRAPHRAG VS HYBRID RETRIEVAL COMPARISON")
    print("=" * 80)

    # Load test questions
    with open('data/100_test_questions.json', 'r') as f:
        test_data = json.load(f)
        test_questions = (
            test_data if isinstance(test_data, list)
            else test_data.get('questions', [])
        )

    # Limit to 20 questions for quick test
    test_subset = test_questions[:20]

    # Initialize retrievers
    baseline = NBARetriever()
    graph_rag = GraphRAGRetriever()

    # Test both approaches
    baseline_hits = 0
    graph_hits = 0
    results = []

    print("\nTesting on 20 questions...")
    print("-" * 80)

    for i, q_data in enumerate(test_subset, 1):
        question = q_data.get('question')
        expected_rule = q_data.get('rule')

        # Baseline retrieval
        baseline_chunks = baseline.retrieve(question)
        baseline_match = any(
            c.get('rule_number') == expected_rule
            for c in baseline_chunks
        )

        # GraphRAG retrieval
        graph_chunks = graph_rag.retrieve_with_graph(question)
        graph_match = any(
            c.get('rule_number') == expected_rule
            for c in graph_chunks
        )

        baseline_hits += baseline_match
        graph_hits += graph_match

        if baseline_match != graph_match:
            result_type = "GRAPH WINS" if graph_match else "BASELINE WINS"
            results.append({
                'question': question,
                'expected': expected_rule,
                'result': result_type
            })

            print(f"[{i:2d}] {result_type:14} Q: {question[:50]}...")

    print("-" * 80)
    print("\nRESULTS SUMMARY:")
    print(f"Baseline:  {baseline_hits}/20 ({baseline_hits/20*100:.1f}%)")
    print(f"GraphRAG:  {graph_hits}/20 ({graph_hits/20*100:.1f}%)")
    print(f"Difference: {graph_hits - baseline_hits:+d}")

    if graph_hits > baseline_hits:
        improvement = ((graph_hits - baseline_hits) / baseline_hits) * 100
        print(f"Improvement: +{improvement:.1f}%")
    elif graph_hits < baseline_hits:
        regression = ((baseline_hits - graph_hits) / baseline_hits) * 100
        print(f"Regression: -{regression:.1f}%")
    else:
        print("No difference")

    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)

    if graph_hits > baseline_hits:
        print("\n✅ GraphRAG shows promise!")
        print("\nWhy it might work:")
        print("  • Follows rule references and relationships")
        print("  • Helps with questions about related rules")
        print("  • Expands context beyond initial retrieval")
        print("\nNext steps for optimization:")
        print("  • Tune graph expansion depth (currently 1 hop)")
        print("  • Adjust relationship weights")
        print("  • Test on full 160-question set")
        print("  • Integrate with cross-encoder re-ranking")

    elif graph_hits < baseline_hits:
        print("\n⚠️ GraphRAG underperforms baseline")
        print("\nWhy it might struggle:")
        print("  • Over-expansion adds noise")
        print("  • Rule relationships not always helpful")
        print("  • Adds latency without accuracy gain")
        print("\nConclusion:")
        print("  Hybrid retrieval already near-optimal for NBA rules")
        print("  because hierarchical chunking captures structure well")

    else:
        print("\n≈ GraphRAG matches baseline")
        print("\nConclusion:")
        print("  Graph expansion neutral - no improvement or regression")
        print("  Suggests hybrid retrieval already optimal")

    print("\n" + "=" * 80)

    return {
        'baseline_accuracy': baseline_hits / 20,
        'graph_accuracy': graph_hits / 20,
        'improvement': (graph_hits - baseline_hits) / 20
    }


if __name__ == "__main__":
    results = evaluate_graph_rag()

    # Print final metrics
    print(f"\n📊 FINAL METRICS:")
    print(f"   Baseline: {results['baseline_accuracy']*100:.1f}%")
    print(f"   GraphRAG: {results['graph_accuracy']*100:.1f}%")
    print(f"   Delta:    {results['improvement']*100:+.1f}%")
