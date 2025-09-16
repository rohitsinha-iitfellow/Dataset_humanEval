import streamlit as st
import json
import os
import csv
import time

st.set_page_config(page_title="Perception Quiz", layout="wide")

# Root directory
root_dir = r"D:\Perception_dataset\Dataset_humanEval"

# Variable to control how many images per folder
max_per_folder = 2

# Collect all folders and questions
all_folders = set()
questions = []
for folder in os.listdir(root_dir):
    folder_path = os.path.join(root_dir, folder)
    if os.path.isdir(folder_path):
        all_folders.add(folder)
        json_path = os.path.join(folder_path, "annotations.json")
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                data = json.load(f)
            count = 0
            for img_name, info in data.items():
                if count >= max_per_folder:
                    break
                img_path = os.path.join(folder_path, img_name)
                if os.path.exists(img_path):
                    question_text = info.get("question", "")
                    if isinstance(question_text, list):
                        question_text = question_text[0]
                    answer = info.get("answer", "")
                    questions.append({
                        "folder": folder,
                        "img_path": img_path,
                        "question": question_text,
                        "answer": answer
                    })
                    count += 1

# Streamlit app
if "setup_done" not in st.session_state:
    st.session_state.setup_done = False

if not st.session_state.setup_done:
    st.title("Perception Quiz Setup")
    name = st.text_input("Enter your name:")
    gender = st.selectbox("Select your gender:", ["Male", "Female", "Other"])
    age = st.number_input("Enter your age:", min_value=1, max_value=120, value=25)
    st.subheader("Test Instructions:")
    instructions = [
        "Read each question carefully.",
        "Observe the image provided.",
        "Select the best answer from the options A, B, C, D.",
        "You cannot go back to previous questions.",
        "Your accuracy will be calculated per task at the end."
    ]
    for i, instr in enumerate(instructions, 1):
        st.write(f"{i}. {instr}")
    if st.button("Start Test") and name:
        st.session_state.name = name
        st.session_state.age = age
        st.session_state.gender = gender
        st.session_state.setup_done = True
        st.session_state.current_question = 0
        st.session_state.answers = []
        st.session_state.scores = []
        st.rerun()
else:
    if "current_question" not in st.session_state:
        st.session_state.current_question = 0
    if "answers" not in st.session_state:
        st.session_state.answers = []
    if "scores" not in st.session_state:
        st.session_state.scores = []

    if st.session_state.current_question < len(questions):
        q = questions[st.session_state.current_question]
        st.image(q["img_path"], caption=q["folder"], width=600)
        st.write(q["question"])
        options = ["A", "B", "C", "D"]
        choice = st.radio("Select your answer:", options, key=f"q_{st.session_state.current_question}")
        if st.button("Submit Answer"):
            st.session_state.answers.append(choice)
            score = 1 if choice == q["answer"] else 0
            st.session_state.scores.append(score)
            st.session_state.current_question += 1
            st.rerun()
    else:
        # Quiz finished
        st.write("Quiz completed!")
        # Calculate folder-wise accuracy
        folder_scores = {}
        folder_counts = {}
        for i, q in enumerate(questions):
            folder = q["folder"]
            if folder not in folder_scores:
                folder_scores[folder] = 0
                folder_counts[folder] = 0
            folder_scores[folder] += st.session_state.scores[i]
            folder_counts[folder] += 1
        for folder in folder_scores:
            accuracy = (folder_scores[folder] / folder_counts[folder]) * 100
            st.write(f"{folder}: {accuracy:.2f}%")
            print(f"{folder}: {accuracy:.2f}%")  # Print to terminal
        # Save results
        lock_file = "results.lock"
        while os.path.exists(lock_file):
            time.sleep(0.1)
        with open(lock_file, 'w') as lf:
            lf.write("locked")
        try:
            if not os.path.exists("results.csv"):
                header = ["name", "age", "gender"] + sorted(all_folders)
                with open("results.csv", "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(header)
            row = [st.session_state.name, st.session_state.age, st.session_state.gender]
            for folder in sorted(all_folders):
                if folder in folder_scores:
                    accuracy = (folder_scores[folder] / folder_counts[folder]) * 100
                else:
                    accuracy = 0
                row.append(accuracy)
            with open("results.csv", "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(row)
        finally:
            os.remove(lock_file)
        st.write("Results recorded")
        # Reset
        if st.button("Restart Quiz"):
            st.session_state.setup_done = False
            st.session_state.current_question = 0
            st.session_state.answers = []
            st.session_state.scores = []
            st.rerun()
