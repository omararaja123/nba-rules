"""
Phase 1 Optimization: Use Claude instead of GPT-3.5-turbo
Expected improvement: +10% (36-38% → 46-48%)
"""

import json
from typing import List, Dict
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# For Claude API
import anthropic

from phase4_prompts import get_system_prompt, get_user_prompt


class ClaudeRAGSystem:
    """RAG system using Claude for better rule understanding."""

    def __init__(self, model: str = "claude-opus-4-8"):
        """Initialize with Claude."""
        self.retrieval = None
        self.model = model
        self.client = anthropic.Anthropic()
        self._init_retrieval()
        print(f"✅ Claude RAG System initialized (Model: {model})")

    def _init_retrieval(self):
        """Initialize hybrid retrieval."""
        import numpy as np
        import faiss
        from rank_bm25 import BM25Okapi
        from sentence_transformers import SentenceTransformer

        # Load enhanced chunks
        with open('data/09_stable_chunks_enhanced.json', 'r') as f:
            data = json.load(f)
        self.chunks = data['chunks']

        # Load embeddings
        self.embeddings = np.load('data/10_embeddings_enhanced.npy')

        # Build FAISS
        index = faiss.IndexFlatL2(self.embeddings.shape[1])
        index.add(self.embeddings.astype(np.float32))
        self.index = index

        # Build BM25
        texts = [c['text'] for c in self.chunks]
        tokenized = [text.lower().split() for text in texts]
        self.bm25 = BM25Okapi(tokenized)

        # Encoder
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """Retrieve top chunks."""
        import numpy as np

        query_embedding = self.encoder.encode(query)
        distances, indices = self.index.search(
            np.array([query_embedding]).astype(np.float32), top_k
        )

        tokens = query.lower().split()
        bm25_scores = self.bm25.get_scores(tokens)

        results = {}
        for j, idx in enumerate(indices[0]):
            chunk = self.chunks[idx]
            rule = chunk['metadata']['rule_number']

            sim_score = 1.0 / (1.0 + distances[0][j])
            bm25_score = min(1.0, bm25_scores[idx] / 10.0)
            combined = (sim_score * 0.7) + (bm25_score * 0.3)

            if rule not in results or results[rule]['score'] < combined:
                results[rule] = {
                    'chunk': chunk,
                    'score': combined,
                    'rule': rule,
                }

        return [r['chunk'] for r in sorted(
            results.values(),
            key=lambda x: x['score'],
            reverse=True
        )[:top_k]]

    def answer_question(self, question: str, top_k: int = 5) -> Dict:
        """Answer using Claude."""
        chunks = self.retrieve(question, top_k=top_k)

        if not chunks:
            return {
                'question': question,
                'answer': 'I could not find relevant information.',
                'citations': [],
                'model': self.model,
            }

        # Format context
        context = 'Retrieved NBA Rules Excerpts:\n'
        context += '=' * 80 + '\n\n'
        for i, chunk in enumerate(chunks, 1):
            meta = chunk['metadata']
            citation = f"Rule {meta['rule_number']}, Section {meta.get('section_number', '?')} ({meta.get('section_title', 'Unknown')})"
            context += f"[{i}] {citation}\n"
            context += '-' * 80 + '\n'
            context += chunk['text']
            context += '\n\n'

        system_prompt = get_system_prompt()
        user_prompt = get_user_prompt(question, context)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                temperature=0.3,
                system=system_prompt,
                messages=[
                    {'role': 'user', 'content': user_prompt}
                ]
            )

            answer = response.content[0].text

        except Exception as e:
            return {
                'question': question,
                'answer': f'Error: {str(e)}',
                'citations': [],
                'model': self.model,
            }

        citations = [
            {
                'rule': chunk['metadata']['rule_number'],
                'citation': f"Rule {chunk['metadata']['rule_number']}"
            }
            for chunk in chunks
        ]

        return {
            'question': question,
            'answer': answer,
            'citations': citations,
            'model': self.model,
        }


class ClaudeEvaluator:
    """Evaluate with Claude on 100 questions."""

    def __init__(self):
        """Initialize."""
        self.rag = ClaudeRAGSystem()
        self.results = []

        # Load test questions
        with open('data/100_test_questions.json', 'r') as f:
            self.questions = json.load(f)

    def run_evaluation(self):
        """Run evaluation."""
        print()
        print("=" * 80)
        print("PHASE 1: CLAUDE EVALUATION (Expected: 46-48%)")
        print("=" * 80)
        print()

        print(f"Testing {len(self.questions)} questions with Claude...")
        print()

        correct = 0
        rule_accuracy = {}

        for i, q in enumerate(self.questions, 1):
            question = q['question']
            expected_rule = q['rule']

            result = self.rag.answer_question(question, top_k=5)
            answer = result['answer']

            # Check if answer mentions the expected rule
            found = expected_rule in [c['rule'] for c in result['citations']]

            if found or f"Rule {expected_rule}" in answer:
                correct += 1

            # Track by rule
            if expected_rule not in rule_accuracy:
                rule_accuracy[expected_rule] = {'correct': 0, 'total': 0}
            rule_accuracy[expected_rule]['total'] += 1
            if found or f"Rule {expected_rule}" in answer:
                rule_accuracy[expected_rule]['correct'] += 1

            if i % 25 == 0:
                accuracy = (correct / i) * 100
                print(f"  [{i:3d}/100] Accuracy: {accuracy:.1f}%")

        accuracy = (correct / len(self.questions)) * 100

        print()
        print("=" * 80)
        print("RESULTS")
        print("=" * 80)
        print()

        print(f"Overall Accuracy: {correct}/100 ({accuracy:.1f}%)")
        print()

        print("Performance on Problem Rules:")
        print()
        for rule in [6, 9, 13]:
            if rule in rule_accuracy:
                stats = rule_accuracy[rule]
                acc = (stats['correct'] / stats['total']) * 100 if stats['total'] > 0 else 0
                rule_name = {6: "Fouls", 9: "Free Throws", 13: "Instant Replay"}.get(rule)
                print(f"  Rule {rule} ({rule_name}): {stats['correct']}/{stats['total']} ({acc:.1f}%)")

        print()
        print("=" * 80)
        print("IMPROVEMENT")
        print("=" * 80)
        print()

        baseline = 36.0
        improvement = accuracy - baseline

        print(f"Previous (GPT-3.5-turbo):  36.0%")
        print(f"Current (Claude):          {accuracy:.1f}%")
        print(f"Improvement:               +{improvement:.1f}% (Target: +10%)")
        print()

        if accuracy >= 46:
            print("✅ Phase 1 SUCCESS! Ready for Phase 2.")
        else:
            print(f"⚠️  Phase 1 showed +{improvement:.1f}% (expected +10%)")

        print()

        return accuracy


def main():
    """Run Phase 1."""
    evaluator = ClaudeEvaluator()
    accuracy = evaluator.run_evaluation()

    # Save results
    with open('data/phase1_claude_results.json', 'w') as f:
        json.dump({
            'phase': 1,
            'model': 'claude-opus-4-8',
            'accuracy': accuracy,
            'timestamp': datetime.now().isoformat(),
        }, f, indent=2)


if __name__ == "__main__":
    main()
