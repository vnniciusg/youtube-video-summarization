from __future__ import annotations

import os
from abc import ABC, ABCMeta, abstractmethod

from dotenv import load_dotenv
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
    def invoke(self, input_data: str, **kwargs) -> str:
        pass

    def __or__(self, other: BaseChain) -> BaseChain:
        outer_self = self

        class ChainedComponent(BaseChain):
            def invoke(self_inner, input_data: str, **kwargs) -> str:
                intermediate = outer_self.invoke(input_data, **kwargs)
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

    def invoke(self, url: str, **kwargs) -> str:
        video_id = YoutubeVideoSumarization.extract_video_id_from_url(url=url)
        transcription = self._ytt_api.fetch(video_id=video_id)
        return " ".join([snippet.text for snippet in transcription.snippets])


class GenerateSummarization(BaseChain, metaclass=SingletonMetaclass):
    __slots__ = "_client"

    def __init__(self) -> None:
        self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def invoke(
        self,
        message: str,
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
                            "text": f"Summarize the following text:\n\n{message}",
                        }
                    ],
                }
            ],
            temperature=temperature,
        )

        return response.choices[0].message.content.strip()


if __name__ == "__main__":
    chain = YoutubeVideoSumarization() | GenerateSummarization()

    result = chain.invoke(
        "https://www.youtube.com/watch?v=uhJJgc-0iTQ&t=41s&pp=ugUEEgJlbtIHCQkHCgGHKiGM7w%3D%3D",
    )
    print(result)
