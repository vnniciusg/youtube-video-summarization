from __future__ import annotations

import os
import re
from abc import ABC, ABCMeta, abstractmethod
from datetime import datetime
from typing import Any, Literal, Optional, Union
from uuid import uuid4

from dotenv import load_dotenv
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from openai import OpenAI
from pydantic import BaseModel, Field
from tqdm import tqdm
from youtube_search import YoutubeSearch
from youtube_transcript_api import YouTubeTranscriptApi

load_dotenv()


class SingletonMetaclass(ABCMeta):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)

        return cls._instances[cls]


class BaseChain(ABC, metaclass=SingletonMetaclass):
    @abstractmethod
    def invoke(self, input: str, **kwargs) -> str:
        pass

    def __or__(self, other: BaseChain) -> BaseChain:
        outer_self = self

        class ChainedComponent(BaseChain):
            def invoke(self_inner, input: str, **kwargs) -> str:
                intermediate = outer_self.invoke(input, **kwargs)
                return other.invoke(intermediate, **kwargs)

        return ChainedComponent()


class BaseException(Exception):
    def __init__(self, *, name: str, message: str) -> None:
        super().__init__(f"[{name}]: {message}")


class ChainException(BaseException):
    pass


class ChainExecutor(BaseException):
    pass


class FunctionException(BaseException):
    pass


def youtube_search(search_terms: str, max_results: int = 5) -> dict[str, Any]:
    """
    Allows you to search for YouTUbe videos based on a given topic or keywords. It returns a list
    of video URLs that match your search criteria.

    Args:
        - search_terms (str): The keywords or topic you want to search for on YouTube.
        - max_results (int, optional, default=5): The maximum number of video results to return

    Returns:
        - dict[str, Any]:
            - if successful:
                - "status": "success"
                - "urls": List of YouTube video URL suffixes (e.g, /watch?v=abc123)
            - if an error occurs:
                - "status": "error"
                - "error": Error message describing the issue
    """
    try:
        yt_search = YoutubeSearch(search_terms=search_terms, max_results=max_results)

        return {
            "status": "success",
            "urls": [video["url_suffix"] for video in yt_search.videos],
        }

    except Exception as e:
        raise FunctionException(
            name="youtube_search", message=f"Failed to search for videos: {str(e)}"
        ) from e


class YoutubeVideoSumarization(BaseChain):
    __slots__ = "_ytt_api"

    def __init__(self) -> None:
        self._ytt_api = YouTubeTranscriptApi()

    @staticmethod
    def extract_video_id_from_url(url: str) -> str:
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
            r'v=([a-zA-Z0-9_-]{11})',
            r'^([a-zA-Z0-9_-]{11})$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        if len(url) == 11 and re.match(r'^[a-zA-Z0-9_-]{11}$', url):
            return url
        
        raise ValueError(f"Could not extract video ID from URL: {url}")

    def invoke(self, input: str, **kwargs) -> str:
        try:
            video_id = YoutubeVideoSumarization.extract_video_id_from_url(url=input)
            transcription = self._ytt_api.fetch(video_id=video_id)
            return " ".join([snippet.text for snippet in transcription.snippets])

        except Exception as e:
            raise ChainException(
                name="YoutubeVideoSumarization",
                message=f"Failed to extract transcript: {str(e)}",
            ) from e


class GenerateSummarization(BaseChain):
    __slots__ = "_client"

    def __init__(self) -> None:
        self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def invoke(
        self,
        input: str,
        *,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.0,
        **kwargs,
    ) -> str:
        try:
            response = self._client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"""
                                    You are an expert content summarizer creating summaries optimized for audio narration. 

                                    Analyze the following transcript and create a comprehensive summary following these guidelines:

                                    **Format Requirements:**
                                    - Write in a natural, conversational tone suitable for audio playback
                                    - Use short, clear sentences that flow smoothly when spoken aloud
                                    - Avoid complex punctuation or formatting that doesn't translate to audio
                                    - Use transition phrases to connect ideas naturally (e.g., "Additionally", "Moving on to", "In conclusion")

                                    **Content Structure:**
                                    1. **Opening**: Start with a brief introduction of the main topic (1-2 sentences)
                                    2. **Key Points**: Present 3-5 most important points in a logical flow
                                    - Each point should be clearly articulated
                                    - Use simple language anyone can understand
                                    3. **Supporting Details**: Include relevant examples or context for each key point
                                    4. **Closing**: End with a brief conclusion or takeaway (1-2 sentences)

                                    **Style Guidelines:**
                                    - Length: 200-350 words (approximately 1.5-2.5 minutes when spoken)
                                    - Use active voice and present tense where appropriate
                                    - Avoid acronyms without explanation
                                    - Replace symbols with words (e.g., "&" becomes "and", "%" becomes "percent")
                                    - Maintain objectivity and factual accuracy

                                    Transcript to summarize:

                                    {input}

                                    Provide the summary ready for text-to-speech conversion.""",
                            }
                        ],
                    }
                ],
                temperature=temperature,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            raise ChainException(
                name="GenerateSummarization",
                message=f"Failed to generate summary: {str(e)}",
            ) from e


class GenerateAudio(BaseChain):
    __slots__ = "_client"

    def __init__(self) -> None:
        self._client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

    def invoke(
        self,
        input: str,
        *,
        save_file_path: Optional[str] = None,
        model_id: str = "eleven_multilingual_v2",
        voice_id: str = "ZF6FPAbjXT4488VcRRnw",
        output_format: str = "mp3_44100_128",
        voice_settings: VoiceSettings = VoiceSettings(
            stability=0.0,
            similarity_boost=1.0,
            style=0.0,
            use_speaker_boost=True,
            speed=1.0,
        ),
        **kwargs,
    ) -> str:
        try:
            response = self._client.text_to_speech.convert(
                text=input,
                voice_id=voice_id,
                model_id=model_id,
                output_format=output_format,
                voice_settings=voice_settings,
            )

            if not save_file_path:
                save_file_path = f"{uuid4()}.mp3"

            with open(save_file_path, "wb") as file:
                for chunk in response:
                    if chunk:
                        file.write(chunk)

            return f"{save_file_path}: A new audio file was saved successfully!"

        except Exception as e:
            raise ChainException(
                name="GenerateAudio", message=f"Failed to generate audio: {str(e)}"
            ) from e


class ChainExecutor:
    def __init__(self, chain: BaseChain):
        self.chain = chain

    def run(
        self, input: Union[str, list[str]], *, skip_on_error: bool = True, **kwargs
    ) -> list[str]:
        if isinstance(input, str):
            input = [input]

        results, errors = [], []

        try:
            for item in tqdm(input, desc="Processing URLs"):
                try:
                    result = self.chain.invoke(item, **kwargs)
                    results.append({"status": "success", "data": result, "input": item})

                except Exception as e:
                    error_info = {"status": "error", "input": item, "error": str(e)}
                    errors.append(error_info)

                    if not skip_on_error:
                        raise

                    tqdm.write(f"Skipped: {item} - {str(e)}")

            return results

        except Exception as e:
            raise ChainException(
                name="ChainExecutor", message=f"Chain execution failed: {str(e)}"
            ) from e


if __name__ == "__main__":
    chain = YoutubeVideoSumarization() | GenerateSummarization() | GenerateAudio()
    results = youtube_search(search_terms="Bulding Effective Agents")

    list_processor = ChainExecutor(chain)
    results = list_processor.run(input=results["urls"])

    print(results)
