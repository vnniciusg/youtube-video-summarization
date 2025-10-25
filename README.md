# YouTube Video Summarization

A Python application that fetches YouTube video transcripts, generates AI-powered summaries optimized for audio narration, and converts them to speech using ElevenLabs.

## Features

- 📝 Extract transcripts from YouTube videos
- 🤖 Generate concise, audio-optimized summaries using OpenAI GPT-4
- 🔊 Convert summaries to natural-sounding audio with ElevenLabs
- 🔗 Chainable processing pipeline for flexible workflows
- 🔍 Search YouTube videos by keywords
- ⚡ Batch process multiple videos with progress tracking
- ✅ Robust error handling with detailed logging
- 🎯 Customizable processing with skip-on-error option

## Prerequisites

- Python 3.13+
- OpenAI API key
- ElevenLabs API key

## Installation

1. Clone the repository:

```bash
git clone https://github.com/vnniciusg/youtube-video-summarization.git
cd youtube-video-summarization
```

2. Install dependencies using `uv`:

```bash
uv sync
```

3. Set up environment variables:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```
OPENAI_API_KEY=your_openai_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

## Usage

### Search and Batch Process Videos

```python
from main import (
    youtube_search,
    YoutubeVideoSumarization, 
    GenerateSummarization, 
    GenerateAudio,
    ChainExecutor
)

# Search for videos
search_response = youtube_search(search_terms="Building Effective Agents", max_results=5)

if search_response["status"] == "success":
    urls = search_response["urls"]
    
    # Create a processing chain
    chain = YoutubeVideoSumarization() | GenerateSummarization() | GenerateAudio()
    
    # Process multiple videos with error handling
    executor = ChainExecutor(chain)
    results = executor.run(
        input=urls,
        skip_on_error=True,  # Continue on errors
        model_name="gpt-4o-mini",
        temperature=0.0,
    )
    
    print(f"Processed: {results['successful']} ✓ | Failed: {results['failed']} ✗")
    for result in results:
        print(result)
```

### Basic Example (Single Video)

```python
from main import YoutubeVideoSumarization, GenerateSummarization, GenerateAudio

# Create a processing chain
chain = YoutubeVideoSumarization() | GenerateSummarization() | GenerateAudio()

# Process a YouTube video
result = chain.invoke("https://www.youtube.com/watch?v=VIDEO_ID")
print(result)  # Outputs: "uuid.mp3: A new audio file was saved successfully!"
```

### Individual Components

#### 1. Search YouTube Videos

```python
from main import youtube_search

result = youtube_search(search_terms="Python tutorials", max_results=10)

if result["status"] == "success":
    urls = result["urls"]
    print(f"Found {len(urls)} videos")
else:
    print(f"Error: {result['error']}")
```

#### 2. Extract Transcript Only

```python
from main import YoutubeVideoSumarization

transcript_extractor = YoutubeVideoSumarization()
transcript = transcript_extractor.invoke("https://www.youtube.com/watch?v=VIDEO_ID")
print(transcript)
```

#### 3. Generate Summary Only

```python
from main import GenerateSummarization

summarizer = GenerateSummarization()
summary = summarizer.invoke(
    "Your transcript text here",
    model_name="gpt-4o-mini",  # Optional
    temperature=0.0  # Optional
)
print(summary)
```

#### 4. Generate Audio Only

```python
from main import GenerateAudio

audio_generator = GenerateAudio()
result = audio_generator.invoke(
    "Text to convert to speech",
    save_file_path="output.mp3",  # Optional
    voice_id="ZF6FPAbjXT4488VcRRnw"  # Optional
)
print(result)
```

#### 5. Batch Process with ChainExecutor

```python
from main import ChainExecutor, YoutubeVideoSumarization, GenerateSummarization

chain = YoutubeVideoSumarization() | GenerateSummarization()

urls = [
    "https://www.youtube.com/watch?v=VIDEO_ID_1",
    "https://www.youtube.com/watch?v=VIDEO_ID_2",
    "https://www.youtube.com/watch?v=VIDEO_ID_3",
]

executor = ChainExecutor(chain)
results = executor.run(
    input=urls,
    skip_on_error=True,  # Skip failed items and continue
)

print(f"Results: {results}")
```

## Configuration

### ChainExecutor Options

Customize batch processing behavior in [`ChainExecutor`](main.py):

- `skip_on_error`: Continue processing on errors (default: `True`)
- `**kwargs`: Additional arguments passed to chain components

### Summarization Options

Customize the summary generation in [`GenerateSummarization`](main.py):

- `model_name`: OpenAI model (default: `"gpt-4o-mini"`)
- `temperature`: Creativity level 0.0-1.0 (default: `0.0`)

### Audio Generation Options

Customize audio output in [`GenerateAudio`](main.py):

- `save_file_path`: Output file path (default: auto-generated UUID)
- `model_id`: ElevenLabs model (default: `"eleven_multilingual_v2"`)
- `voice_id`: Voice selection (default: `"ZF6FPAbjXT4488VcRRnw"`)
- `output_format`: Audio format (default: `"mp3_44100_128"`)
- `voice_settings`: Fine-tune voice characteristics

## Project Structure

```
youtube-video-summarization/
├── main.py                 # Main application code
├── pyproject.toml          # Project dependencies
├── .env                    # Environment variables (not in git)
├── .env.example            # Environment template
├── .pre-commit-config.yaml # Code quality hooks
├── README.md               # This file
└── LICENSE                 # MIT License
```

## Development

### Code Quality

This project uses pre-commit hooks with Ruff for code formatting and linting:

```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Architecture

The application uses a chain pattern where each component implements [`BaseChain`](main.py) and can be combined using the `|` operator:

1. **[`YoutubeVideoSumarization`](main.py)**: Fetches video transcripts
2. **[`GenerateSummarization`](main.py)**: Creates audio-optimized summaries
3. **[`GenerateAudio`](main.py)**: Converts text to speech

Each component uses the Singleton pattern to reuse API clients efficiently.

## Supported YouTube URL Formats

- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/embed/VIDEO_ID`
- Direct video ID
- URL suffixes from youtube_search (e.g., `/watch?v=VIDEO_ID&pp=...`)

## Error Handling

The application uses custom exception classes for better error tracking:

### ChainException
Raised when a chain component fails during execution. Includes:
- Chain name that failed
- Error message
- Original exception traceback

### FunctionException
Raised when utility functions like `youtube_search()` fail.

### Example Error Handling

```python
from main import ChainException, FunctionException, ChainExecutor, youtube_search

try:
    results = youtube_search("search terms")
    if results["status"] == "success":
        chain = YoutubeVideoSumarization() | GenerateSummarization() | GenerateAudio()
        executor = ChainExecutor(chain)
        output = executor.run(results["urls"])
except FunctionException as e:
    print(f"Search failed: {e}")
except ChainException as e:
    print(f"Chain execution failed: {e}")
```

## Limitations

- Only works with videos that have available transcripts
- Requires active internet connection
- API costs apply for OpenAI and ElevenLabs usage
- YouTube URL extraction supports common formats (full URLs and suffixes)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
