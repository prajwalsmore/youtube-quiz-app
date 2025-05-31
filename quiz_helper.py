# Filename: quiz_helper.py

import os
import textwrap
import json
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq

# Load .env variables
load_dotenv()
llm = ChatGroq(
    model_name="llama3-8b-8192",
    temperature=0.7,
    api_key=os.getenv("GROQ_API_KEY")
)

def get_video_id(url):
    query = urlparse(url)
    if query.hostname == 'youtu.be':
        return query.path[1:]
    if query.hostname in ('www.youtube.com', 'youtube.com'):
        return parse_qs(query.query).get('v', [None])[0]
    return None

def extract_transcript(youtube_url, max_duration_sec=600):
    video_id = get_video_id(youtube_url)
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        filtered = [entry['text'] for entry in transcript if entry['start'] <= max_duration_sec]
        return " ".join(filtered)
    except (TranscriptsDisabled, NoTranscriptFound, Exception) as e:
        print("❌ Transcript fetch failed:", e)
        return None

def split_text(text, max_chars=3000):
    return textwrap.wrap(text, width=max_chars)

def summarize_video(youtube_url):
    transcript = extract_transcript(youtube_url)
    if not transcript:
        return None, "Transcript could not be fetched."

    summary_prompt = PromptTemplate(
        input_variables=["text"],
        template="Summarize the following YouTube transcript in bullet points:\n\n{text}"
    )

    chain = summary_prompt | llm
    chunks = split_text(transcript, max_chars=3000)
    summaries = [chain.invoke({"text": chunk}).content.strip() for chunk in chunks]
    return transcript, "\n".join(summaries)

def generate_quiz(transcript):
    quiz_prompt = PromptTemplate(
        input_variables=["text"],
        template="""
You are a quiz generator.

Based on the transcript below, generate exactly 5 multiple-choice questions and return them strictly as a JSON array. Use this structure:

[
  {{
    "question": "What is Python?",
    "options": ["A) A snake", "B) A programming language", "C) A car", "D) A drink"],
    "answer": "B) A programming language"
  }},
  ...
]

Only return the JSON array. Do not include any explanation or introductory text.

Transcript:
{text}
"""
    )

    chain = quiz_prompt | llm
    result = chain.invoke({"text": transcript[:3000]})
    raw = result.content.strip()

    try:
        return json.loads(raw)
    except Exception as e:
        print("❌ Failed to parse JSON from LLM output:\n", raw)
        return []


