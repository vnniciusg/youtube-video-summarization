# YouTube Video Summarization

A Python application that fetches YouTube video transcripts, generates AI-powered summaries optimized for audio narration, and converts them to speech using ElevenLabs.

## Features

- 📝 Extract transcripts from YouTube videos
- 🤖 Generate concise, audio-optimized summaries using OpenAI GPT-4
- 🔊 Convert summaries to natural-sounding audio with ElevenLabs
- 🔗 Chainable processing pipeline for flexible workflows

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

### Basic Example

```python
from main import YoutubeVideoSumarization, GenerateSummarization, GenerateAudio

# Create a processing chain
chain = YoutubeVideoSumarization() | GenerateSummarization() | GenerateAudio()

# Process a YouTube video
result = chain.invoke("https://www.youtube.com/watch?v=VIDEO_ID")
print(result)  # Outputs: "uuid.mp3: A new audio file was saved successfully!"
```

### Individual Components

#### 1. Extract Transcript Only

```python
from main import YoutubeVideoSumarization

transcript_extractor = YoutubeVideoSumarization()
transcript = transcript_extractor.invoke("https://www.youtube.com/watch?v=VIDEO_ID")
print(transcript)
```

#### 2. Generate Summary Only

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

#### 3. Generate Audio Only

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

## Configuration

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

## Limitations

- Only works with videos that have available transcripts
- Requires active internet connection
- API costs apply for OpenAI and ElevenLabs usage

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
