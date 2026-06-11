# Running RAG Locally (No API Key Required)

Complete guide to running your NBA Rules RAG system with local LLMs.

---

## Quick Start (5 minutes)

### Option 1: Ollama (Easiest) ⭐

```bash
# 1. Download from https://ollama.ai (macOS, Linux, Windows)

# 2. Open terminal and run:
ollama serve

# 3. In another terminal, pull a model:
ollama pull mistral

# 4. Test it works:
curl http://localhost:11434/api/generate -d '{"model":"mistral","prompt":"test"}'

# 5. Run RAG evaluation:
python3 phase4_evaluate_local.py
```

That's it! ✅

### Option 2: LM Studio (GUI)

```bash
# 1. Download from https://lmstudio.ai

# 2. Open LM Studio and:
   - Load a model (Mistral recommended)
   - Click "Start Server"

# 3. Run RAG:
python3 phase4_evaluate_local.py
```

### Option 3: GPT4All (Simple)

```bash
# 1. Download from https://gpt4all.io

# 2. Load a model and enable "API Server"

# 3. Run RAG:
python3 phase4_evaluate_local.py
```

---

## Detailed Setup

### Ollama (Recommended for This Project)

**Why Ollama?**
- ✅ Simplest to use
- ✅ Works on Mac, Linux, Windows
- ✅ Fast inference
- ✅ Easy model switching
- ✅ Good model selection

**Installation:**

1. **Download**
   - macOS: https://ollama.ai/download/Ollama-darwin.zip
   - Linux: `curl -sSL https://ollama.ai/install.sh | sh`
   - Windows: https://ollama.ai/download/OllamaSetup.exe

2. **Start Server**
   ```bash
   ollama serve
   ```
   Keep this running in a terminal window

3. **Pull Models**
   ```bash
   # Mistral (7B, recommended for this project)
   ollama pull mistral

   # Or alternatives:
   ollama pull llama2        # 7B, good quality
   ollama pull neural-chat   # 7B, chat optimized
   ollama pull orca-mini     # 3B, fast but less capable
   ```

4. **Verify Setup**
   ```bash
   curl http://localhost:11434/api/generate \
     -d '{"model":"mistral","prompt":"What is 2+2?"}' 
   ```
   Should return JSON with response

---

## Using Local RAG

### Basic Usage

```python
from phase4_rag_local import LocalRAGSystem

# Initialize with local model
rag = LocalRAGSystem(
    model="mistral",
    base_url="http://localhost:11434"
)

# Setup
rag.setup()

# Answer question
result = rag.answer_question("What is traveling?")
rag.print_answer(result)
```

### Running Evaluation (10 Questions)

```bash
python3 phase4_evaluate_local.py
```

**Output:**
- Results table (faithfulness + relevance scores)
- Metrics summary
- Sample answers
- JSON export to `data/evaluation_local_results.json`

### Single Test

```bash
python3 -c "
from phase4_rag_local import LocalRAGSystem

rag = LocalRAGSystem('mistral', 'http://localhost:11434')
rag.setup()
result = rag.answer_question('How many timeouts per game?')
rag.print_answer(result)
"
```

---

## Model Recommendations

### For This Project (NBA Rules RAG)

| Model | Size | Speed | Quality | Recommended |
|-------|------|-------|---------|-------------|
| **Mistral** | 7B | Fast | Excellent | ⭐⭐⭐ |
| **Llama 2** | 7B | Fast | Good | ⭐⭐⭐ |
| **Neural Chat** | 7B | Fast | Good | ⭐⭐ |
| **Orca Mini** | 3B | Very Fast | Fair | ⭐ |
| **Dolphin Mixtral** | 8x7B | Slow | Excellent | ⭐⭐ (if you have GPU) |

**Recommendation:** Start with **Mistral 7B**
- Great balance of quality and speed
- Works well for rule-based tasks
- Runs on CPU (though slower than GPU)

---

## Performance Notes

### On CPU (MacBook, typical laptop)
- **Mistral 7B**: 5-15 tokens/second
- Full 10-question evaluation: ~10-20 minutes
- Acceptable for class projects

### On GPU (NVIDIA with CUDA)
- **Mistral 7B**: 50-200 tokens/second
- Full evaluation: ~1-2 minutes
- Much faster if available

### Memory Usage
- **Mistral 7B**: ~4-6 GB RAM
- Most modern laptops have enough
- Check with: `free -h` (Linux) or Activity Monitor (macOS)

---

## Troubleshooting

### "Could not connect to local LLM server"

**Problem:** The script can't reach `http://localhost:11434`

**Solutions:**
1. Check Ollama is running: `ps aux | grep ollama`
2. Start it: `ollama serve`
3. Verify connection: `curl http://localhost:11434/api/generate -d '{"model":"mistral","prompt":"test"}'`
4. Change base_url if using different port:
   ```python
   rag = LocalRAGSystem(
       model="mistral",
       base_url="http://localhost:8000"  # Different port
   )
   ```

### "Model not found"

**Problem:** Model not downloaded or wrong name

**Solutions:**
```bash
# List installed models
ollama list

# Pull missing model
ollama pull mistral

# Or pull different model
ollama pull llama2
```

### Very Slow Inference

**Problem:** Model running slowly

**Reasons:**
- CPU-only inference is inherently slow
- Laptop background processes using CPU
- Model too large for your RAM

**Solutions:**
1. Use smaller model: `ollama pull orca-mini`
2. Close other applications
3. Wait for response (can take 1-2 minutes per question)

### High Memory Usage

**Problem:** System getting very slow during inference

**Reasons:**
- Model too large for available RAM
- Multiple models loaded

**Solutions:**
1. Use smaller model
2. Restart Ollama: `pkill ollama && ollama serve`
3. Check available RAM: `free -h`

### Wrong Answers / Low Faithfulness

**Problem:** Local model not answering well

**Reasons:**
- Model not fine-tuned for rule-based tasks
- Temperature too high
- Poor context retrieval

**Solutions:**
1. Lower temperature:
   ```python
   rag.answer_question(question, temperature=0.1)
   ```
2. Increase top_k (more context):
   ```python
   rag.answer_question(question, top_k=10)
   ```
3. Try different model: `ollama pull llama2`

---

## Advanced Configuration

### Custom Model

```python
rag = LocalRAGSystem(
    model="your-custom-model-name",
    base_url="http://localhost:11434"
)
```

### Different LLM Server

If using LM Studio or GPT4All instead of Ollama:

```python
# LM Studio (default port 1234)
rag = LocalRAGSystem(
    model="any-model",
    base_url="http://localhost:1234"
)

# GPT4All (default port 4891)
rag = LocalRAGSystem(
    model="any-model",
    base_url="http://localhost:4891"
)
```

### Tuning Response Quality

```python
result = rag.answer_question(
    question="What is traveling?",
    top_k=10,           # More context (slower but better)
    temperature=0.2,    # Lower = more deterministic
    max_tokens=1024     # Longer answers
)
```

---

## Files Provided

| File | Purpose |
|------|---------|
| `phase4_rag_local.py` | Main RAG system with local LLM |
| `phase4_evaluate_local.py` | Evaluation framework (10 questions) |
| `LOCAL_LLM_SETUP.md` | This guide |

---

## Comparison: Local vs API

| Aspect | Local | API (Claude) |
|--------|-------|------------|
| Cost | FREE | Pay per API call |
| API Key | Not needed | Need Anthropic key |
| Privacy | Data stays local | Data sent to server |
| Speed | Depends on hardware | Fast (cloud GPU) |
| Quality | Good (7B models) | Excellent (Claude) |
| Setup | ~5 min | ~1 min |
| Offline | YES | NO |

**Local is great for:**
- Class projects (no costs!)
- Learning RAG architecture
- Development/testing
- Privacy-sensitive data
- Offline use

**API is better for:**
- Production systems
- Maximum accuracy needed
- Fast inference required
- Complex reasoning tasks

---

## Running Both

You can easily switch between local and API:

```python
# Use local for testing
from phase4_rag_local import LocalRAGSystem
rag = LocalRAGSystem("mistral")

# Use API for production
from phase4_rag_system import RAGSystem
rag = RAGSystem()
```

Both use the same retrieval pipeline, so results are comparable.

---

## Tips for Success

### 1. Start Simple
```bash
# Just run evaluation
python3 phase4_evaluate_local.py
```

### 2. Monitor Performance
- Watch terminal output for inference speed
- Note faithfulness/relevance scores
- Save results to JSON for analysis

### 3. Experiment with Models
```bash
# Try different models
ollama pull llama2
python3 phase4_evaluate_local.py

# Switch back
ollama pull mistral
python3 phase4_evaluate_local.py
```

### 4. Optimize for Your Hardware
- **Fast machine?** Use Mistral 7B
- **Limited RAM?** Use Orca Mini 3B
- **Has GPU?** Try larger models

### 5. Be Patient
- First run downloads model (~4GB for Mistral)
- Inference is slower on CPU than cloud
- But you save money! 💰

---

## Expected Results

### With Mistral 7B

**Typical Performance:**
- Faithfulness: 70-85%
- Relevance: 75-90%
- Speed: 10-20 min for 10 questions

**Quality:**
- Good understanding of rules
- Mostly accurate citations
- Some hallucinations (inherent to local models)

**Note:** Local models are ~10-20% less accurate than Claude, but much cheaper and fully local!

---

## Next Steps

1. **Install Ollama**: https://ollama.ai
2. **Start server**: `ollama serve`
3. **Pull model**: `ollama pull mistral`
4. **Run evaluation**: `python3 phase4_evaluate_local.py`
5. **Review results**: Check console output and `data/evaluation_local_results.json`

---

## Support

If you encounter issues:

1. **Check installation**
   ```bash
   ollama --version
   ollama list
   ```

2. **Verify connectivity**
   ```bash
   curl http://localhost:11434/api/generate -d '{"model":"mistral","prompt":"hi"}'
   ```

3. **Check logs**
   - Ollama logs are in terminal where you ran `ollama serve`
   - Check for error messages

4. **Try different model**
   ```bash
   ollama pull llama2
   # Edit phase4_evaluate_local.py to use "llama2" instead of "mistral"
   ```

---

## Summary

✅ **No API key needed**  
✅ **Free to run (no costs)**  
✅ **Works offline**  
✅ **Great for class projects**  
✅ **Easy to set up (5 minutes)**  

Ready to start? Download Ollama and run:

```bash
ollama serve              # Terminal 1
ollama pull mistral       # Terminal 2
python3 phase4_evaluate_local.py  # Terminal 3
```

Good luck! 🚀
