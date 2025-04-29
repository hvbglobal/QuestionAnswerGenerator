import streamlit as st
import pandas as pd
import json
import os
import time
import random
import re
from datetime import datetime
import tempfile
import requests
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io
import base64

# Set up page configuration
st.set_page_config(
    page_title="ExamPrep AI - Past Paper Generator",
    page_icon="📝",
    layout="wide"
)

# Pre-defined API key - replace with your actual Groq API key
DEFAULT_GROQ_API_KEY = "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"  # Replace this with your actual Groq API key

# Initialize session state variables if they don't exist
if 'generated_questions' not in st.session_state:
    st.session_state.generated_questions = []
if 'selected_subject' not in st.session_state:
    st.session_state.selected_subject = None
if 'selected_topics' not in st.session_state:
    st.session_state.selected_topics = []
if 'use_custom_api_key' not in st.session_state:
    st.session_state.use_custom_api_key = False
if 'custom_api_key' not in st.session_state:
    st.session_state.custom_api_key = ""
if 'pdf_data' not in st.session_state:
    st.session_state.pdf_data = None
if 'pdf_filename' not in st.session_state:
    st.session_state.pdf_filename = None

# CSS styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #1E3A8A;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #F0F7FF;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #1E3A8A;
        margin-bottom: 1rem;
        color: #333333;
            
    }
    .question-box {
        background-color: #F9FAFB;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #E5E7EB;
        margin-bottom: 1rem;
        color: #333333;
        
    }
    .mark-scheme {
        background-color: #F0FDF4;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #047857;
        margin-top: 0.5rem;
        color: #333333;
    }
    .difficulty-easy, .difficulty-very-easy {
        color: #047857;
        font-weight: bold;
    }
    .difficulty-medium {
        color: #B45309;
        font-weight: bold;
    }
    .difficulty-hard, .difficulty-very-hard {
        color: #B91C1C;
        font-weight: bold;
    }
    .stProgress > div > div > div > div {
        background-color: #1E3A8A;
    }
    .api-key-warning {
        color: #B91C1C;
        font-weight: bold;
        font-size: 0.8rem;
    }
    .download-btn {
        background-color: #1E3A8A;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 0.3rem;
        text-decoration: none;
        font-weight: bold;
        margin-top: 1rem;
        display: inline-block;
    }
    .download-btn:hover {
        background-color: #1E40AF;
    }
</style>
""", unsafe_allow_html=True)

# Title and description
st.markdown('<h1 class="main-header">ExamPrep AI: Past Paper Question Generator</h1>', unsafe_allow_html=True)
st.markdown("""
<div class="info-box">
Generate custom exam-style questions based on real IGCSE and A-Level past papers. Practice with 
AI-generated questions that match the format, difficulty, and style of actual exam questions.
</div>
""", unsafe_allow_html=True)

SUBJECTS = {
    "IGCSE": [
        "Mathematics", "Physics", "Chemistry", "Biology", 
        "English Language", "English as a Second Language", "English Literature", "Computer Science",
        "Business Studies", "Economics", "Geography", "History"
    ],
    "A-Level": [
        "Mathematics", "Further Mathematics", "Physics", "Chemistry", "Biology",
        "English Literature", "Computer Science", "Economics",
        "Business", "Psychology", "Sociology", "Geography", "History"
    ]
}

TOPICS = {
    "IGCSE Mathematics": [
        "Number", "Algebra", "Geometry", "Statistics and Probability", 
        "Functions", "Vectors and Transformations", "Calculus"
    ],
    "IGCSE Physics": [
        "Mechanics", "Thermal Physics", "Waves", "Electricity and Magnetism", 
        "Modern Physics", "Energy", "Radioactivity"
    ],
    "IGCSE Chemistry": [
        "Atomic Structure", "Bonding", "Periodic Table", "Chemical Reactions", 
        "Acids and Bases", "Organic Chemistry", "Quantitative Chemistry"
    ],
    "IGCSE Biology": [
        "Cell Biology", "Human Biology", "Plant Biology", "Ecology", 
        "Genetics", "Evolution", "Microbiology"
    ],
    "IGCSE English Language": [
        "Reading Comprehension", "Writing Skills", "Summary Writing", 
        "Directed Writing", "Vocabulary Development", "Grammar and Punctuation", "Text Analysis"
    ],
    "IGCSE English as a Second Language": [
        "Reading Skills", "Writing Skills", "Grammar and Language Use", 
        "Vocabulary Development", "Listening Skills", "Speaking Skills", "Exam-Specific Skills"
    ],
    "IGCSE English Literature": [
        "Prose", "Poetry Analysis", "Drama Study", "Literary Devices", 
        "Context and Interpretation", "Comparative Analysis", "Essay Writing Skills"
    ],
    "IGCSE Computer Science": [
        "Programming Concepts", "Problem-solving and Design", "Data Representation", 
        "Computer Systems", "Networks and Communication", "Security and Ethics", "Databases"
    ],
    "IGCSE Business Studies": [
        "Business Activity", "People in Business", "Marketing", 
        "Operations Management", "Financial Information and Decisions", "External Influences", "Business Strategy"
    ],
    "IGCSE Economics": [
        "Basic Economic Problems", "The Allocation of Resources", "Microeconomic Decision Makers", 
        "Government and the Economy", "Economic Development", "International Trade and Globalization", 
        "Market Failure and Government Intervention"
    ],
    "IGCSE Geography": [
        "Physical Geography", "Human Geography", "Global Issues", 
        "Geographical Skills", "Plate Tectonics and Landforms", "Ecosystems and Biomes", "Urban Environments"
    ],
    "IGCSE History": [
        "International Relations", "The Cold War Era", "Key World Leaders and Regimes", 
        "Causes and Effects of Major Wars", "Decolonization and Independence Movements", 
        "Social and Economic Developments", "Source Analysis and Interpretation"
    ],
    "A-Level Mathematics": [
        "Pure Mathematics", "Calculus", "Mechanics", "Statistics", 
        "Probability", "Vectors", "Differential Equations"
    ],
    "A-Level Further Mathematics": [
        "Complex Numbers", "Matrices and Linear Algebra", "Further Calculus", 
        "Further Mechanics", "Further Statistics", "Decision Mathematics", "Differential Geometry"
    ],
    "A-Level Physics": [
        "Mechanics", "Materials", "Waves", "Electricity", "Magnetism", 
        "Nuclear Physics", "Particle Physics", "Quantum Physics", "Thermodynamics"
    ],
    "A-Level Chemistry": [
        "Physical Chemistry", "Inorganic Chemistry", "Organic Chemistry", 
        "Analytical Chemistry", "Thermodynamics", "Electrochemistry", "Kinetics"
    ],
    "A-Level Biology": [
        "Cell Biology", "Molecular Biology", "Genetics", "Ecology", 
        "Human Physiology", "Plant Biology", "Evolution", "Biochemistry"
    ],
    "A-Level English Literature": [
        "Poetry", "Drama", "Prose", "Literary Theory and Criticism", 
        "Contextual Study", "Comparative Analysis", "Independent Critical Study"
    ],
    "A-Level Computer Science": [
        "Programming and Problem-solving", "Data Structures and Algorithms", "Theory of Computation", 
        "Data Representation and Computer Architecture", "Communication and Networking", 
        "Databases and Software Development", "Ethical and Legal Issues in Computing"
    ],
    "A-Level Economics": [
        "Microeconomics", "Macroeconomics", "Global Economics", "Price Elasticity of Demand",
        "Economic Schools of Thought", "Quantitative Methods in Economics", 
        "Financial Markets and Monetary Policy", "Labor Markets and Income Distribution"
    ],
    "A-Level Business": [
        "Marketing and Customer Needs", "Financial Planning and Management", "Human Resource Management", 
        "Operations Management", "Business Strategy and Competitiveness", 
        "Global Business Environment", "Business Ethics and Decision Making"
    ],
    "A-Level Psychology": [
        "Approaches in Psychology", "Research Methods and Scientific Processes", "Biopsychology", 
        "Cognitive Psychology", "Social Psychology", "Developmental Psychology", "Individual Differences"
    ],
    "A-Level Sociology": [
        "Sociological Theories and Methods", "Family and Households", "Education", 
        "Crime and Deviance", "Media", "Stratification and Inequality", "Religion and Belief Systems"
    ],
    "A-Level Geography": [
        "Physical Geography", "Human Geography", "Contemporary Urban Environments", 
        "Population and Environment", "Resource Security", 
        "Geographical Skills and Fieldwork", "Hazards and Disaster Management"
    ],
    "A-Level History": [
        "Breadth Studies", "Depth Studies", "Historical Interpretations", 
        "Source Evaluation and Analysis", "Thematic Studies", 
        "Historical Investigations", "Historiography"
    ]
}

# Available Groq models
GROQ_MODELS = [
    "llama3-8b-8192",
    "llama3-70b-8192",
    "mixtral-8x7b-32768",
    "gemma-7b-it"
]

# Sample question formats
QUESTION_FORMATS = {
    "Multiple Choice": "Generate a multiple choice question with 4 options (A, B, C, D) and one correct answer.",
    "Short Answer": "Generate a question requiring a short answer (1-2 sentences).",
    "Calculation": "Generate a question requiring mathematical calculation and working.",
    "Extended Response": "Generate a question requiring an extended response (paragraph or essay).",
    "Practical": "Generate a question about experimental design or interpretation of results."
}

# Difficulty descriptions for enhanced prompting
DIFFICULTY_DESCRIPTIONS = {
    "Very Easy": {
        "description": "Basic recall of fundamental concepts, suitable for beginners or introduction to a topic.",
        "complexity": "Low complexity with straightforward application of basic knowledge.",
        "cognitive_level": "Knowledge and comprehension level, focusing on recall and basic understanding.",
        "marks_range": "Typically worth 1-2 marks in an exam setting."
    },
    "Easy": {
        "description": "Straightforward application of core concepts with minimal complexity.",
        "complexity": "Simple problem-solving requiring direct application of learned material.",
        "cognitive_level": "Basic application level, requiring understanding and simple implementation.",
        "marks_range": "Typically worth 2-3 marks in an exam setting."
    },
    "Medium": {
        "description": "Moderate difficulty requiring good understanding of concepts and some analysis.",
        "complexity": "Multi-step problems requiring connection between different concepts.",
        "cognitive_level": "Application and analysis level, requiring deeper thinking and evaluation.",
        "marks_range": "Typically worth 3-5 marks in an exam setting."
    },
    "Hard": {
        "description": "Challenging questions requiring thorough understanding and advanced application.",
        "complexity": "Complex scenarios requiring synthesis of multiple concepts and critical thinking.",
        "cognitive_level": "Analysis and synthesis level, requiring evaluation and creation of new ideas.",
        "marks_range": "Typically worth 5-8 marks in an exam setting."
    },
    "Very Hard": {
        "description": "Highly challenging questions at the upper limit of the curriculum difficulty.",
        "complexity": "Requires sophisticated understanding, creative problem-solving and critical evaluation.",
        "cognitive_level": "Synthesis and evaluation level, requiring original thinking and deep analysis.",
        "marks_range": "Typically worth 8+ marks in an exam setting."
    }
}

# Function to create a download link for PDF
def get_pdf_download_link(pdf_bytes, filename):
    """Generate a link to download the PDF file."""
    b64 = base64.b64encode(pdf_bytes).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}" class="download-btn">Download PDF</a>'
    return href

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    
    # API Key options
    st.subheader("API Configuration")
    use_custom_api = st.checkbox("Use Custom API Key", value=st.session_state.use_custom_api_key)
    st.session_state.use_custom_api_key = use_custom_api
    
    if st.session_state.use_custom_api_key:
        custom_api_key = st.text_input(
            "Enter Groq API Key", 
            value=st.session_state.custom_api_key,
            type="password",
            help="Enter your own Groq API key"
        )
        st.session_state.custom_api_key = custom_api_key
        st.markdown('<p class="api-key-warning">Your API key is never stored and only used for this session</p>', unsafe_allow_html=True)
    
    # Model selection
    st.subheader("Model Settings")
    selected_model = st.selectbox("Select Groq Model", GROQ_MODELS, index=1)  # Default to llama3-70b
    
    # Curriculum selection
    st.subheader("Content Settings")
    curriculum = st.selectbox("Select Curriculum", ["IGCSE", "A-Level"])
    
    # Subject selection
    subject = st.selectbox("Select Subject", SUBJECTS[curriculum])
    full_subject = f"{curriculum} {subject}"
    st.session_state.selected_subject = full_subject
    
    # Topic selection (if available)
    if full_subject in TOPICS:
        available_topics = TOPICS[full_subject]
        selected_topics = st.multiselect("Select Topics", available_topics)
        st.session_state.selected_topics = selected_topics
    
    # Question type
    question_type = st.selectbox("Question Type", list(QUESTION_FORMATS.keys()))
    
    # Enhanced difficulty slider with more options
    difficulty = st.select_slider(
        "Difficulty Level",
        options=["Very Easy", "Easy", "Medium", "Hard", "Very Hard"],
        value="Medium"
    )
    
    # Show description of selected difficulty
    if difficulty in DIFFICULTY_DESCRIPTIONS:
        st.info(DIFFICULTY_DESCRIPTIONS[difficulty]["description"])
    
    # Number of questions
    num_questions = st.slider("Number of Questions", 1, 10, 3)
    
    # Generate button
    generate_button = st.button("Generate Questions")
    
    # Clear Results button
    clear_button = st.button("Clear Results")
    if clear_button:
        st.session_state.generated_questions = []
        st.session_state.pdf_data = None
        st.session_state.pdf_filename = None
        st.rerun()

# Function to generate questions using Groq API
def generate_exam_questions(subject, topics, question_type, difficulty, num_questions, model, api_key):
    questions = []
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    api_url = "https://api.groq.com/openai/v1/chat/completions"
    
    # Create progress bar
    progress_bar = st.progress(0)
    progress_text = st.empty()
    
    for i in range(num_questions):
        progress_text.text(f"Generating question {i+1} of {num_questions}...")
        
        # Get difficulty details for enhanced prompting
        difficulty_details = DIFFICULTY_DESCRIPTIONS.get(difficulty, DIFFICULTY_DESCRIPTIONS["Medium"])
        
        # Create a detailed prompt with enhanced difficulty guidance
        prompt = f"""
        As an expert {subject} examiner, create an original exam question that meets these criteria:
        
        - Subject: {subject}
        - Topics: {', '.join(topics) if topics else 'Any relevant topic'}
        - Question Type: {question_type} - {QUESTION_FORMATS[question_type]}
        - Difficulty: {difficulty}
        
        DIFFICULTY DETAILS:
        - Description: {difficulty_details['description']}
        - Complexity Level: {difficulty_details['complexity']}
        - Cognitive Level: {difficulty_details['cognitive_level']}
        - Expected Marks Range: {difficulty_details['marks_range']}
        
        The question should:
        1. Follow the exact style and format of official {subject} past papers
        2. Be completely original (not copied from existing papers)
        3. Have an appropriate mark scheme/model answer
        4. Include any necessary diagrams or graphs described in text format
        5. Match the specified difficulty level precisely - this is important for exam preparation
        
        Structure your response as valid JSON with these fields:
        - question: The full question text
        - marks: Number of marks for this question (appropriate for the question type and difficulty)
        - difficulty: "{difficulty}"
        - question_type: "{question_type}"
        - mark_scheme: The mark scheme or model answer
        - topic: The specific topic this question addresses
        
        IMPORTANT: Your response must be valid JSON with NO additional text before or after. Do not include control characters, newlines within strings should be represented as \\n.
        """
        
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        # Add response_format if using a compatible model
        if model in ["llama3-70b-8192", "gemma-7b-it"]:
            data["response_format"] = {"type": "json_object"}
        
        try:
            # Call Groq API with backoff for rate limiting
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.post(api_url, headers=headers, json=data, timeout=30)
                    response.raise_for_status()
                    break
                except requests.exceptions.RequestException as e:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        st.warning(f"API request failed. Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        raise e
            
            result = response.json()
            
            # Extract and parse the response
            content = result['choices'][0]['message']['content']
            
            # Look for JSON content and parse it
            try:
                # Clean the content: remove control characters and escape sequences
                cleaned_content = re.sub(r'[\x00-\x1F\x7F]', '', content)
                
                # Try to find and extract JSON from the response
                if cleaned_content.find('{') >= 0 and cleaned_content.rfind('}') >= 0:
                    json_start = cleaned_content.find('{')
                    json_end = cleaned_content.rfind('}') + 1
                    json_content = cleaned_content[json_start:json_end]
                    
                    # Parse the JSON
                    question_data = json.loads(json_content)
                    
                    # Validate required fields
                    required_fields = ["question", "marks", "difficulty", "question_type", "mark_scheme", "topic"]
                    for field in required_fields:
                        if field not in question_data:
                            question_data[field] = "Not specified" if field != "marks" else "N/A"
                    
                    questions.append(question_data)
                else:
                    # If no JSON structure is found, create a structured response from the text
                    st.warning(f"No valid JSON structure found. Creating structured response from text.")
                    question_data = {
                        "question": cleaned_content,
                        "marks": "N/A",
                        "difficulty": difficulty,
                        "question_type": question_type,
                        "mark_scheme": "Not provided in response",
                        "topic": topics[0] if topics else "General"
                    }
                    questions.append(question_data)
                    
            except json.JSONDecodeError as e:
                st.warning(f"JSON decode error: {str(e)}. Creating structured response from text.")
                # Create a structured response even if JSON parsing fails
                question_data = {
                    "question": content,
                    "marks": "N/A",
                    "difficulty": difficulty,
                    "question_type": question_type,
                    "mark_scheme": "Not provided in response",
                    "topic": topics[0] if topics else "General"
                }
                questions.append(question_data)
                
        except Exception as e:
            st.error(f"Error generating question: {str(e)}")
            time.sleep(2)  # Rate limiting protection
        
        # Update progress
        progress_bar.progress((i + 1) / num_questions)
    
    # Clear progress indicators when done
    progress_bar.empty()
    progress_text.empty()
    
    return questions

# Improved PDF generation function using ReportLab
def generate_pdf(questions, subject):
    # Create a BytesIO object to store PDF
    buffer = io.BytesIO()
    
    try:
        # Set up styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=16,
            alignment=TA_CENTER,
            spaceAfter=12
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Heading2'],
            fontSize=12,
            alignment=TA_CENTER,
            spaceAfter=12,
            fontStyle='italic'
        )
        
        heading_style = ParagraphStyle(
            'Heading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=12,
            spaceAfter=6
        )
        
        question_style = ParagraphStyle(
            'QuestionStyle',
            parent=styles['Normal'],
            fontSize=12,
            spaceBefore=6,
            spaceAfter=6
        )
        
        mark_scheme_style = ParagraphStyle(
            'MarkScheme',
            parent=styles['Normal'],
            fontSize=12,
            spaceBefore=6,
            spaceAfter=6,
            backColor=colors.lightgreen,
            borderPadding=5
        )
        
        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            topMargin=36,
            bottomMargin=36,
            leftMargin=36,
            rightMargin=36
        )
        
        # Content list
        content = []
        
        # Add title and date
        content.append(Paragraph(f"{subject} Practice Questions", title_style))
        content.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d')}", subtitle_style))
        content.append(Spacer(1, 12))
        
        # Add questions
        for i, q in enumerate(questions, 1):
            # Question header
            content.append(Paragraph(f"Question {i} ({q.get('marks', 'N/A')} marks)", heading_style))
            
            # Topic and difficulty
            content.append(Paragraph(f"Topic: {q.get('topic', 'General')} - Difficulty: {q.get('difficulty', 'Medium')}", styles["Italic"]))
            
            # Question text
            question_text = q.get('question', 'Question text missing')
            # Handle potential newline characters in the text
            question_text = question_text.replace('\n', '<br/>')
            content.append(Paragraph(question_text, question_style))
            content.append(Spacer(1, 12))
        
        # Add a page break before mark schemes
        content.append(Paragraph("", styles["Normal"]))
        content.append(Spacer(1, 36))  # Force page break
        
        # Add mark scheme title
        content.append(Paragraph(f"{subject} Mark Schemes", title_style))
        content.append(Spacer(1, 12))
        
        # Add mark schemes
        for i, q in enumerate(questions, 1):
            content.append(Paragraph(f"Question {i} Mark Scheme:", heading_style))
            
            # Mark scheme text
            mark_scheme_text = q.get('mark_scheme', 'Mark scheme missing')
            # Handle potential newline characters in the text
            mark_scheme_text = mark_scheme_text.replace('\n', '<br/>')
            content.append(Paragraph(mark_scheme_text, mark_scheme_style))
            content.append(Spacer(1, 12))
        
        # Build the PDF
        doc.build(content)
        buffer.seek(0)
        return buffer.getvalue(), f"{subject.replace(' ', '_')}_questions.pdf"
    
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")
        return None, None

# Main content area - Generate questions if button is clicked
if 'generate_button' in locals() and generate_button:
    if not st.session_state.selected_subject:
        st.warning("Please select a subject first.")
    else:
        # Determine which API key to use
        api_key = st.session_state.custom_api_key if st.session_state.use_custom_api_key and st.session_state.custom_api_key else DEFAULT_GROQ_API_KEY
        
        if not api_key:
            st.error("Please enter a valid API key or use the default key.")
        else:
            try:
                with st.spinner(f"Generating {num_questions} {difficulty} {question_type} questions for {st.session_state.selected_subject}..."):
                    topics = st.session_state.selected_topics if st.session_state.selected_topics else []
                    generated_questions = generate_exam_questions(
                        st.session_state.selected_subject,
                        topics,
                        question_type,
                        difficulty,
                        num_questions,
                        selected_model,
                        api_key
                    )
                    st.session_state.generated_questions = generated_questions
                    
                    # Generate PDF after questions are created
                    if generated_questions:
                        with st.spinner("Preparing PDF for download..."):
                            pdf_data, pdf_filename = generate_pdf(
                                generated_questions,
                                st.session_state.selected_subject
                            )
                            if pdf_data:
                                st.session_state.pdf_data = pdf_data
                                st.session_state.pdf_filename = pdf_filename
            except Exception as e:
                st.error(f"An error occurred during question generation: {str(e)}")

# Display generated questions
if st.session_state.generated_questions:
    st.markdown('<h2 class="sub-header">Generated Questions</h2>', unsafe_allow_html=True)
    
    # Display PDF download link if PDF was generated
    if st.session_state.pdf_data and st.session_state.pdf_filename:
        st.markdown(
            get_pdf_download_link(st.session_state.pdf_data, st.session_state.pdf_filename),
            unsafe_allow_html=True
        )
    else:
        # Generate PDF on demand
        if st.button("Generate PDF for Download"):
            try:
                with st.spinner("Generating PDF..."):
                    pdf_data, pdf_filename = generate_pdf(
                        st.session_state.generated_questions,
                        st.session_state.selected_subject
                    )
                    if pdf_data:
                        st.session_state.pdf_data = pdf_data
                        st.session_state.pdf_filename = pdf_filename
                        st.markdown(
                            get_pdf_download_link(pdf_data, pdf_filename),
                            unsafe_allow_html=True
                        )
                    else:
                        st.error("Failed to generate PDF. Please try again.")
            except Exception as e:
                st.error(f"Error generating PDF: {str(e)}")
    
    # Display questions with collapsible mark schemes
    for i, question in enumerate(st.session_state.generated_questions, 1):
        difficulty_class = question.get('difficulty', 'Medium').lower()
        # Normalize difficulty class for CSS (remove spaces, convert to lowercase)
        difficulty_class = difficulty_class.lower().replace(" ", "-")
        
        with st.expander(f"Question {i}: {question.get('topic', 'Unspecified Topic')} ({question.get('marks', 'N/A')} marks)", expanded=True):
            st.markdown(f"""
            <div class="question-box">
                <p><strong>Question {i}</strong> <span class="difficulty-{difficulty_class}">[{question.get('difficulty', 'Medium')} - {question.get('marks', 'N/A')} marks]</span></p>
                <p>{question.get('question', 'Question text not available.')}</p>
            </div>
            <div class="mark-scheme">
                <p><strong>Mark Scheme</strong></p>
                <p>{question.get('mark_scheme', 'Mark scheme not available.')}</p>
            </div>
            """, unsafe_allow_html=True)

# Display information if no questions have been generated yet
else:
     st.markdown("""
    <div class="info-box">
        <h3>How to use this tool:</h3>
        <ol>
            <li>Select a Groq model from the sidebar (llama3-70b-8192 recommended for best results)</li>
            <li>Select your curriculum and subject</li>
            <li>Choose specific topics you want to practice (optional)</li>
            <li>Select the type of question and difficulty level</li>
            <li>Choose how many questions to generate</li>
            <li>Click "Generate Questions" and wait for the AI to create custom questions</li>
            <li>Review the questions and their mark schemes</li>
            <li>Download questions as a PDF for offline practice</li>
        </ol>
    </div>
    
    <div class="info-box">
        <h3>About Groq Models:</h3>
        <ul>
            <li><strong>llama3-70b-8192</strong>: Best quality, good for complex subjects</li>
            <li><strong>llama3-8b-8192</strong>: Faster but less detailed</li>
            <li><strong>mixtral-8x7b-32768</strong>: Good balance of speed and quality with longer context</li>
            <li><strong>gemma-7b-it</strong>: Efficient model for straightforward questions</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# Add a footer with disclaimer
st.markdown("---")
st.caption("""
**Disclaimer:** This tool uses AI to generate questions that mimic the style of past papers. While they follow the format and content expectations, 
these are not official exam questions and should be used as supplementary practice material only. Always refer to official past papers and resources 
from your examination board for the most accurate preparation.
""")