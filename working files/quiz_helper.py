# Filename: quiz_helper.py

import os
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from urllib.parse import urlparse, parse_qs
import textwrap

from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq

# Load .env
load_dotenv()

# Initialize Groq LLM
llm = ChatGroq(
    model_name="llama3-8b-8192",  # Or llama3-70b-8192
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

def extract_transcript(youtube_url):
    video_id = get_video_id(youtube_url)
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([entry['text'] for entry in transcript])
    except (TranscriptsDisabled, NoTranscriptFound, Exception) as e:
        print("❌ Transcript fetch failed:", e)
        return None

# Helper to chunk long text
def split_text(text, max_chars=3000):
    return textwrap.wrap(text, width=max_chars)

def summarize_video(youtube_url):
    transcript = extract_transcript(youtube_url)
    if not transcript:
        return None, "Transcript could not be fetched for this video."

    summary_prompt = PromptTemplate(
        input_variables=["text"],
        template="Summarize the following part of a YouTube transcript in concise bullet points:\n\n{text}"
    )

    chain = summary_prompt | llm
    chunks = split_text(transcript, max_chars=3000)
    summaries = []

    for chunk in chunks:
        result = chain.invoke({"text": chunk})
        summaries.append(result.content.strip())

    full_summary = "\n\n".join(summaries)
    return transcript, full_summary

def generate_quiz(transcript):
    quiz_prompt = PromptTemplate(
        input_variables=["text"],
        template="""Based on this transcript, generate 3 multiple-choice questions with 4 options each.
List options A–D and specify the correct answer clearly.\n\nTranscript:\n{text}"""
    )

    chain = quiz_prompt | llm
    result = chain.invoke({"text": transcript[:3000]})  # Trim input to avoid token overload
    return parse_quiz_output(result.content)

def parse_quiz_output(raw_text):
    questions = []
    for qblock in raw_text.strip().split("\n\n"):
        if not qblock.strip():
            continue
        lines = qblock.strip().split("\n")
        q_text = lines[0].strip()
        opts = [line.strip() for line in lines[1:5]]
        answer_line = [line for line in lines if line.lower().startswith("answer")]
        answer = answer_line[0].split(":")[-1].strip() if answer_line else "Not specified"
        questions.append({
            "question": q_text,
            "options": opts,
            "answer": answer
        })
    return questions
