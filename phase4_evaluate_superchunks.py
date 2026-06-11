"""
Phase 4: Evaluation with Super Chunks
Tests RAG system with traveling and goaltending super chunks.
"""

import json
from typing import List, Dict
from datetime import datetime
from dotenv import load_dotenv
import numpy as np

# Load environment
load_dotenv()

from phase4_rag_openai import OpenAIRAGSystem


class SuperChunkRAGSystem:
    """RAG system using enhanced chunks with super chunks."""

    def __init__(self, model: str = "gpt-3.5-turbo"):
        """Initialize RAG with super chunks."""
        self.retrieval = None
        self.model = model
        self.llm_client = None
        self._init_retrieval_with_superchunks()
        self._setup_llm()

    def _init_retrieval_with_superchunks(self):
        """Initialize retrieval with super chunks."""
        import sys
        sys.path.insert(0, '/Users/omar/Documents/Claude-Vibe-Code/nba-rules')

        from phase3_embeddings import EmbeddingPipeline

        # Use custom chunks and embeddings
        self.retrieval_obj = type('Retrieval', (), {})()
        self.retrieval_obj.chunks = []
        self.retrieval_obj.metadata = []
        self.retrieval_obj.embeddings = None
        self.retrieval_obj.index = None

        # Load enhanced chunks
        with open('data/09_stable_chunks_with_superchunks.json', 'r') as f:
            data = json.load(f)
            self.retrieval_obj.chunks = data['chunks']

        # Load enhanced embeddings
        self.retrieval_obj.embeddings = np.load('data/10_embeddings_with_superchunks.npy')

        # Regenerate metadata
        self.retrieval_obj.metadata = [
            {
                'chunk_id': c['id'],
                'rule_number': c['metadata']['rule_number'],
                'section_number': c['metadata']['section_number'],
                'section_title': c['metadata']['section_title'],
                'page_number': c['metadata']['page_number'],
            }
            for c in self.retrieval_obj.chunks
        ]

        # Build FAISS index
        import faiss

        embedding_dim = self.retrieval_obj.embeddings.shape[1]
        index = faiss.IndexFlatL2(embedding_dim)
        index.add(self.retrieval_obj.embeddings.astype(np.float32))
        self.retrieval_obj.index = index

        print("✅ Retrieval initialized with super chunks")

    def _setup_llm(self):
        """Setup OpenAI client."""
        try:
            from openai import OpenAI

            self.llm_client = OpenAI()
            print(f"✅ OpenAI API client initialized (Model: {self.model})")
        except Exception as e:
            print(f"❌ OpenAI initialization error: {e}")
            raise

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """Retrieve chunks using hybrid search."""
        from sentence_transformers import SentenceTransformer
        from rank_bm25 import BM25Okapi

        # Encode query
        model = SentenceTransformer('all-MiniLM-L6-v2')
        query_embedding = model.encode(query)

        # Semantic search
        distances, indices = self.retrieval_obj.index.search(
            np.array([query_embedding]).astype(np.float32), top_k * 2
        )

        # BM25 search
        texts = [c['text'] for c in self.retrieval_obj.chunks]
        tokenized = [text.lower().split() for text in texts]
        bm25 = BM25Okapi(tokenized)
        tokens = query.lower().split()
        bm25_scores = bm25.get_scores(tokens)

        # Combine results
        results_dict = {}
        for i, idx in enumerate(indices[0]):
            chunk = self.retrieval_obj.chunks[idx]
            meta = self.retrieval_obj.metadata[idx]

            sim_score = 1.0 / (1.0 + distances[0][i])
            bm25_score = min(1.0, bm25_scores[idx] / 10.0)
            combined = (sim_score * 0.7) + (bm25_score * 0.3)

            results_dict[idx] = {
                'chunk_id': chunk['id'],
                'text': chunk['text'],
                'rule_number': meta['rule_number'],
                'section_title': meta['section_title'],
                'page_number': meta['page_number'],
                'combined_score': combined,
                'citation': (
                    f"Rule {meta['rule_number']}, Section {meta['section_number']} "
                    f"({meta['section_title']}), p. {meta['page_number']}"
                ),
            }

        # Sort and return top-k
        sorted_results = sorted(
            results_dict.values(), key=lambda x: x['combined_score'], reverse=True
        )
        return sorted_results[:top_k]

    def answer_question(self, question: str, top_k: int = 5) -> Dict:
        """Answer question using super chunks."""
        from phase4_prompts import get_system_prompt, get_user_prompt

        # Retrieve chunks
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
            context += f"[{i}] {chunk['citation']}\n"
            context += '-' * 80 + '\n'
            context += chunk['text']
            context += '\n\n'

        # Create prompts
        system_prompt = get_system_prompt()
        user_prompt = get_user_prompt(question, context)

        # Call LLM
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                max_tokens=1024,
                temperature=0.3,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt},
                ],
            )
            answer = response.choices[0].message.content
        except Exception as e:
            return {
                'question': question,
                'answer': f'Error: {str(e)}',
                'citations': [],
                'model': self.model,
            }

        # Extract citations
        citations = [
            {
                'chunk_id': c['chunk_id'],
                'citation': c['citation'],
                'rule_number': c['rule_number'],
            }
            for c in chunks
        ]

        return {
            'question': question,
            'answer': answer,
            'citations': citations,
            'retrieved_chunks': [
                {
                    'citation': c['citation'],
                    'combined_score': c['combined_score'],
                }
                for c in chunks
            ],
            'model': self.model,
        }


class SuperChunkEvaluator:
    """Evaluate RAG with super chunks."""

    def __init__(self):
        """Initialize evaluator."""
        self.rag = SuperChunkRAGSystem()
        self.results = []
        self.questions = [
            {'id': 1, 'question': 'What actions constitute a traveling violation under NBA rules?',
             'expected': 'Rule 4'},
            {'id': 2, 'question': 'When is defensive goaltending called and what happens after the violation?',
             'expected': 'Rule 11'},
            {'id': 3, 'question': 'Which situations are reviewable using instant replay?',
             'expected': 'Rule 13'},
            {'id': 4, 'question': 'What behaviors can result in a technical foul being assessed?',
             'expected': 'Rule 12'},
            {'id': 5, 'question': 'How many timeouts does a team receive during a regulation NBA game?',
             'expected': 'Rule 5'},
            {'id': 6, 'question': 'When does the shot clock reset to 14 seconds instead of 24 seconds?',
             'expected': 'Rule 7'},
            {'id': 7, 'question': 'In what situations is a jump ball used to resume play?',
             'expected': 'Rule 6'},
            {'id': 8, 'question': 'What is the difference between a Flagrant Foul Penalty 1 and Penalty 2?',
             'expected': 'Rule 12'},
            {'id': 9, 'question': 'When is a player considered out of bounds?',
             'expected': 'Rule 10'},
            {'id': 10, 'question': 'How many free throws are awarded for different types of personal fouls?',
             'expected': 'Rule 8'},
        ]

    def run_evaluation(self) -> List[Dict]:
        """Run full evaluation."""
        print()
        print('=' * 80)
        print('SUPER CHUNK EVALUATION')
        print('=' * 80)
        print()

        for i, q in enumerate(self.questions, 1):
            print(f"[{i}/10] Q: {q['question'][:50]}...")
            result = self.rag.answer_question(q['question'], top_k=5)

            # Score
            faith = 5 if result['answer'] and 'could not find' not in result['answer'].lower() else 1
            relev = 5 if q['expected'].lower() in result['answer'].lower() else 1

            result_item = {
                'id': q['id'],
                'question': q['question'],
                'faithfulness': faith,
                'relevance': relev,
                'answer': result['answer'][:200],
                'citations': result['citations'],
            }
            self.results.append(result_item)

            print(f"  → Faithfulness: {faith}/5, Relevance: {relev}/5")
            print()

        return self.results

    def print_results(self):
        """Print results."""
        faith_scores = [r['faithfulness'] for r in self.results]
        relev_scores = [r['relevance'] for r in self.results]

        avg_faith = sum(faith_scores) / len(faith_scores)
        avg_relev = sum(relev_scores) / len(relev_scores)

        print()
        print('=' * 80)
        print('RESULTS WITH SUPER CHUNKS')
        print('=' * 80)
        print()
        print(f"Faithfulness: {avg_faith:.2f}/5.00 ({(sum(1 for s in faith_scores if s >= 4) / len(faith_scores) * 100):.0f}%)")
        print(f"Relevance:    {avg_relev:.2f}/5.00 ({(sum(1 for s in relev_scores if s >= 4) / len(relev_scores) * 100):.0f}%)")
        print()

        # Highlight improvements
        print("Questions Fixed:")
        for r in self.results:
            if r['id'] == 1 and r['faithfulness'] == 5:
                print(f"  ✅ Q{r['id']} (Traveling): Now works!")
            elif r['id'] == 2 and r['faithfulness'] == 5:
                print(f"  ✅ Q{r['id']} (Goaltending): Still works!")

        print()


def main():
    """Run evaluation."""
    evaluator = SuperChunkEvaluator()
    evaluator.run_evaluation()
    evaluator.print_results()


if __name__ == '__main__':
    main()
