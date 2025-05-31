# Filename: main.py

import streamlit as st
from quiz_helper import summarize_video, generate_quiz

st.set_page_config(page_title="YouTube Summarizer + Quiz", page_icon="📺")
st.title("📺 YouTube Video Summarizer + Quiz Generator")

youtube_url = st.text_input("Enter YouTube Video URL:")

if youtube_url:
    with st.spinner("Extracting and summarizing video..."):
        transcript, summary = summarize_video(youtube_url)
    
    if not transcript:
        st.error("❌ Could not extract transcript. Please try another video.")
    else:
        st.subheader("📄 Summary")
        st.markdown(summary)

        with st.spinner("Generating quiz questions..."):
            questions = generate_quiz(transcript)

        st.subheader("📝 Quiz")
        for i, q in enumerate(questions, 1):
            st.markdown(f"**Q{i}. {q['question']}**")
            for opt in q['options']:
                st.markdown(f"- {opt}")
            if st.checkbox(f"Show Answer for Q{i}"):
                st.success(f"✅ Correct Answer: {q['answer']}")
