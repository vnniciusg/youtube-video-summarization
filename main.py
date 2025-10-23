from __future__ import annotations

import os
from abc import ABC, ABCMeta, abstractmethod
from typing import Optional
from uuid import uuid4

from dotenv import load_dotenv
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from openai import OpenAI
from youtube_transcript_api import YouTubeTranscriptApi

load_dotenv()


class SingletonMetaclass(ABCMeta):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)

        return cls._instances[cls]


class BaseChain(ABC):
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


class YoutubeVideoSumarization(BaseChain, metaclass=SingletonMetaclass):
    __slots__ = "_ytt_api"

    def __init__(self) -> None:
        self._ytt_api = YouTubeTranscriptApi()

    @staticmethod
    def extract_video_id_from_url(url: str) -> str:
        if "youtu.be/" in url:
            return url.split("youtu.be/")[1].split("?")[0]
        if "youtube.com/watch?v=" in url:
            return url.split("v=")[1].split("&")[0]

        if "youtube.com/embed/" in url:
            return url.split("embed/")[1].split("?")[0]

        return url

    def invoke(self, input: str, **kwargs) -> str:
        video_id = YoutubeVideoSumarization.extract_video_id_from_url(url=input)
        transcription = self._ytt_api.fetch(video_id=video_id)
        return " ".join([snippet.text for snippet in transcription.snippets])


class GenerateSummarization(BaseChain, metaclass=SingletonMetaclass):
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


class GenerateAudio(BaseChain, metaclass=SingletonMetaclass):
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


if __name__ == "__main__":
    chain = YoutubeVideoSumarization() | GenerateSummarization() | GenerateAudio()

    result = chain.invoke(
        "https://www.youtube.com/watch?v=uhJJgc-0iTQ&t=41s&pp=ugUEEgJlbtIHCQkHCgGHKiGM7w%3D%3D",
    )
    print(result)
