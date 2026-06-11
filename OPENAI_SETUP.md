# Phase 4: Using OpenAI Instead of Claude

Quick setup guide for using OpenAI GPT-4 with your RAG system.

---

## Quick Start (3 minutes)

### 1. Get OpenAI API Key

1. Go to https://platform.openai.com/
2. Sign up or log in
3. Click **"API keys"** in the left sidebar
4. Click **"Create new secret key"**
5. Copy the key (starts with `sk-`)

### 2. Set API Key

```bash
export OPENAI_API_KEY="sk-..."

# Verify it works
echo $OPENAI_API_KEY
```

### 3. Install OpenAI Python Package

```bash
pip install openai
```

### 4. Run Evaluation

```bash
python3 phase4_evaluate_openai.py
```

That's it! ✅

---

## Model Options

### Recommended for This Project: GPT-4 Turbo

```python
rag = OpenAIRAGSystem(model="gpt-4-turbo")
```

**Why?**
- Excellent quality for rule-based tasks
- Faster than GPT-4
- Cheaper than GPT-4
- Great balance of cost/quality

### Other Options

| Model | Cost | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| **gpt-4-turbo** | $$$ | Fast | Excellent | ⭐ Recommended |
| **gpt-4** | $$$$ | Slower | Excellent+ | Best quality |
| **gpt-3.5-turbo** | $ | Very Fast | Good | Budget option |

### Price Comparison (approximate per 1000 tokens)

```
gpt-3.5-turbo:    $0.0005 input, $0.0015 output
gpt-4-turbo:      $0.01 input, $0.03 output
gpt-4:            $0.03 input, $0.06 output
```

For 10 questions with ~500 tokens each:
- gpt-3.5-turbo: ~$0.10
- gpt-4-turbo: ~$0.50
- gpt-4: ~$1.50

---

## Files to Use

| File | Purpose |
|------|---------|
| `phase4_rag_openai.py` | RAG system with OpenAI |
| `phase4_evaluate_openai.py` | Evaluation framework (10 questions) |
| `phase4_retrieval.py` | Retrieval (same for all) |
| `phase4_prompts.py` | Prompts (same for all) |

---

## Usage Examples

### Single Question

```python
from phase4_rag_openai import OpenAIRAGSystem

rag = OpenAIRAGSystem(model="gpt-4-turbo")
rag.setup()

result = rag.answer_question("What is traveling?")
rag.print_answer(result)
rag.save_result(result)
```

### Full Evaluation (10 Questions)

```bash
python3 phase4_evaluate_openai.py
```

### Use Different Model

```python
# Cheaper but good quality
rag = OpenAIRAGSystem(model="gpt-3.5-turbo")

# Best quality (most expensive)
rag = OpenAIRAGSystem(model="gpt-4")
```

---

## Expected Results

### With GPT-4 Turbo

**Quality:**
- Faithfulness: 90%+ ✓
- Relevance: 85%+ ✓
- Citations: Accurate ✓

**Speed:**
- Per question: ~10-30 seconds
- 10 questions: ~2-5 minutes total

**Cost:**
- 10 questions: ~$0.50

### Comparison to Local Models

| Aspect | GPT-4 Turbo | Mistral 7B |
|--------|-------------|-----------|
| Quality | 95%+ | 70% |
| Speed | 10-30 sec | 30-180 sec |
| Cost | $0.50/10Q | FREE |
| Hallucination | Rare | Common |
| Citations | Excellent | Good |

---

## Troubleshooting

### "Error: The model `gpt-4-turbo` does not exist"

**Problem:** Model name might have changed

**Solution:**
```bash
# Try alternative names:
gpt-4-1106-preview    # Older GPT-4 Turbo name
gpt-4-0125-preview    # Even older name
gpt-4                 # Latest GPT-4
gpt-3.5-turbo         # Always works
```

### "Error: OPENAI_API_KEY not found"

**Problem:** API key not set

**Solution:**
```bash
export OPENAI_API_KEY="sk-..."
python3 phase4_evaluate_openai.py
```

### "Error: Invalid authentication"

**Problem:** Bad API key

**Solution:**
1. Check key is correct (copy from https://platform.openai.com/api-keys)
2. Key should start with `sk-`
3. Make sure it's not in quotes in terminal:
   ```bash
   # CORRECT
   export OPENAI_API_KEY=sk-...
   
   # WRONG
   export OPENAI_API_KEY="sk-..."  # Don't include quotes
   ```

### "Rate limit exceeded"

**Problem:** Too many API calls too fast

**Solution:**
- Wait a minute
- Upgrade OpenAI plan (if needed)
- Use cheaper model (gpt-3.5-turbo)

### "Insufficient tokens in account"

**Problem:** You've used all your free credits

**Solution:**
- Add payment method to OpenAI account
- Or use local LLM (Ollama) instead

---

## Switching Between Providers

### Use OpenAI (Current)
```bash
python3 phase4_evaluate_openai.py
```

### Use Claude API
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python3 phase4_evaluate.py
```

### Use Local LLM
```bash
ollama serve  # Terminal 1
python3 phase4_evaluate_local.py  # Terminal 2
```

All use the same retrieval and chunk system!

---

## Cost Estimation

### 10 Questions Evaluation

```
Model            Input Tokens    Output Tokens    Cost
─────────────────────────────────────────────────────
gpt-3.5-turbo    ~2,000         ~1,500          $0.06
gpt-4-turbo      ~2,000         ~1,500          $0.50
gpt-4            ~2,000         ~1,500          $1.50
```

### Full Training

If you run evaluation multiple times:

```
100 evaluations (1000 questions):
gpt-3.5-turbo: ~$6
gpt-4-turbo:   ~$50
gpt-4:         ~$150
```

---

## Tips

### 1. Test with Cheap Model First
```python
rag = OpenAIRAGSystem(model="gpt-3.5-turbo")
rag.setup()
result = rag.answer_question("How many timeouts?")
rag.print_answer(result)
```

### 2. Switch to GPT-4 Turbo for Final Evaluation
```python
rag = OpenAIRAGSystem(model="gpt-4-turbo")
```

### 3. Monitor Your Usage
- https://platform.openai.com/account/usage/overview
- Check how much you're spending

### 4. Set Cost Limits
- https://platform.openai.com/account/billing/limits
- Prevent accidental high bills

---

## Environment Setup

### One-Time Setup

```bash
# 1. Add to ~/.zshrc or ~/.bashrc
echo 'export OPENAI_API_KEY="sk-..."' >> ~/.zshrc

# 2. Reload shell
source ~/.zshrc

# 3. Verify
echo $OPENAI_API_KEY
```

### Per-Session Setup

```bash
# Just set for this terminal session
export OPENAI_API_KEY="sk-..."
python3 phase4_evaluate_openai.py
```

---

## Next Steps

1. **Get API key** from https://platform.openai.com/
2. **Set environment variable**: `export OPENAI_API_KEY="sk-..."`
3. **Install package**: `pip install openai`
4. **Run evaluation**: `python3 phase4_evaluate_openai.py`
5. **Review results**: Check console output and `data/evaluation_openai_results.json`

---

## Support

If you get stuck:

1. **Check API key**: https://platform.openai.com/api-keys
2. **Check billing**: https://platform.openai.com/account/billing/overview
3. **Check usage**: https://platform.openai.com/account/usage
4. **OpenAI docs**: https://platform.openai.com/docs/

---

## Summary

✅ **Setup time**: 3 minutes  
✅ **Cost**: ~$0.50 for full eval  
✅ **Quality**: 90%+ expected  
✅ **Speed**: 2-5 minutes for 10 questions  

Ready to start? 

```bash
export OPENAI_API_KEY="sk-..."
python3 phase4_evaluate_openai.py
```
