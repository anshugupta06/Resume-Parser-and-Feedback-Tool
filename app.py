from flask import Flask, render_template, request, send_file
import os
from werkzeug.utils import secure_filename
import random
import re
import docx
import fitz  # PyMuPDF
import json
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import string
from nltk.tokenize import word_tokenize
import textwrap

app = Flask(__name__)

# Set up upload folder and allowed file types
UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'pdf', 'docx'}

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit file size to 16MB

# Function to check if the file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to generate a unique filename
def generate_unique_filename(filename):
    extension = filename.rsplit('.', 1)[1].lower()
    random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{random_string}.{extension}"

def extract_text_from_pdf_pymupdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# Function to extract text from DOCX
def extract_text_from_docx(docx_path):
    doc = docx.Document(docx_path)
    text = ""
    for para in doc.paragraphs:
        text += para.text
    return text

# Function to parse the resume and extract text based on file type
def parse_resume(resume_path):
    extension = resume_path.rsplit('.', 1)[1].lower()
    if extension == 'pdf':
        return extract_text_from_pdf_pymupdf(resume_path)
    elif extension == 'docx':
        return extract_text_from_docx(resume_path)
    return ""

# Define stream-related skills
keywords = {
    # Computer Science (CS)
    'cs': [
        'ai', 'machine', 'python', 'java', 'c++', 'algorithms',
        'data structures', 'software', 'cloud', 'android', 'ios', 'web development', 'deep learning', 'pytorch', 'tensorflow', 
        'javascript', 'react', 'node.js', 'html', 'css', 'sql', 'nosql', 'mongodb', 'git', 'github', 'docker', 'kubernetes', 
        'devops', 'tensorflow', 'hadoop', 'spark', 'data science', 'big data', 'nlp', 'computer vision', 'cybersecurity', 
        'blockchain', 'docker', 'kubernetes', 'json', 'restful api', 'graphql', 'angular', 'flask', 'djangoreact', 'vue.js',
        'automation', 'testing', 'debugging', 'saas', 'ui/ux design'
    ],
    
    # Information Technology (IT)
    'it': [
        'network', 'cloud', 'aws', 'azure', 'itil', 'server', 'database', 'vpn', 'firewall', 'tcp/ip', 'dns', 'active directory',
        'virtualization', 'vmware', 'storage', 'palo alto', 'power shell', 'windows server', 'red hat', 'docker', 'network security',
        'cloud security', 'data backup', 'automation', 'ci/cd', 'python', 'powershell', 'automation', 'cloudformation', 
        'sysadmin', 'incident management', 'log analysis', 'it service management', 'cloud migration', 'elastic search', 'splunk'
    ],

    # Electrical Engineering (EE)
    'ee': [
        'vlsi', 'control systems', 'microcontrollers', 'embedded systems', 'signal processing', 'analog circuits', 'power systems', 
        'robotics', 'automation', 'scada', 'power electronics', 'motor control', 'circuit design', 'pcb design', 'mechatronics', 
        'renewable energy', 'solar power', 'electromagnetics', 'signal integrity', 'communication systems', 'rf', 'antenna design',
        'system on chip', 'iot', 'energy storage', 'hvac', 'energy systems', 'electrical distribution', 'grid management'
    ],

    # Mechanical Engineering (ME)
    'me': [
        'solidworks', 'autocad', 'thermal', 'robotics', 'manufacturing', 'materials science', 'fluid mechanics', 'dynamics', 'control',
        'finite element analysis', 'cam', 'cnc programming', 'product design', 'vibration analysis', 'heat transfer', 'mechanics', 
        'turbines', 'gears', 'casting', 'manufacturing processes', 'machine learning for manufacturing', 'stress analysis', 
        'design for manufacturability', 'testing', 'composite materials', 'mechanical design', 'structural analysis', 'materials testing',
        'advanced manufacturing', 'aerospace engineering', '3d printing', 'hydraulics', 'pneumatics', 'control systems', 'energy'
    ],

    # Civil Engineering (CE)
    'ce': [
        'autocad', 'revit', 'structural engineering', 'civil 3d', 'surveying', 'geotechnical', 'foundation engineering', 'hydraulics', 
        'transportation engineering', 'environmental engineering', 'water resources', 'building information modeling', 'seismic design',
        'earthquake engineering', 'structural design', 'concrete technology', 'steel structures', 'geotechnical analysis', 'soil mechanics', 
        'land surveying', 'soil testing', 'traffic engineering', 'sustainability', 'stormwater management', 'urban planning', 'bridge design', 
        'project management', 'site management', 'construction', 'environmental impact assessment', 'sustainable development', 'plumbing'
    ],

    # Other fields and general terms
    'general': [
        'resume', 'contact', 'email', 'linkedin', 'github', 'portfolio', 'skills', 'projects', 'experience', 'education', 
        'certifications', 'languages', 'achievements', 'interests', 'volunteer', 'workshop', 'seminar', 'conferences', 'leadership',
        'teamwork', 'communication', 'problem-solving', 'public speaking', 'collaboration', 'innovation', 'creativity', 
        'management', 'organization', 'internship', 'programming', 'research', 'publications', 'awards', 'honors', 'references', 
        'work experience', 'academic', 'bachelor', 'master', 'degree', 'gpa', 'final year', 'thesis', 'dissertation', 'project management'
    ]
}

def calculate_ats_score(resume_path, stream):
    resume_text = parse_resume(resume_path).lower()
    print("Parsed Resume Text:", resume_text[:500])  # Debugging output

    ats_score = 10  # Start from 10 to avoid 0 score issue
    feedback = []

    # --- 1. Structure & Formatting (20 points) ---
    if 500 < len(resume_text) < 3000:  # Ideal resume length
        ats_score += 5
    else:
        feedback.append("Ensure your resume is between 1-2 pages for better readability.")

    required_sections = ['contact', 'skills', 'education', 'experience']
    structure_score = sum(3 for section in required_sections if section in resume_text)
    ats_score += structure_score  # 3 points per section
    if structure_score < 12:
        feedback.append("Consider adding missing sections for better ATS compatibility.")

    if '-' in resume_text or '•' in resume_text:  # Checking bullet points
        ats_score += 3
    else:
        feedback.append("Use bullet points in experience and skills sections for better readability.")

    if resume_path.endswith('.pdf'):  # PDF check
        ats_score += 5
    else:
        feedback.append("Save your resume as a PDF for better ATS parsing.")

    # --- 2. Contact Information (10 points) ---
    name_pattern = re.compile(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', re.IGNORECASE)
    email_pattern = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', re.IGNORECASE)
    phone_pattern = re.compile(r'(\+?\d{1,2}\s?)?(\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}', re.IGNORECASE)

    if re.search(name_pattern, resume_text):
        ats_score += 3
    else:
        feedback.append("Your name is missing from the resume.")

    if re.search(email_pattern, resume_text):
        ats_score += 3
    else:
        feedback.append("Include a professional email in your resume.")

    if re.search(phone_pattern, resume_text):
        ats_score += 3
    else:
        feedback.append("Your resume should include a contact number.")

    # --- 3. Work Experience & Achievements (20 points) ---
    if 'experience' in resume_text:
        ats_score += 5
    else:
        feedback.append("Add a 'Work Experience' section to strengthen your resume.")

    years_experience = len(re.findall(r'\d{4}[-–]\d{4}', resume_text))  # Finding year ranges
    ats_score += min(years_experience * 2, 10)

    if re.search(r'\b(\d+%|\d+\s?(k|million|billion))\b', resume_text):  # Checking for numbers in experience
        ats_score += 5
    else:
        feedback.append("Include measurable achievements (e.g., 'Increased efficiency by 20%').")

    # --- 4. Education & Certifications (10 points) ---
    if 'education' in resume_text and ('college' in resume_text or 'university' in resume_text):
        ats_score += 3
    else:
        feedback.append("Include your college/university details.")

    if 'certification' in resume_text:
        ats_score += 4
    else:
        feedback.append("Add certifications to enhance your resume.")

    # --- 5. Skills & Keywords Match (20 points) ---
    stream_keywords = keywords.get(stream, [])
    skill_matches = sum(1 for keyword in stream_keywords if re.search(r'\b' + re.escape(keyword) + r'\b', resume_text, re.IGNORECASE))
    
    skill_match_percentage = (skill_matches / len(stream_keywords)) * 100 if stream_keywords else 0
    ats_score += min(skill_match_percentage // 5, 10)  # Max 10 points

    if skill_matches < 2:
        feedback.append("Your resume lacks important skills. Add more relevant keywords.")

    # --- 6. Projects, Publications, & Extracurriculars (10 points) ---
    if stream == 'cs' and 'project' in resume_text:
        ats_score += 5
    elif stream == 'cs':
        feedback.append("For CS, add at least one project to improve your resume.")

    if 'research' in resume_text or 'publication' in resume_text or 'blog' in resume_text:
        ats_score += 5
    else:
        feedback.append("Publishing blogs, research papers, or projects can improve your resume.")

    # --- 7. ATS Optimization (10 points) ---
    if not re.search(r'\.(jpg|png|gif|svg)', resume_text):  # Checking if there are no images
        ats_score += 5
    else:
        feedback.append("Avoid adding images or graphics to your resume.")

    if all(heading in resume_text for heading in ['work experience', 'education', 'skills']):
        ats_score += 5

    # --- Final Adjustments ---
    ats_score = max(ats_score, 10)  # Ensuring no score goes below 10
    ats_score = min(ats_score, 100)  # Ensuring max score is 100

    print(f"Final ATS Score: {ats_score}")

    return ats_score, feedback


def generate_pdf(ats_score, feedback):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    # Margins and spacing
    left_margin = 50
    right_margin = 550  
    line_spacing = 20
    y_position = 750  

    # ATS Score Heading
    c.setFont("Helvetica-Bold", 12)
    c.drawString(left_margin, y_position, f"ATS Score: {ats_score}")
    y_position -= 30  

    # Feedback Heading
    c.drawString(left_margin, y_position, "Feedback:")
    y_position -= 20  
    c.setFont("Helvetica", 12)

    # Ensure feedback is a list
    if isinstance(feedback, str):
        feedback = [feedback]

    # Check if feedback is empty
    if not feedback:
        feedback = ["No feedback available."]

    # Wrapping text
    for item in feedback:
        wrapped_lines = textwrap.wrap(item, width=75)  # Wrap at 75 characters
        for line in wrapped_lines:
            c.drawString(left_margin, y_position, f"- {line}")
            y_position -= line_spacing

            if y_position < 50:  # New page if needed
                c.showPage()
                c.setFont("Helvetica", 12)
                y_position = 750

    c.save()
    buffer.seek(0)
    return buffer

@app.route('/', methods=['GET', 'POST'])

def index():
    ats_score = None
    feedback = None

    if request.method == 'POST':
        stream = request.form['stream']

        if 'file' not in request.files:
            return 'No file part', 400
        
        file = request.files['file']

        if file.filename == '':
            return 'No selected file', 400
        
        if file and allowed_file(file.filename):
            filename = generate_unique_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Save the file and check if it's saved properly
            file.save(filepath)
            print(f"File saved at: {filepath}")  # Debugging file saving
            
            ats_score, feedback = calculate_ats_score(filepath, stream)
            print(f"ATS Score: {ats_score}, Feedback: {feedback}")  # Debugging the ATS score and feedback
            
            # Generate the PDF for feedback and ATS score
            pdf_buffer = generate_pdf(ats_score, feedback)

            # Send PDF file as a response
            return send_file(pdf_buffer, as_attachment=True, download_name="ATS_Feedback.pdf", mimetype='application/pdf')
    
    return render_template('index.html', ats_score=ats_score, feedback=feedback)

if __name__ == '__main__':
    app.run(debug=True)