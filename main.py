import os

from dotenv import load_dotenv
from openai import OpenAI
from youtube_transcript_api import YouTubeTranscriptApi

load_dotenv()

# _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class SingletonMetaclass(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
            
        return cls._instances[cls]

class YoutubeVideoSumarization(metaclass=SingletonMetaclass):

    __slots__ = ("_ytt_api","__weakref__")

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
    
    def invoke(self, url: str) -> str:
        video_id = YoutubeVideoSumarization.extract_video_id_from_url(url=url)
        transcription = self._ytt_api.fetch(video_id=video_id)
        return " ".join([snippet.text for snippet in transcription.snippets])


if __name__ == "__main__":

    ytv_summarization = YoutubeVideoSumarization()
    print(ytv_summarization.invoke(url="https://www.youtube.com/watch?v=uhJJgc-0iTQ&t=41s&pp=ugUEEgJlbtIHCQkHCgGHKiGM7w%3D%3D"))
