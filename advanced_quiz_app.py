import streamlit as st
import json
import os
import csv
import time
import random
import pandas as pd
from collections import defaultdict

st.set_page_config(page_title="Advanced Perception Quiz", layout="wide")

# Root directory
root_dir = r"./"

# Configuration
IMAGES_PER_FOLDER = 1  # Number of images each user sees per folder
TRACKING_FILE = "user_image_tracking.json"  # File to track which images have been shown to which users
RESULTS_FILE = "detailed_results.csv"  # CSV file for storing detailed results
ANSWER_KEY = {
    "abstract":"answer",
    "dynamic_isomorph":"fifth_label",
    "hierarchial_isomorph": "answer",
    "mental_composition": "answer",
    "mental_rotation" : "answer",
    "paper_folding":"correct_option",
    "slippage":"violation",
    "symmetric_isomorph":"asymmetric_label"
}
class QuizManager:
    def __init__(self):
        self.all_folders = self._get_all_folders()
        self.all_images = self._load_all_images()
        self.tracking_data = self._load_tracking_data()
    
    def _get_all_folders(self):
        """Get all folders that contain annotations.json"""
        folders = []
        for folder in os.listdir(root_dir):
            folder_path = os.path.join(root_dir, folder)
            if os.path.isdir(folder_path):
                json_path = os.path.join(folder_path, "annotations.json")
                if os.path.exists(json_path):
                    folders.append(folder)
        return sorted(folders)
    
    def _load_all_images(self):
        """Load all images and their questions from all folders"""
        all_images = {}
        for folder in self.all_folders:
            folder_path = os.path.join(root_dir, folder)
            json_path = os.path.join(folder_path, "annotations.json")
            
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            folder_images = {}
            for img_name, info in data.items():
                img_path = os.path.join(folder_path, img_name)
                if os.path.exists(img_path):
                    question_text = info.get("question", "")
                    if isinstance(question_text, list):
                        question_text = question_text[0]
                    
                    folder_images[img_name] = {
                        "img_path": img_path,
                        "question": question_text,
                        "answer": info.get(ANSWER_KEY[folder], "")
                    }
            
            all_images[folder] = folder_images
        
        return all_images
    
    def _load_tracking_data(self):
        """Load tracking data for image distribution"""
        if os.path.exists(TRACKING_FILE):
            with open(TRACKING_FILE, 'r') as f:
                return json.load(f)
        else:
            # Initialize tracking data
            tracking = {}
            for folder in self.all_folders:
                tracking[folder] = {}
                for img_name in self.all_images[folder].keys():
                    tracking[folder][img_name] = {
                        "shown_count": 0,
                        "shown_to_users": []
                    }
            return tracking
    
    def _save_tracking_data(self):
        """Save tracking data to file"""
        with open(TRACKING_FILE, 'w') as f:
            json.dump(self.tracking_data, f, indent=2)
    
    def get_images_for_user(self, user_id):
        """Get images for a specific user ensuring fair distribution"""
        user_images = {}
        
        for folder in self.all_folders:
            # Get images that this user hasn't seen
            available_images = []
            for img_name, img_data in self.all_images[folder].items():
                if user_id not in self.tracking_data[folder][img_name]["shown_to_users"]:
                    available_images.append(img_name)
            
            # If we don't have enough unseen images, include some that have been shown least
            if len(available_images) < IMAGES_PER_FOLDER:
                # Sort by shown_count to get least shown images
                all_images_sorted = sorted(
                    self.all_images[folder].keys(),
                    key=lambda x: self.tracking_data[folder][x]["shown_count"]
                )
                
                # Add images until we have enough, prioritizing least shown
                for img_name in all_images_sorted:
                    if img_name not in available_images:
                        available_images.append(img_name)
                    if len(available_images) >= IMAGES_PER_FOLDER:
                        break
            
            # Randomly select IMAGES_PER_FOLDER from available
            if len(available_images) >= IMAGES_PER_FOLDER:
                selected_images = random.sample(available_images, IMAGES_PER_FOLDER)
            else:
                selected_images = available_images
            
            # Update tracking data
            for img_name in selected_images:
                if user_id not in self.tracking_data[folder][img_name]["shown_to_users"]:
                    self.tracking_data[folder][img_name]["shown_to_users"].append(user_id)
                    self.tracking_data[folder][img_name]["shown_count"] += 1
            
            user_images[folder] = selected_images
        
        self._save_tracking_data()
        return user_images
    
    def get_csv_columns(self):
        """Generate all CSV column names"""
        columns = ["name", "age", "gender"]
        
        for folder in self.all_folders:
            for img_name in sorted(self.all_images[folder].keys()):
                # Remove file extension for cleaner column names
                img_base = img_name.replace('.png', '').replace('.jpg', '').replace('.jpeg', '')
                columns.append(f"{folder}_{img_base}_response")
                columns.append(f"{folder}_{img_base}_time")
        
        return columns
    
    def save_user_results(self, user_data, selected_images, responses, times):
        """Save user results to CSV"""
        columns = self.get_csv_columns()
        
        # Initialize row with empty values
        row_data = {}
        for col in columns:
            row_data[col] = ""
        
        # Fill in user data
        row_data["name"] = user_data["name"]
        row_data["age"] = user_data["age"]
        row_data["gender"] = user_data["gender"]
        
        # Fill in responses and times for shown images
        response_index = 0
        for folder in self.all_folders:
            if folder in selected_images:
                for img_name in selected_images[folder]:
                    img_base = img_name.replace('.png', '').replace('.jpg', '').replace('.jpeg', '')
                    response_col = f"{folder}_{img_base}_response"
                    time_col = f"{folder}_{img_base}_time"
                    
                    if response_index < len(responses):
                        row_data[response_col] = responses[response_index]
                        row_data[time_col] = times[response_index]
                        response_index += 1
        
        # Create DataFrame and save
        df_row = pd.DataFrame([row_data])
        
        # Check if file exists and append or create
        if os.path.exists(RESULTS_FILE):
            df_row.to_csv(RESULTS_FILE, mode='a', header=False, index=False)
        else:
            df_row.to_csv(RESULTS_FILE, mode='w', header=True, index=False)

# Initialize quiz manager
if "quiz_manager" not in st.session_state:
    st.session_state.quiz_manager = QuizManager()

# Initialize session state
if "setup_done" not in st.session_state:
    st.session_state.setup_done = False

if not st.session_state.setup_done:
    st.title("Advanced Perception Quiz Setup")
    
    st.markdown("""
    ### Welcome to the Advanced Perception Quiz
    
    This quiz will test your visual perception abilities across different cognitive tasks.
    You will see 5 images from each category, and your responses and reaction times will be recorded.
    """)
    
    # User information
    col1, col2, col3 = st.columns(3)
    
    with col1:
        name = st.text_input("Enter your name:")
    
    with col2:
        gender = st.selectbox("Select your gender:", ["Male", "Female", "Other"])
    
    with col3:
        age = st.number_input("Enter your age:", min_value=1, max_value=120, value=25)
    
    st.subheader("Test Instructions:")
    instructions = [
        "Read each question carefully.",
        "Observe the image provided with full attention.",
        "Select the best answer from the options A, B, C, D (or similar options).",
        "You cannot go back to previous questions once submitted.",
        "Your response time for each question will be recorded.",
        "Each user will see 5 images per category, ensuring fair distribution across participants.",
        "Take your time to understand each question, but answer as accurately as possible."
    ]
    
    for i, instr in enumerate(instructions, 1):
        st.write(f"{i}. {instr}")
    
    st.info(f"You will answer questions from {len(st.session_state.quiz_manager.all_folders)} different categories: {', '.join(st.session_state.quiz_manager.all_folders)}")
    
    if st.button("Start Test", type="primary") and name:
        # Generate unique user ID
        user_id = f"{name}_{int(time.time())}"
        
        st.session_state.name = name
        st.session_state.age = age
        st.session_state.gender = gender
        st.session_state.user_id = user_id
        st.session_state.setup_done = True
        
        # Get images for this user
        st.session_state.selected_images = st.session_state.quiz_manager.get_images_for_user(user_id)
        
        # Create question list from selected images
        questions = []
        for folder in st.session_state.quiz_manager.all_folders:
            for img_name in st.session_state.selected_images[folder]:
                img_data = st.session_state.quiz_manager.all_images[folder][img_name]
                questions.append({
                    "folder": folder,
                    "img_name": img_name,
                    "img_path": img_data["img_path"],
                    "question": img_data["question"],
                    "answer": img_data["answer"] # ANSWER_KEY[folder]
                })
        
        # Shuffle questions to randomize order across folders
        random.shuffle(questions)
        st.session_state.questions = questions
        st.session_state.current_question = 0
        st.session_state.responses = []
        st.session_state.times = []
        st.session_state.question_start_time = time.time()
        
        st.rerun()

else:
    # Quiz interface
    if "current_question" not in st.session_state:
        st.session_state.current_question = 0
    if "responses" not in st.session_state:
        st.session_state.responses = []
    if "times" not in st.session_state:
        st.session_state.times = []
    if "question_start_time" not in st.session_state:
        st.session_state.question_start_time = time.time()

    if st.session_state.current_question < len(st.session_state.questions):
        q = st.session_state.questions[st.session_state.current_question]
        
        # Progress indicator
        progress = (st.session_state.current_question + 1) / len(st.session_state.questions)
        st.progress(progress)
        st.write(f"Question {st.session_state.current_question + 1} of {len(st.session_state.questions)}")
        st.write(f"**Category**: {q['folder']}")
        
        # Display image
        st.image(q["img_path"], caption=f"{q['folder']} - {q['img_name']}", width=1000)
        
        # Display question
        st.write("**Question:**")
        st.write(q["question"])
        
        # Determine answer options based on the answer format
        answer = q["answer"].strip()
        if q["folder"] in ["abstract","slippage"]:
            # Format like "A", "B", "C", "D"
            options = ["A", "B", "C", "D", "E", "F"]
        else:
            # Default fallback
            options = ["A", "B", "C", "D"]
        
        # Answer selection
        choice = st.radio("Select your answer:", options, key=f"q_{st.session_state.current_question}",index=None)
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("Submit Answer", type="primary",disabled=(choice is None)):
                # Calculate time taken
                time_taken = time.time() - st.session_state.question_start_time
                
                # Store response and time
                st.session_state.responses.append(choice)
                st.session_state.times.append(round(time_taken, 2))
                
                # Move to next question
                st.session_state.current_question += 1
                st.session_state.question_start_time = time.time()
                
                st.rerun()
        
        with col2:
            if st.session_state.current_question > 0:
                elapsed_time = time.time() - st.session_state.question_start_time
                st.write(f"Time elapsed: {elapsed_time:.1f} seconds")

    else:
        # Quiz completed
        st.title("🎉 Quiz Completed!")
        st.success("Thank you for participating in the Perception Quiz!")
        
        # Calculate and display results
        correct_count = 0
        folder_stats = defaultdict(lambda: {"correct": 0, "total": 0})
        
        for i, q in enumerate(st.session_state.questions):
            is_correct = st.session_state.responses[i] == q["answer"].strip("()").upper()
            if is_correct:
                correct_count += 1
            
            folder_stats[q["folder"]]["total"] += 1
            if is_correct:
                folder_stats[q["folder"]]["correct"] += 1
        
        # Overall performance
        overall_accuracy = (correct_count / len(st.session_state.questions)) * 100
        st.write(f"**Overall Accuracy**: {overall_accuracy:.1f}% ({correct_count}/{len(st.session_state.questions)})")
        
        # Folder-wise performance
        st.subheader("Performance by Category:")
        for folder in sorted(folder_stats.keys()):
            stats = folder_stats[folder]
            accuracy = (stats["correct"] / stats["total"]) * 100
            st.write(f"**{folder}**: {accuracy:.1f}% ({stats['correct']}/{stats['total']})")
        
        # Average response time
        avg_time = sum(st.session_state.times) / len(st.session_state.times)
        st.write(f"**Average Response Time**: {avg_time:.2f} seconds")
        
        # Save results
        try:
            user_data = {
                "name": st.session_state.name,
                "age": st.session_state.age,
                "gender": st.session_state.gender
            }
            
            st.session_state.quiz_manager.save_user_results(
                user_data, 
                st.session_state.selected_images,
                st.session_state.responses,
                st.session_state.times
            )
            
            st.success("✅ Your results have been saved successfully!")
            
        except Exception as e:
            st.error(f"❌ Error saving results: {str(e)}")
        
        # Reset option
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Take Quiz Again", type="primary"):
                # Clear all session state
                for key in list(st.session_state.keys()):
                    if key != "quiz_manager":  # Keep the quiz manager
                        del st.session_state[key]
                st.rerun()
        
        # with col2:
        #     st.download_button(
        #         label="Download Results CSV",
        #         data=open(RESULTS_FILE, "rb").read() if os.path.exists(RESULTS_FILE) else b"",
        #         file_name=RESULTS_FILE,
        #         mime="text/csv"
        #     )

# Sidebar with statistics (for admin/researcher view)
with st.sidebar:
    st.title("Quiz Statistics")
    
    if os.path.exists(TRACKING_FILE):
        tracking_data = st.session_state.quiz_manager.tracking_data
        
        # st.subheader("Image Distribution")
        # for folder in st.session_state.quiz_manager.all_folders:
        #     with st.expander(f"{folder} ({len(tracking_data[folder])} images)"):
        #         for img_name, data in tracking_data[folder].items():
        #             st.write(f"**{img_name}**: shown {data['shown_count']} times")
    
    if os.path.exists(RESULTS_FILE):
        try:
            df = pd.read_csv(RESULTS_FILE)
            st.subheader("Participation Summary")
            st.write(f"Total participants: {len(df)}")
            if len(df) > 0:
                st.write(f"Average age: {df['age'].mean():.1f}")
                gender_counts = df['gender'].value_counts()
                for gender, count in gender_counts.items():
                    st.write(f"{gender}: {count}")
        except:
            pass