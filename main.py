# Filename: main.py

import streamlit as st
from quiz_helper import summarize_video, generate_quiz
from quiz_cache import load_cache, save_cache, get_video_id_from_url

st.set_page_config(page_title="YouTube Summarizer + Quiz", page_icon="📺")
st.title("📺 YouTube Video Summarizer + Quiz Generator")

youtube_url = st.text_input("Enter YouTube Video URL:")

if youtube_url:
    video_id = get_video_id_from_url(youtube_url)
    cache = load_cache()

    if video_id in cache:
        st.info("📂 Loaded from history/cache.")
        summary = cache[video_id]["summary"]
        questions = cache[video_id]["quiz"]
    else:
        with st.spinner("Extracting and summarizing video..."):
            transcript, summary = summarize_video(youtube_url)

        if not transcript:
            st.error("❌ Could not extract transcript.")
            st.stop()

        with st.spinner("Generating quiz questions..."):
            questions = generate_quiz(transcript)

        if not questions:
            st.error("❌ Failed to generate quiz questions. Please try a different video.")
            st.stop()

        cache[video_id] = {
            "summary": summary,
            "quiz": questions
        }
        save_cache(cache)
        st.success("✅ Processed and cached.")

    # ✅ Freeze quiz for this video (no reshuffling)
    if "current_questions" not in st.session_state or st.session_state.get("current_video") != video_id:
        st.session_state.current_video = video_id
        st.session_state.current_questions = questions[:5]  # Always first 5 questions

    questions = st.session_state.current_questions

    st.subheader("📄 Summary")
    st.markdown(summary)

    st.subheader("📝 Take the Quiz")
    score = 0
    user_answers = []

    for idx, q in enumerate(questions, 1):
        st.markdown(f"**Q{idx}: {q['question']}**")
        selected = st.radio(
            "Choose an answer:",
            q["options"],
            key=f"q_{idx}",
            index=None,
            label_visibility="collapsed"
        )
        user_answers.append((selected, q["answer"]))

    if st.button("Submit Quiz"):
        if any(ans is None for ans, _ in user_answers):
            st.warning("⚠️ Please answer all questions before submitting.")
        else:
            for i, (user_ans, correct_ans) in enumerate(user_answers, 1):
                if user_ans and correct_ans and user_ans.strip().startswith(correct_ans[0]):
                    score += 1
                    st.success(f"✅ Q{i}: Correct")
                else:
                    st.error(f"❌ Q{i}: Incorrect. Correct answer: {correct_ans}")
            st.info(f"🎯 Final Score: {score} / {len(user_answers)}")
