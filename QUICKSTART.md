# Quick Start Guide

Get Vacation Builder running in 5 minutes!

## Step 1: Run Setup Script

```bash
./setup.sh
```

This will automatically:
- Check for Node.js and Python
- Install all dependencies
- Set up the Python virtual environment
- Create configuration files

## Step 2: Download LLM Model

You need a GGUF model file. Here's the easiest way:

### Recommended Model: Mistral 7B Instruct (4GB)

```bash
cd backend/models

# Download using wget
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf

# OR download using curl
curl -L -O https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf

cd ../..
```

**Alternative**: Visit [HuggingFace](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF) and manually download the Q4_K_M model file.

### Other Model Options

- **Smaller/Faster** (3GB): `mistral-7b-instruct-v0.2.Q3_K_M.gguf`
- **Larger/Better** (6GB): `mistral-7b-instruct-v0.2.Q5_K_M.gguf`

## Step 3: Configure (Optional)

Add a Google Places API key for better attraction data:

```bash
# Edit backend/.env
GOOGLE_PLACES_API_KEY=your_key_here
```

Skip this if you don't have an API key - the app will still work using Wikipedia.

## Step 4: Run the App

```bash
npm run dev
```

The app will:
1. Start the Python backend (wait for "LLM: Ready ✓" in the status bar)
2. Open the Electron desktop app

## Usage

1. **Enter preferences**: "I love beaches, local food, and historical sites"
2. **Add destinations**: "Bali, Indonesia"
3. **Set dates** (optional): Pick start/end dates
4. **Generate**: Click "Generate Itinerary" and wait ~30-60 seconds
5. **Export**: Click "Export PDF" to save

## Troubleshooting

### "Backend: Offline"
- Check the console/terminal for Python errors
- Ensure virtual environment is activated
- Verify model file is in `backend/models/`

### "LLM: Loading..." stays forever
- Model file might be in the wrong location
- Check `backend/.env` for correct model path
- Try a smaller model if running out of memory

### PDF generation fails
Install system dependencies:
```bash
# macOS
brew install cairo pango gdk-pixbuf libffi

# Ubuntu/Debian
sudo apt-get install libcairo2 libpango-1.0-0 libpangocairo-1.0-0
```

## Need Help?

- Check the full [README.md](README.md) for detailed documentation
- Review backend logs in the terminal
- Ensure you have at least 8GB RAM for the 7B models

## Tips

- First generation takes longer (model loading)
- Subsequent generations are faster
- Use Q3_K_M models on systems with <8GB RAM
- GPU acceleration: Edit `backend/llm/model.py` and set `n_gpu_layers=-1`
