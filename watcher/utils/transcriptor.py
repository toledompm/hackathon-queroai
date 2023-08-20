import moviepy.editor as mp
import openai
import os
import re
from pydub import AudioSegment
import pandas as pd


def __format_transcript__(segments: list[dict[str, str | float]], offset: int):
    return [
        {
            "start": segment["start"] + offset,
            "end": segment["end"] + offset,
            "text": segment["text"],
        }
        for segment in segments
    ]


def convert_mp4_to_mp3(video_path: str) -> str:
    """
    convert_mp4_to_mp3 creates a mp3 file from a mp4 clip and returns the path to the mp3 file
    """
    save_path = video_path[: video_path.rfind("/")]

    audio_clip_path = f"{save_path}/{os.urandom(16).hex()}.mp3"
    clip = mp.VideoFileClip(video_path).subclip()
    clip.audio.write_audiofile(audio_clip_path)
    return audio_clip_path


def transcription_mp3_to_text(mp3_path: str) -> list[dict[str, str | float]]:
    """
    transcription_mp3_to_text transcribes a mp3 file to text using OpenAI's API
    """
    save_path = mp3_path[: mp3_path.rfind("/")]

    batch_in_milliseconds = 1000 * 60 * 10  # 1000 miliseconds * 60 seconds * 10 minutes
    start = 0
    end = batch_in_milliseconds
    total_transcript = []

    song = AudioSegment.from_mp3(mp3_path)
    while start < len(song):
        random_mp3_file_name = f"{save_path}/{os.urandom(16).hex()}.mp3"
        song[start:end].export(random_mp3_file_name, format="mp3")
        arq = open(random_mp3_file_name, "rb")
        transcript = openai.Audio.transcribe(
            file=arq, model="whisper-1", response_format="verbose_json", language="pt"
        )
        total_transcript += __format_transcript__(transcript["segments"], start / 1000)
        start += batch_in_milliseconds
        end += batch_in_milliseconds
    return total_transcript


def parser_text(file_path: str) -> list[dict[str, str | float]]:
    """
    parser text to input format
    """
    save_path = file_path[: file_path.rfind("/")]
    parsead_text = []

    arq = open(file_path, "rb")
    text = arq.read().decode("utf-8")
    paragraph_regex = re.compile(r".+\n")
    parsead_text = [
        {
            "text": [batch.group()],
            "start": [batch.start()],
            "end": [batch.end()],
        }
        for batch in paragraph_regex.finditer(text)
    ]

    indexes_small_batches = [idx for idx, batch in enumerate(parsead_text) if len(batch['text'][0]) < 50]
    ok_batches = [idx for idx, batch in enumerate(parsead_text) if len(batch['text'][0]) >= 50]

    for idx in indexes_small_batches:
        idx_concat = idx+1 if idx+1 < len(parsead_text) else idx-1
        parsead_text[idx_concat]['text'][0] += parsead_text[idx]['text'][0]

    indexes_filtered = np.array(parsead_text)[list(set(ok_batches) - set(indexes_small_batches))]
    dfs = [pd.DataFrame(data=dic) for dic in indexes_filtered]
    return dfs