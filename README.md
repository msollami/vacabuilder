# Vacation Builder

An AI-powered desktop application that creates personalized vacation itineraries using a local LLM. No external API calls required for the AI features - everything runs on your machine!

## Features

- **Local AI Processing**: Uses llama.cpp with Python bindings for completely private, offline LLM processing
- **Multi-Source Data**: Fetches information from Google Places API, Wikipedia, and web scraping
- **Beautiful PDF Export**: Generates professionally styled PDF itineraries
- **Real-time Preview**: See your itinerary in markdown format before exporting
- **Desktop App**: Electron-based application with a modern, intuitive interface

## Architecture

- **Frontend**: Electron with vanilla JavaScript
- **Backend**: Python FastAPI server
- **LLM**: llama.cpp with Python bindings (supports GGUF models)
- **Data Sources**: Google Places API, Wikipedia API, web scraping
- **PDF Generation**: WeasyPrint with custom styling

## Prerequisites

- **Node.js** (v16 or higher)
- **Python** 3.8 or higher
- **Git**
- A GGUF model file (see Model Setup below)

## Installation

### 1. Clone the Repository

```bash
cd /Users/67840/Downloads/VacationBuilder
```

### 2. Install Node.js Dependencies

```bash
npm install
```

### 3. Set Up Python Environment

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate  # On Windows

# Install Python dependencies
pip install -r requirements.txt
```

**Note**: Installing `llama-cpp-python` may take several minutes as it compiles from source.

### 4. Download LLM Model

Download a GGUF model file and place it in `backend/models/`. Recommended models:

- **Mistral 7B Instruct** (4GB) - Excellent balance of quality and speed
- **Llama 2 7B Chat** (4GB) - Good alternative

Download from [Hugging Face - TheBloke](https://huggingface.co/TheBloke):

```bash
# Example: Download Mistral 7B Instruct (Q4_K_M quantization)
cd backend/models
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf
```

**Recommended quantization**: Q4_K_M (good balance of quality and file size)

### 5. Configure Environment (Optional)

Copy the example environment file:

```bash
cd backend
cp .env.example .env
```

Edit `.env` and add your API keys (all optional):

```env
# Optional: Google Places API Key for better attraction data
GOOGLE_PLACES_API_KEY=your_api_key_here

# Model path (if different from default)
LLM_MODEL_PATH=models/mistral-7b-instruct-v0.2.Q4_K_M.gguf
```

## Usage

### Running the Application

From the project root directory:

```bash
npm run dev
```

This will:
1. Start the Python backend server on `http://127.0.0.1:8000`
2. Launch the Electron desktop application

### Using the App

1. **Enter Your Preferences**: Describe your ideal vacation (e.g., "I love outdoor activities, local cuisine, and historical sites")

2. **Add Destinations**: Click "Add Destination" and enter:
   - Destination name (e.g., "Paris, France")
   - Optional start and end dates

3. **Generate Itinerary**: Click "Generate Itinerary" and wait (may take 30-60 seconds)

4. **Preview & Export**: Review the markdown preview and click "Export PDF" to save

## Project Structure

```
VacationBuilder/
├── src/                          # Electron frontend
│   ├── main.js                   # Electron main process
│   ├── preload.js                # IPC bridge
│   └── renderer/                 # UI files
│       ├── index.html
│       ├── app.js
│       └── styles.css
├── backend/                      # Python backend
│   ├── main.py                   # FastAPI server
│   ├── requirements.txt
│   ├── llm/
│   │   └── model.py              # llama.cpp wrapper
│   ├── fetchers/
│   │   ├── google_places.py      # Google Places API
│   │   ├── wikipedia.py          # Wikipedia API
│   │   └── web_scraper.py        # Web scraping
│   ├── services/
│   │   └── itinerary_planner.py  # Core logic
│   ├── pdf/
│   │   └── generator.py          # PDF generation
│   └── models/                   # GGUF model files (not in git)
├── package.json
└── README.md
```

## Troubleshooting

### Backend Won't Start

- Ensure Python virtual environment is activated
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Verify the model file exists in `backend/models/`

### LLM Loading Issues

- **Model not found**: Check the path in `.env` or `backend/llm/model.py`
- **Out of memory**: Try a smaller model or quantization (Q3_K_M instead of Q4_K_M)
- **Slow generation**: This is normal for CPU inference. Consider:
  - Using a smaller model
  - Reducing `max_tokens` in `model.py`
  - If you have an NVIDIA GPU, set `n_gpu_layers=-1` in `model.py`

### PDF Generation Fails

- Install system dependencies for WeasyPrint:
  - **macOS**: `brew install cairo pango gdk-pixbuf libffi`
  - **Ubuntu/Debian**: `sudo apt-get install build-essential python3-dev python3-pip python3-setuptools python3-wheel python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info`

### Google Places Not Working

- Add a valid API key to `.env`
- Enable Places API in Google Cloud Console
- The app will still work without it, using Wikipedia and web scraping

## Development

### Running Backend Separately

```bash
cd backend
source venv/bin/activate
python main.py
```

### Running Frontend Separately

```bash
npm start
```

### Building for Distribution

```bash
npm run build
```

This will create distributable packages in the `dist/` folder.

## Customization

### Changing the LLM Model

Edit `backend/llm/model.py` to adjust:
- `n_ctx`: Context window size (default: 4096)
- `n_threads`: CPU threads to use
- `n_gpu_layers`: GPU acceleration (set to -1 for full GPU)
- `temperature`: Generation randomness (0.7 = balanced)

### Customizing PDF Style

Edit `backend/pdf/generator.py` in the `_get_pdf_styles()` method to modify:
- Fonts and colors
- Layout and spacing
- Header/footer content

### Adding Data Sources

Create new fetcher classes in `backend/fetchers/` and integrate them in `backend/services/itinerary_planner.py`.

## API Endpoints

The backend exposes these endpoints:

- `GET /health` - Health check and LLM status
- `POST /api/plan` - Generate itinerary
- `POST /api/generate-pdf` - Export to PDF

## Performance Notes

- **First generation**: May take 1-2 minutes as the model loads into memory
- **Subsequent generations**: 30-60 seconds depending on your CPU
- **GPU acceleration**: Can reduce generation time to 10-20 seconds

## License

MIT

## Credits

- **llama.cpp**: Fast LLM inference
- **Mistral AI / Meta**: Model providers
- **FastAPI**: Python web framework
- **Electron**: Desktop app framework
