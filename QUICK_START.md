# Quick Start Guide - Code Assistant POC

## 🚀 Get Started in 3 Steps

### 1. Setup Environment

```bash
# Create .env file with your OpenAI API key
echo "OPENAI_API_KEY=your_key_here" > .env

# Install dependencies
pip3.9 install -r requirements.txt
```

---

### 2. Index Your Codebase

**Choose ANY codebase path you want to index:**

```bash
# Basic usage - index any directory
python3.9 scripts/index_codebase.py /path/to/your/codebase

# Example: Index the sample React app
python3.9 scripts/index_codebase.py ./my_codebase/mycarhub/src

# Example: Index your own project
python3.9 scripts/index_codebase.py ~/projects/my-awesome-app/src
```

**Advanced options:**

```bash
# Custom collection name
python3.9 scripts/index_codebase.py ./my_project \
  --collection my_project_index

# Custom chunk size
python3.9 scripts/index_codebase.py ./my_project \
  --chunk-size 1500 \
  --chunk-overlap 150

# Full customization
python3.9 scripts/index_codebase.py /path/to/code \
  --output ./custom_vector_db \
  --collection my_collection \
  --chunk-size 2000 \
  --chunk-overlap 200
```

**Get help:**

```bash
python3.9 scripts/index_codebase.py --help
```

---

### 3. Start the Server

```bash
# Start the FastAPI server
python3.9 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 💡 Usage Examples

### Ask Questions via API

```bash
# Health check
curl http://localhost:8000/

# List indexed documents
curl http://localhost:8000/debug/docs

# Ask a question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What components are in this React app?"}'
```

---

## 🔧 Configuration Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `codebase_path` | - | *required* | Path to your codebase |
| `--output` | `-o` | `./chroma_db` | Vector store output directory |
| `--collection` | `-c` | `code_assistant_index` | Collection name |
| `--chunk-size` | - | `1000` | Characters per chunk |
| `--chunk-overlap` | - | `100` | Overlap between chunks |

---

## 📝 Supported File Types

The indexer automatically detects and processes:

- **JavaScript/TypeScript**: `.js`, `.jsx`, `.ts`, `.tsx`
- **Python**: `.py`
- **Swift**: `.swift`, `.m`, `.h`
- **Kotlin/Java**: `.kt`, `.java`, `.gradle`
- **Web**: `.html`, `.css`
- **Config**: `.json`, `.yaml`, `.toml`, `.xml`, `.md`

---

## ⚡ Key Features

✅ **Dynamic Path Selection** - No need to edit code, just pass your path  
✅ **Flexible Configuration** - Customize via command-line arguments  
✅ **Multiple Projects** - Index different codebases with different collections  
✅ **Error Handling** - Clear error messages for invalid paths  
✅ **Language Aware** - Respects code structure when chunking  

---

## 🐛 Troubleshooting

**Problem: "Directory does not exist"**
```bash
# Make sure the path is valid
ls /path/to/your/codebase
```

**Problem: "No code files found"**
- Check if your codebase contains supported file types
- Try with a different directory

**Problem: "OPENAI_API_KEY not set"**
```bash
# Create .env file
echo "OPENAI_API_KEY=sk-..." > .env
```

**Problem: "RAG system not initialized"**
```bash
# Re-run indexing with default collection
python3.9 scripts/index_codebase.py ./my_codebase/mycarhub/src
```

---

## 📚 More Information

See [README.md](README.md) for detailed documentation.

---

## 💡 Pro Tips

1. **Multiple Projects**: Use different collection names for different codebases
   ```bash
   python3.9 scripts/index_codebase.py ~/frontend --collection frontend_code
   python3.9 scripts/index_codebase.py ~/backend --collection backend_code
   ```

2. **Large Codebases**: Increase chunk size for better context
   ```bash
   python3.9 scripts/index_codebase.py ./large_project --chunk-size 2000
   ```

3. **Test First**: Use the test script to verify setup
   ```bash
   python3.9 test_startup.py
   ```

4. **Re-indexing**: Simply run the command again to update the index
   ```bash
   python3.9 scripts/index_codebase.py ./my_project
   ```

---

Happy coding! 🎉

