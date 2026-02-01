import os
from ollama import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

prompt = """
You are an expert resume parser. Given the following resume text, extract the following fields as JSON:        
- employment_status: 'employed' or 'unemployed'
- current_job_title: (if employed, the most recent/current job title, else null)
- current_employer: (if employed, the most recent/current employer, else null)
- current_job_period: (if employed, the period for the current job, else null)
- reasoning: brief explanation of how you determined the employment status

Resume text:
Ahmed Mohammed Al-Mansouri
Dubai, UAE | +971-50-123-4567 | ahmed.mansouri@email.com

Professional Summary
Results-driven Senior Sales Manager with 8+ years of experience. Proven track record of exceeding targets and building high-performing teams. Seeking to leverage expertise for greater impact and organizational growth.     
Work Experience
Senior Sales Manager - Al-Fardan Retail Group
Jan 2022 - Present | Dubai, UAE
Exceeded performance targets consistently
Led and mentored cross-functional teams
Improved operational efficiency by 35%

Education
Bachelor of Business Administration - United Arab Emirates University
Graduated 2015, GPA: 3.6/4.0

Skills
Leadership • Project Management • Strategic Planning • Team Building • Analysis • Problem Solving

Respond ONLY with a JSON object.
"""

client = Client(
    host="https://ollama.com",
    headers={'Authorization': 'Bearer ' + os.environ.get('OLLAMA_CLOUD_API_KEY')}
)


messages = [
  {
    'role': 'user',
    'content': prompt,
  },
]

# for part in client.chat('gpt-oss:120b', messages=messages, stream=True):
#   print(part['message']['content'], end='', flush=True)

response = client.chat('gpt-oss:120b', messages=messages)
print(response['message']['content'])