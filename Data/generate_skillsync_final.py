"""
SkillSync HRMS - Part 1: Reference Tables + Employees
"""
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

np.random.seed(42)
random.seed(42)

N_EMPLOYEES   = 200
FOUNDED       = datetime(2023, 1, 1)
HIRE_END      = datetime(2025, 6, 30)
ATTEND_START  = datetime(2023, 1, 1)
ATTEND_END    = datetime(2025, 12, 31)
NOW           = datetime(2026, 1, 1)
TURNOVER_RATE = 0.25

def safe_end(val):
    if val and str(val) != 'nan':
        return datetime.strptime(str(val), '%Y-%m-%d')
    return NOW

# ── 1. DEPARTMENTS ────────────────────────────────────────────
departments = pd.DataFrame([
    (1,'Engineering'),(2,'Analytics'),(3,'Human Resources'),
    (4,'Marketing'),(5,'Finance'),(6,'Operations'),
    (7,'Sales'),(8,'Customer Support'),
], columns=['department_id','department_name'])
departments.to_csv('/home/claude/departments.csv', index=False)
print("✅ departments.csv")

# ── 2. SKILLS CATALOG (expanded, more complexity-5) ──────────
skills_raw = [
    # Data Science
    ('SK-101','Python',                  'Technical',  1),
    ('SK-102','NumPy',                   'Technical',  2),
    ('SK-103','Pandas',                  'Technical',  2),
    ('SK-104','Matplotlib',              'Technical',  2),
    ('SK-105','Scikit-learn',            'Technical',  3),
    ('SK-106','PyTorch',                 'Technical',  4),
    ('SK-107','TensorFlow',              'Technical',  4),
    ('SK-108','Deep Learning',           'Technical',  5),
    ('SK-109','Statistics',              'Technical',  2),
    ('SK-110','Machine Learning',        'Technical',  4),
    ('SK-111','Data Analysis',           'Technical',  3),
    ('SK-112','Data Visualization',      'Technical',  3),
    ('SK-113','Feature Engineering',     'Technical',  4),
    ('SK-114','Model Deployment (MLOps)','Technical',  5),
    ('SK-115','A/B Testing',             'Technical',  3),
    # Database
    ('SK-116','SQL',                     'Technical',  1),
    ('SK-117','PostgreSQL',              'Technical',  2),
    ('SK-118','Data Modeling',           'Technical',  3),
    ('SK-119','ETL Development',         'Technical',  4),
    ('SK-120','Apache Spark',            'Technical',  5),
    ('SK-121','Data Warehousing',        'Technical',  4),
    ('SK-122','NoSQL (MongoDB)',          'Technical',  3),
    # Frontend
    ('SK-123','HTML & CSS',              'Technical',  1),
    ('SK-124','JavaScript',              'Technical',  2),
    ('SK-125','TypeScript',              'Technical',  3),
    ('SK-126','React',                   'Technical',  3),
    ('SK-127','Next.js',                 'Technical',  4),
    ('SK-128','UI/UX Design',            'Technical',  3),
    ('SK-129','Figma',                   'Technical',  2),
    # Backend
    ('SK-130','Node.js',                 'Technical',  3),
    ('SK-131','Express.js',              'Technical',  3),
    ('SK-132','REST API Design',         'Technical',  3),
    ('SK-133','GraphQL',                 'Technical',  4),
    ('SK-134','Django',                  'Technical',  3),
    ('SK-135','FastAPI',                 'Technical',  3),
    ('SK-136','Microservices',           'Technical',  5),
    ('SK-137','System Design',           'Technical',  5),
    # DevOps / Cloud
    ('SK-138','Linux',                   'Technical',  1),
    ('SK-139','Bash Scripting',          'Technical',  2),
    ('SK-140','Git',                     'Technical',  1),
    ('SK-141','Docker',                  'Technical',  3),
    ('SK-142','Kubernetes',              'Technical',  4),
    ('SK-143','CI/CD Pipelines',         'Technical',  4),
    ('SK-144','Terraform',               'Technical',  4),
    ('SK-145','AWS',                     'Technical',  3),
    ('SK-146','Azure',                   'Technical',  3),
    ('SK-147','Cloud Architecture',      'Technical',  5),
    # Testing
    ('SK-148','Unit Testing',            'Technical',  2),
    ('SK-149','Integration Testing',     'Technical',  3),
    ('SK-150','Test Automation',         'Technical',  4),
    # Soft Skills
    ('SK-151','Communication',           'Soft',        1),
    ('SK-152','Teamwork',                'Soft',        1),
    ('SK-153','Problem Solving',         'Soft',        2),
    ('SK-154','Critical Thinking',       'Soft',        2),
    ('SK-155','Time Management',         'Soft',        1),
    ('SK-156','Presentation Skills',     'Soft',        2),
    ('SK-157','Negotiation',             'Soft',        3),
    ('SK-158','Customer Service',        'Soft',        2),
    ('SK-159','Conflict Resolution',     'Soft',        3),
    ('SK-160','Emotional Intelligence',  'Soft',        3),
    # Management
    ('SK-161','Leadership',              'Management',  3),
    ('SK-162','Mentoring',               'Management',  4),
    ('SK-163','Decision Making',         'Management',  3),
    ('SK-164','Project Management',      'Management',  4),
    ('SK-165','Agile',                   'Management',  3),
    ('SK-166','Scrum',                   'Management',  3),
    ('SK-167','Stakeholder Management',  'Management',  4),
    ('SK-168','Operations Management',   'Management',  4),
    ('SK-169','Production Management',   'Management',  5),
    ('SK-170','Strategic Planning',      'Management',  5),
    ('SK-171','Risk Management',         'Management',  5),
    ('SK-172','Change Management',       'Management',  5),
    ('SK-173','Budget Management',       'Management',  4),
    ('SK-174','Vendor Management',       'Management',  4),
    # Domain
    ('SK-175','Digital Marketing',       'Domain',      2),
    ('SK-176','SEO',                     'Domain',      3),
    ('SK-177','Content Marketing',       'Domain',      3),
    ('SK-178','Social Media Marketing',  'Domain',      2),
    ('SK-179','Accounting',              'Domain',      2),
    ('SK-180','Financial Analysis',      'Domain',      3),
    ('SK-181','Budget Planning',         'Domain',      4),
    ('SK-182','Financial Modeling',      'Domain',      5),
    ('SK-183','HR Management',           'Domain',      3),
    ('SK-184','Recruitment',             'Domain',      3),
    ('SK-185','Sales Techniques',        'Domain',      2),
    ('SK-186','CRM Tools',               'Domain',      2),
    ('SK-187','ERP Systems',             'Domain',      4),
    ('SK-188','Supply Chain Management', 'Domain',      5),
]
skills_catalog = pd.DataFrame(skills_raw,
    columns=['skill_id','skill_name','domain','complexity_level'])
skills_catalog.to_csv('/home/claude/skills_catalog.csv', index=False)
print(f"✅ skills_catalog.csv ({len(skills_catalog)} skills)")

sid   = dict(zip(skills_catalog['skill_name'], skills_catalog['skill_id']))
sname = dict(zip(skills_catalog['skill_id'],   skills_catalog['skill_name']))
all_skill_ids = skills_catalog['skill_id'].tolist()

# ── 3. SKILL CHAIN DAG (with weight column) ───────────────────
# weight = manual expert-based assignment (0.1–1.0)
dag_raw = [
    # Data Science
    ('Python','NumPy',              0.9),('Python','Pandas',             0.9),
    ('Python','Matplotlib',         0.8),('Python','Django',             0.8),
    ('Python','FastAPI',            0.8),('NumPy','Scikit-learn',        0.9),
    ('Pandas','Scikit-learn',       0.9),('Pandas','Data Analysis',      0.9),
    ('Statistics','Data Analysis',  0.8),('Statistics','Machine Learning',0.8),
    ('Scikit-learn','Machine Learning',0.9),('Scikit-learn','PyTorch',   0.8),
    ('Scikit-learn','TensorFlow',   0.8),('PyTorch','Deep Learning',     0.9),
    ('TensorFlow','Deep Learning',  0.9),('Machine Learning','Feature Engineering',0.9),
    ('Machine Learning','Model Deployment (MLOps)',0.8),
    ('Matplotlib','Data Visualization',0.9),
    ('Data Analysis','Data Visualization',0.8),
    ('Data Analysis','A/B Testing', 0.7),
    # Database
    ('SQL','PostgreSQL',            0.9),('PostgreSQL','Data Modeling',  0.9),
    ('Data Modeling','ETL Development',0.9),('ETL Development','Apache Spark',0.8),
    ('ETL Development','Data Warehousing',0.8),('SQL','NoSQL (MongoDB)',  0.5),
    # Frontend
    ('HTML & CSS','JavaScript',     0.9),('JavaScript','TypeScript',     0.9),
    ('JavaScript','Node.js',        0.8),('TypeScript','React',          0.9),
    ('React','Next.js',             0.9),('HTML & CSS','UI/UX Design',   0.7),
    ('Figma','UI/UX Design',        0.8),
    # Backend
    ('Node.js','Express.js',        0.9),('Express.js','REST API Design',0.9),
    ('REST API Design','GraphQL',   0.8),('REST API Design','Microservices',0.8),
    ('System Design','Microservices',0.9),
    # DevOps
    ('Linux','Bash Scripting',      0.9),('Linux','Docker',              0.8),
    ('Git','Docker',                0.7),('Git','CI/CD Pipelines',       0.9),
    ('Docker','Kubernetes',         0.9),('Docker','CI/CD Pipelines',    0.8),
    ('Kubernetes','Terraform',      0.8),('Linux','AWS',                 0.7),
    ('Linux','Azure',               0.7),('AWS','Cloud Architecture',    0.9),
    ('Azure','Cloud Architecture',  0.9),
    # Testing
    ('Unit Testing','Integration Testing',0.9),
    ('Integration Testing','Test Automation',0.9),
    # Soft → Management
    ('Communication','Presentation Skills',0.8),
    ('Communication','Negotiation',        0.7),
    ('Communication','Leadership',         0.8),
    ('Teamwork','Leadership',              0.8),
    ('Critical Thinking','Decision Making',0.9),
    ('Emotional Intelligence','Leadership',0.7),
    ('Leadership','Mentoring',             0.9),
    ('Leadership','Project Management',    0.9),
    ('Leadership','Stakeholder Management',0.8),
    ('Leadership','Strategic Planning',    0.8),
    ('Leadership','Change Management',     0.7),
    ('Project Management','Agile',         0.9),
    ('Agile','Scrum',                      0.9),
    ('Project Management','Operations Management',0.8),
    ('Operations Management','Production Management',0.9),
    ('Operations Management','Risk Management',0.8),
    ('Project Management','Budget Management',0.8),
    ('Budget Management','Vendor Management',0.7),
    # Domain
    ('Digital Marketing','SEO',            0.9),
    ('Digital Marketing','Content Marketing',0.8),
    ('Digital Marketing','Social Media Marketing',0.8),
    ('Accounting','Financial Analysis',    0.9),
    ('Financial Analysis','Budget Planning',0.9),
    ('Financial Analysis','Financial Modeling',0.9),
    ('HR Management','Recruitment',        0.9),
    ('Sales Techniques','CRM Tools',       0.8),
    ('CRM Tools','ERP Systems',            0.7),
    ('Operations Management','Supply Chain Management',0.8),
]
dag_rows = []
for p, t, w in dag_raw:
    if p in sid and t in sid:
        dag_rows.append({'prerequisite_skill_id': sid[p],
                         'target_skill_id':       sid[t],
                         'weight':                w})
skill_chain_dag = pd.DataFrame(dag_rows)
skill_chain_dag.to_csv('/home/claude/skill_chain_dag.csv', index=False)
print(f"✅ skill_chain_dag.csv ({len(skill_chain_dag)} edges)")

prereq_lookup = {}
for _, row in skill_chain_dag.iterrows():
    prereq_lookup.setdefault(row['target_skill_id'], []).append(row['prerequisite_skill_id'])

# ── 4. JOB ROLES (with bonus_eligibility_percentage) ─────────
role_info = {
    # id:(name, dept_id, level, sal_min, sal_max, headcount_w, bonus_pct)
    1:  ('Frontend Developer',           1,'Junior', 10000,18000,10, 5),
    2:  ('Senior Frontend Developer',    1,'Senior', 22000,35000, 4,12),
    3:  ('Backend Developer',            1,'Junior', 12000,20000,10, 5),
    4:  ('Full Stack Developer',         1,'Mid',    15000,26000, 8, 8),
    5:  ('Tech Lead',                    1,'Lead',   30000,42000, 2,18),
    6:  ('DevOps Engineer',              1,'Mid',    16000,28000, 5, 8),
    7:  ('QA Engineer',                  1,'Junior', 10000,17000, 5, 5),
    8:  ('Data Analyst',                 2,'Junior', 11000,19000, 8, 5),
    9:  ('Senior Data Analyst',          2,'Senior', 22000,34000, 3,12),
    10: ('Business Analyst',             2,'Mid',    13000,22000, 4, 8),
    11: ('HR Specialist',                3,'Junior',  8000,13000, 5, 4),
    12: ('HR Manager',                   3,'Manager',20000,32000, 2,15),
    13: ('Marketing Specialist',         4,'Junior',  9000,15000, 5, 6),
    14: ('Marketing Manager',            4,'Manager',19000,30000, 2,15),
    15: ('UX Designer',                  4,'Mid',    12000,21000, 4, 7),
    16: ('Financial Analyst',            5,'Mid',    13000,22000, 4, 8),
    17: ('Accountant',                   5,'Junior',  9000,15000, 5, 4),
    18: ('Operations Manager',           6,'Manager',22000,36000, 2,18),
    19: ('Product Manager',              6,'Senior', 24000,38000, 3,15),
    20: ('Sales Representative',         7,'Junior',  7000,13000, 8,10),
    21: ('Senior Sales Representative',  7,'Senior', 15000,26000, 3,18),
    22: ('Customer Support Specialist',  8,'Junior',  6500,11000, 8, 4),
}
job_roles_df = pd.DataFrame([
    {'job_role_id': rid, 'role_name': v[0], 'department_id': v[1],
     'level': v[2], 'salary_min': v[3], 'salary_max': v[4],
     'bonus_eligibility_percentage': v[6]}
    for rid, v in role_info.items()
])
job_roles_df.to_csv('/home/claude/job_roles.csv', index=False)
print("✅ job_roles.csv")

# ── 5. JOB ROLE REQUIREMENTS (no skill_name, only skill_id) ──
role_skill_map = {
    'Frontend Developer':          [('HTML & CSS',2,.20),('JavaScript',2,.25),('TypeScript',1,.15),('React',2,.25),('Git',1,.10),('Communication',1,.05)],
    'Senior Frontend Developer':   [('HTML & CSS',3,.10),('JavaScript',4,.20),('TypeScript',3,.15),('React',4,.20),('Next.js',3,.15),('Git',3,.05),('UI/UX Design',2,.05),('Leadership',2,.05),('Mentoring',1,.05)],
    'Backend Developer':           [('Python',2,.20),('Django',2,.20),('FastAPI',1,.10),('SQL',2,.20),('REST API Design',2,.15),('Git',1,.10),('Unit Testing',1,.05)],
    'Full Stack Developer':        [('HTML & CSS',2,.10),('JavaScript',3,.15),('TypeScript',2,.10),('React',2,.10),('Node.js',2,.10),('Express.js',2,.10),('SQL',2,.15),('REST API Design',2,.10),('Git',2,.05),('Docker',1,.05)],
    'Tech Lead':                   [('JavaScript',4,.10),('TypeScript',4,.10),('React',4,.08),('Node.js',4,.08),('REST API Design',4,.08),('Docker',3,.06),('Git',4,.05),('System Design',3,.08),('Leadership',4,.15),('Mentoring',3,.10),('Project Management',3,.08),('Communication',4,.04)],
    'DevOps Engineer':             [('Linux',3,.15),('Bash Scripting',2,.10),('Git',3,.10),('Docker',3,.20),('Kubernetes',2,.15),('CI/CD Pipelines',3,.15),('AWS',2,.10),('Terraform',1,.05)],
    'QA Engineer':                 [('Unit Testing',2,.30),('Integration Testing',2,.25),('Python',1,.15),('Git',1,.10),('Problem Solving',2,.10),('Communication',1,.10)],
    'Data Analyst':                [('SQL',3,.20),('Python',2,.15),('Pandas',2,.15),('Data Analysis',3,.20),('Data Visualization',2,.15),('Statistics',2,.10),('Communication',2,.05)],
    'Senior Data Analyst':         [('SQL',4,.12),('Python',3,.10),('Pandas',3,.10),('NumPy',3,.08),('Data Analysis',4,.15),('Machine Learning',3,.12),('Feature Engineering',2,.08),('Data Visualization',3,.10),('Statistics',3,.05),('Leadership',2,.05),('Presentation Skills',3,.05)],
    'Business Analyst':            [('SQL',2,.15),('Data Analysis',3,.20),('Data Visualization',2,.10),('Communication',4,.20),('Critical Thinking',3,.15),('Presentation Skills',3,.10),('Stakeholder Management',2,.10)],
    'HR Specialist':               [('HR Management',2,.30),('Recruitment',2,.25),('Communication',3,.20),('Teamwork',2,.15),('Time Management',2,.10)],
    'HR Manager':                  [('HR Management',4,.20),('Recruitment',3,.15),('Leadership',4,.20),('Communication',4,.15),('Decision Making',3,.15),('Mentoring',3,.10),('Budget Management',2,.05)],
    'Marketing Specialist':        [('Digital Marketing',3,.25),('SEO',2,.20),('Content Marketing',2,.20),('Social Media Marketing',2,.15),('Communication',3,.10),('Data Analysis',2,.10)],
    'Marketing Manager':           [('Digital Marketing',4,.20),('SEO',3,.10),('Content Marketing',3,.10),('Leadership',4,.20),('Communication',4,.15),('Budget Planning',3,.15),('Decision Making',3,.10)],
    'UX Designer':                 [('UI/UX Design',3,.30),('Figma',3,.20),('HTML & CSS',2,.15),('Communication',3,.20),('Problem Solving',3,.15)],
    'Financial Analyst':           [('Accounting',2,.15),('Financial Analysis',3,.30),('SQL',2,.12),('Data Analysis',2,.15),('Critical Thinking',3,.15),('Presentation Skills',2,.08),('Financial Modeling',2,.05)],
    'Accountant':                  [('Accounting',3,.40),('Financial Analysis',2,.25),('Critical Thinking',2,.15),('Communication',2,.10),('Time Management',2,.10)],
    'Operations Manager':          [('Operations Management',4,.20),('Production Management',3,.15),('Leadership',4,.20),('Project Management',4,.15),('Decision Making',3,.15),('Budget Management',3,.10),('Communication',4,.05)],
    'Product Manager':             [('Project Management',3,.15),('Agile',3,.12),('Scrum',2,.08),('Communication',4,.15),('Leadership',3,.12),('Data Analysis',3,.10),('Stakeholder Management',3,.10),('Decision Making',3,.10),('Strategic Planning',2,.08)],
    'Sales Representative':        [('Sales Techniques',2,.35),('CRM Tools',2,.20),('Communication',3,.25),('Negotiation',2,.20)],
    'Senior Sales Representative': [('Sales Techniques',4,.25),('CRM Tools',3,.15),('Communication',4,.20),('Negotiation',4,.20),('Leadership',3,.10),('Presentation Skills',3,.10)],
    'Customer Support Specialist': [('Customer Service',3,.35),('Communication',3,.30),('Problem Solving',2,.20),('CRM Tools',1,.15)],
}
role_req_rows = []
for rid, (rname,*_) in role_info.items():
    for sname_r, min_prof, weight in role_skill_map.get(rname, []):
        if sname_r in sid:
            role_req_rows.append({'job_role_id': rid, 'required_skill_id': sid[sname_r],
                                  'min_proficiency': min_prof, 'importance_weight': weight})
job_role_requirements = pd.DataFrame(role_req_rows)
job_role_requirements.to_csv('/home/claude/job_role_requirements.csv', index=False)
print(f"✅ job_role_requirements.csv ({len(job_role_requirements)} rows)")

req_by_role = {}
for rid in role_info:
    req_by_role[rid] = job_role_requirements[
        job_role_requirements['job_role_id']==rid]['required_skill_id'].tolist()

# ── 6. LEARNING RESOURCES (expanded + category + skill_level) ─
lr_data = [
    # Data Science
    ('LR-001','Python for Beginners',                'Course',      10,'High',  sid['Python'],                'edX',      'Data Science',    'Beginner'),
    ('LR-002','Python for Data Science',             'Course',      12,'High',  sid['Pandas'],                'Coursera', 'Data Science',    'Intermediate'),
    ('LR-003','SQL Masterclass',                     'Course',      10,'High',  sid['SQL'],                   'edX',      'Data Engineering','Beginner'),
    ('LR-004','Advanced SQL & PostgreSQL',           'Course',       8,'Medium',sid['PostgreSQL'],            'Udemy',    'Data Engineering','Intermediate'),
    ('LR-005','Machine Learning A-Z',                'Course',      20,'High',  sid['Machine Learning'],      'Coursera', 'Data Science',    'Intermediate'),
    ('LR-006','Deep Learning Specialization',        'Course',      30,'Medium',sid['Deep Learning'],         'Coursera', 'Data Science',    'Advanced'),
    ('LR-007','Feature Engineering for ML',          'Course',       8,'Medium',sid['Feature Engineering'],   'Udemy',    'Data Science',    'Advanced'),
    ('LR-008','MLOps: Model Deployment',             'Course',      12,'Low',   sid['Model Deployment (MLOps)'],'edX',    'Data Science',    'Advanced'),
    ('LR-009','Statistics for Data Science',         'Course',       8,'Medium',sid['Statistics'],            'edX',      'Data Science',    'Beginner'),
    # Frontend & Backend
    ('LR-010','React & TypeScript Bootcamp',         'Course',      16,'High',  sid['React'],                 'Udemy',    'IT',              'Intermediate'),
    ('LR-011','Next.js Full-Stack Development',      'Course',      14,'Medium',sid['Next.js'],               'Udemy',    'IT',              'Advanced'),
    ('LR-012','Node.js & Express.js Deep Dive',      'Course',      12,'High',  sid['Express.js'],            'Udemy',    'IT',              'Intermediate'),
    ('LR-013','REST API Design & GraphQL',           'Course',      10,'Medium',sid['GraphQL'],               'Coursera', 'IT',              'Advanced'),
    ('LR-014','System Design for Engineers',         'Course',      16,'Medium',sid['System Design'],         'edX',      'Engineering',     'Advanced'),
    ('LR-015','Microservices Architecture',          'Course',      14,'Low',   sid['Microservices'],         'Coursera', 'Engineering',     'Advanced'),
    # DevOps / Cloud
    ('LR-016','Docker & Kubernetes Essentials',      'Course',      14,'Medium',sid['Docker'],                'Coursera', 'IT',              'Intermediate'),
    ('LR-017','Kubernetes Advanced',                 'Course',      12,'Low',   sid['Kubernetes'],            'edX',      'IT',              'Advanced'),
    ('LR-018','CI/CD with GitHub Actions',           'Course',      10,'Medium',sid['CI/CD Pipelines'],       'Udemy',    'IT',              'Intermediate'),
    ('LR-019','AWS Cloud Practitioner',              'Certification',16,'High', sid['AWS'],                   'AWS',      'IT',              'Beginner'),
    ('LR-020','Cloud Architecture Design',           'Course',      14,'Medium',sid['Cloud Architecture'],    'Coursera', 'IT',              'Advanced'),
    ('LR-021','Terraform Infrastructure as Code',    'Course',       8,'Low',   sid['Terraform'],             'Udemy',    'IT',              'Advanced'),
    # Testing
    ('LR-022','Software Testing Fundamentals',       'Course',       8,'Medium',sid['Unit Testing'],          'edX',      'IT',              'Beginner'),
    ('LR-023','Test Automation with Selenium',       'Course',      10,'Medium',sid['Test Automation'],       'Udemy',    'IT',              'Intermediate'),
    # Management & Leadership
    ('LR-024','Leadership Essentials',               'Course',       6,'High',  sid['Leadership'],            'Coursera', 'Management',      'Beginner'),
    ('LR-025','Agile & Scrum Certification',         'Certification',16,'High', sid['Agile'],                 'Scrum.org','Management',      'Intermediate'),
    ('LR-026','Project Management Professional',     'Certification',40,'Medium',sid['Project Management'],   'PMI',      'Management',      'Advanced'),
    ('LR-027','Strategic Planning & Execution',      'Course',       8,'Low',   sid['Strategic Planning'],    'Coursera', 'Management',      'Advanced'),
    ('LR-028','Risk Management Fundamentals',        'Course',       6,'Low',   sid['Risk Management'],       'edX',      'Management',      'Advanced'),
    ('LR-029','Operations & Production Management',  'Course',      10,'Medium',sid['Production Management'], 'Coursera', 'Management',      'Advanced'),
    ('LR-030','Budget & Vendor Management',          'Course',       6,'Medium',sid['Budget Management'],     'Udemy',    'Management',      'Intermediate'),
    # Soft Skills
    ('LR-031','Communication & Presentation Skills', 'Workshop',     4,'High',  sid['Communication'],         'Internal', 'Problem Solving', 'Beginner'),
    ('LR-032','Critical Thinking & Problem Solving', 'Workshop',     4,'High',  sid['Problem Solving'],       'Internal', 'Problem Solving', 'Intermediate'),
    ('LR-033','Negotiation & Conflict Resolution',   'Workshop',     4,'Medium',sid['Negotiation'],           'Coursera', 'Problem Solving', 'Intermediate'),
    ('LR-034','Emotional Intelligence at Work',      'Course',       4,'Medium',sid['Emotional Intelligence'],'Coursera', 'Problem Solving', 'Intermediate'),
    # Domain
    ('LR-035','Digital Marketing Fundamentals',      'Course',       8,'High',  sid['Digital Marketing'],     'Google',   'Marketing',       'Beginner'),
    ('LR-036','SEO & Content Marketing',             'Course',       6,'Medium',sid['SEO'],                   'Udemy',    'Marketing',       'Intermediate'),
    ('LR-037','Financial Analysis Basics',           'Course',       6,'High',  sid['Financial Analysis'],    'edX',      'Finance',         'Beginner'),
    ('LR-038','Financial Modeling & Valuation',      'Course',      10,'Medium',sid['Financial Modeling'],    'Coursera', 'Finance',         'Advanced'),
    ('LR-039','HR Management Best Practices',        'Course',       8,'High',  sid['HR Management'],         'SHRM',     'HR',              'Beginner'),
    ('LR-040','Sales Mastery & CRM Tools',           'Course',      10,'High',  sid['Sales Techniques'],      'Udemy',    'Sales',           'Intermediate'),
]
learning_resources = pd.DataFrame(lr_data, columns=[
    'resource_id','title','type','duration_hours','priority',
    'target_skill_id','provider','category','skill_level'])
learning_resources.to_csv('/home/claude/learning_resources.csv', index=False)
print(f"✅ learning_resources.csv ({len(learning_resources)} resources)")

# ── 7. EMPLOYEES CORE ─────────────────────────────────────────
emp_ids = [f'EMP-{i:04d}' for i in range(1, N_EMPLOYEES+1)]
first_male   = ['Ahmed','Mohamed','Omar','Khaled','Youssef','Hassan','Mahmoud','Ali','Ibrahim',
                'Kareem','Tarek','Sameh','Amr','Hossam','Sherif','Adel','Ashraf','Essam',
                'Mostafa','Wael','Ramy','Hesham','Maged','Ayman','Samy','Hany','Walid','Magdy']
first_female = ['Sara','Fatma','Laila','Noura','Rania','Mona','Mariam','Salma','Aya','Nour',
                'Rana','Mai','Eman','Amal','Hala','Sahar','Heba','Dina','Nada','Yasmin',
                'Shaimaa','Reem','Ghada','Nihal','Samar','Marwa','Asmaa','Rasha','Manal']
last_names   = ['El-Masry','Abdel-Rahman','Hassan','Farouk','El-Sayed','Ibrahim','Mostafa',
                'Sherif','Magdy','Adel','Salem','Fathy','Nabil','Zaki','Kamal','Hafez',
                'Gaber','Mansour','Tawfik','Soliman','Ragab','Shalaby','Barakat','Helal',
                'Nasr','Rizk','Fouad','Shawky','El-Shafei','Radwan','Sabry','El-Banna']

genders = np.random.choice(['Male','Female'], N_EMPLOYEES, p=[0.68,0.32])
full_names = [f"{np.random.choice(first_male if g=='Male' else first_female)} {np.random.choice(last_names)}"
              for g in genders]

role_ids_pool = list(role_info.keys())
role_weights  = np.array([role_info[r][5] for r in role_ids_pool], dtype=float)
role_weights /= role_weights.sum()
job_role_ids  = np.random.choice(role_ids_pool, N_EMPLOYEES, p=role_weights)
dept_ids      = [role_info[r][1] for r in job_role_ids]

# Hire dates — staggered, skewed to grow over time, NO lone first employee
# Minimum 5 employees in first month to avoid unrealistic gaps
hire_dates = []
# First 5 hires in first 2 weeks
for i in range(5):
    hire_dates.append(FOUNDED + timedelta(days=random.randint(0, 14)))
# Rest spread across full period, beta-skewed toward later (company growing)
for _ in range(N_EMPLOYEES - 5):
    total_days = (HIRE_END - FOUNDED).days
    day_offset = int(np.random.beta(1.8, 1.0) * total_days)
    hire_dates.append(FOUNDED + timedelta(days=day_offset))
random.shuffle(hire_dates)  # shuffle so first 5 not always EMP-0001..5

# Status, end_date, tenure (formula-based: (ref_date - hire_date).days / 365)
statuses, end_dates, tenure_years = [], [], []
for hd in hire_dates:
    if random.random() < TURNOVER_RATE:
        status   = 'Inactive'
        max_days = max(90, (NOW - hd).days - 30)
        ed       = hd + timedelta(days=random.randint(90, max_days))
        if ed > NOW: ed = NOW - timedelta(days=random.randint(1,30))
        end_dates.append(ed)
        tenure = round((ed - hd).days / 365, 2)
    else:
        status = 'Active'
        end_dates.append(None)
        tenure = round((NOW - hd).days / 365, 2)
    statuses.append(status)
    tenure_years.append(tenure)

ages         = np.random.randint(22, 48, N_EMPLOYEES)
total_working = []
for i in range(N_EMPLOYEES):
    min_tw = max(int(tenure_years[i])+1, 1)
    max_tw = max(ages[i]-21, min_tw+1)
    total_working.append(np.random.randint(min_tw, max_tw+1))

salaries = []
for i in range(N_EMPLOYEES):
    smin, smax = role_info[job_role_ids[i]][3], role_info[job_role_ids[i]][4]
    base = np.random.randint(smin, smax)
    bump = int(tenure_years[i] * 350 + np.random.normal(0, 700))
    salaries.append(int(round(max(smin, min(smax+4000, base+bump)), -2)))

# work_life_balance moved to evaluations — NOT in employees
overtime  = np.random.choice(['Yes','No'], N_EMPLOYEES, p=[0.30,0.70])
leave_bal = np.random.randint(0, 22, N_EMPLOYEES)
yslp      = [np.random.randint(0, min(int(t),3)+1) for t in tenure_years]

commute      = np.clip(np.round(np.random.exponential(13, N_EMPLOYEES)+1,1), 1, 60)
commute_cats = ['Near' if c<=10 else ('Medium' if c<=25 else 'Far') for c in commute]

senior_idx = [i for i,r in enumerate(job_role_ids)
              if role_info[r][2] in ('Senior','Lead','Manager')]
manager_ids = []
for i in range(N_EMPLOYEES):
    if random.random() < 0.08 or not senior_idx:
        manager_ids.append(None)
    else:
        mgr = random.choice(senior_idx)
        manager_ids.append(emp_ids[mgr] if mgr != i else None)

phones = [f"{np.random.choice(['010','011','012','015'])}{random.randint(10000000,99999999)}"
          for _ in range(N_EMPLOYEES)]

employees = pd.DataFrame({
    'employee_id':                emp_ids,
    'full_name':                  full_names,
    'gender':                     genders,
    'age':                        ages,
    'hire_date':                  [d.strftime('%Y-%m-%d') for d in hire_dates],
    'department_id':              dept_ids,
    'job_role_id':                job_role_ids,
    'salary_egp':                 salaries,
    'manager_id':                 manager_ids,
    'commute_distance_km':        commute,
    'commute_category':           commute_cats,
    'status':                     statuses,
    'end_date':                   [ed.strftime('%Y-%m-%d') if ed else None for ed in end_dates],
    'tenure_years':               tenure_years,   # formula: (ref_date-hire_date).days/365
    'phone_number':               phones,
    'total_working_years':        total_working,
    'years_since_last_promotion': yslp,
    'overtime':                   overtime,
    'leave_balance':              leave_bal,
})
employees.to_csv('/home/claude/employees_core.csv', index=False)
print("✅ employees_core.csv")

# Expose key objects for other parts
import pickle
state = {
    'employees': employees, 'emp_ids': emp_ids, 'hire_dates': hire_dates,
    'end_dates': end_dates, 'tenure_years': tenure_years, 'statuses': statuses,
    'job_role_ids': job_role_ids, 'dept_ids': dept_ids, 'salaries': salaries,
    'overtime': overtime, 'commute': commute, 'ages': ages,
    'role_info': role_info, 'role_ids_pool': role_ids_pool,
    'skills_catalog': skills_catalog, 'sid': sid, 'sname': sname,
    'all_skill_ids': all_skill_ids, 'prereq_lookup': prereq_lookup,
    'job_role_requirements': job_role_requirements, 'req_by_role': req_by_role,
    'learning_resources': learning_resources, 'skill_chain_dag': skill_chain_dag,
    'N_EMPLOYEES': N_EMPLOYEES, 'NOW': NOW, 'FOUNDED': FOUNDED,
    'ATTEND_START': ATTEND_START, 'ATTEND_END': ATTEND_END,
}
with open('/home/claude/state.pkl','wb') as f:
    pickle.dump(state, f)
print("✅ state saved")


np.random.seed(43)
random.seed(43)

    S = pickle.load(f)

employees         = S['employees']
emp_ids           = S['emp_ids']
hire_dates        = S['hire_dates']
end_dates         = S['end_dates']
tenure_years      = S['tenure_years']
statuses          = S['statuses']
job_role_ids      = S['job_role_ids']
salaries          = S['salaries']
overtime          = S['overtime']
commute           = S['commute']
role_info         = S['role_info']
skills_catalog    = S['skills_catalog']
sid               = S['sid']
all_skill_ids     = S['all_skill_ids']
prereq_lookup     = S['prereq_lookup']
jrr               = S['job_role_requirements']
req_by_role       = S['req_by_role']
learning_resources= S['learning_resources']
N                 = S['N_EMPLOYEES']
NOW               = S['NOW']
ATTEND_START      = S['ATTEND_START']
ATTEND_END        = S['ATTEND_END']

def safe_end(val):
    if val and str(val) != 'nan':
        return datetime.strptime(str(val), '%Y-%m-%d')
    return NOW

# ── 1. EMPLOYEE SKILL MATRIX ──────────────────────────────────
print("Building skill matrix...")
role_fit_scores = {}
emp_skill_rows  = []

prof_ceiling = {'Junior':3,'Mid':4,'Senior':5,'Lead':5,'Manager':5}

for idx, emp in employees.iterrows():
    eid    = emp['employee_id']
    rid    = emp['job_role_id']
    level  = role_info[rid][2]
    tenure = emp['tenure_years']

    req_ids   = req_by_role.get(rid, [])
    skill_set = set(req_ids)

    level_extra = {'Junior':1,'Mid':3,'Senior':6,'Lead':8,'Manager':7}
    n_extra = level_extra.get(level,2) + int(tenure*0.8) + random.randint(0,2)
    others  = [s for s in all_skill_ids if s not in req_ids]
    if others and n_extra > 0:
        skill_set.update(np.random.choice(others,
            size=min(n_extra,len(others)), replace=False))

    # enforce prerequisites
    changed = True
    while changed:
        changed = False
        for sk in list(skill_set):
            for pre in prereq_lookup.get(sk, []):
                if pre not in skill_set:
                    skill_set.add(pre); changed = True

    ceiling    = prof_ceiling.get(level, 3)
    skill_prof = {}
    for sk in skill_set:
        complexity = int(skills_catalog.loc[
            skills_catalog['skill_id']==sk,'complexity_level'].values[0])
        base = (1.5 + tenure*0.4 + np.random.normal(0,.5)
                if sk in req_ids else 1.0 + tenure*0.3 + np.random.normal(0,.5))
        base -= (complexity-1)*0.2
        prof = int(np.clip(base, 1, ceiling))
        skill_prof[sk] = prof
        emp_skill_rows.append({
            'employee_id':         eid,
            'skill_id':            sk,
            'proficiency':         prof,
            'verification_status': np.random.choice(['Verified','Pending'],p=[.65,.35]),
        })

    # role-fit score (formula-based)
    reqs_df = jrr[jrr['job_role_id']==rid]
    total_w = met_w = 0.0
    for _, rrow in reqs_df.iterrows():
        w = rrow['importance_weight']; minp = rrow['min_proficiency']
        actual = skill_prof.get(rrow['required_skill_id'], 0)
        total_w += w
        met_w   += w if actual >= minp else (w*(actual/minp) if actual>0 else 0)
    role_fit_scores[eid] = round((met_w/total_w)*100,1) if total_w>0 else 0.0

emp_skill_matrix = pd.DataFrame(emp_skill_rows)
emp_skill_matrix.to_csv('/home/claude/employee_skill_matrix.csv', index=False)
print(f"✅ employee_skill_matrix.csv ({len(emp_skill_matrix):,} rows)")

employees['role_fit_score'] = employees['employee_id'].map(role_fit_scores)
employees.to_csv('/home/claude/employees_core.csv', index=False)

# ── 2. ATTENDANCE (with absence_reason + early_leave_minutes) ─
print("Generating attendance...")

working_days = []
cur = ATTEND_START
while cur <= ATTEND_END:
    if cur.weekday() not in (4,5):   # skip Fri/Sat
        working_days.append(cur)
    cur += timedelta(days=1)

# Absence reason weights per status bucket
# status -> list of (reason, weight)
absence_reasons_present = [('Work From Home',0.40),('Training / Official Duty',0.15),
                            ('Late Arrival',0.45)]
absence_reasons_absent  = [('Sick Leave',0.30),('Personal Leave',0.18),
                            ('Vacation / Annual Leave',0.24),('Emergency',0.06),
                            ('Unpaid Leave',0.06),('Other',0.16)]
absence_reasons_half    = [('Half Day',0.70),('Personal Leave',0.15),
                            ('Emergency',0.10),('Other',0.05)]

def pick_reason(pool):
    reasons, weights = zip(*pool)
    weights = np.array(weights); weights /= weights.sum()
    return np.random.choice(reasons, p=weights)

att_rows = []
for idx, emp in employees.iterrows():
    eid    = emp['employee_id']
    hd     = datetime.strptime(emp['hire_date'],'%Y-%m-%d')
    ed     = safe_end(emp['end_date'])
    km     = emp['commute_distance_km']
    ot     = emp['overtime']

    # Causal rates (no work_life_balance here — moved to evaluations)
    fit         = role_fit_scores.get(eid, 60) / 100
    absent_rate = np.clip(0.03 + (1-fit)*0.06 + np.random.normal(0,.01), 0.01, 0.15)
    late_rate   = np.clip(0.04 + km/160       + np.random.normal(0,.02), 0.01, 0.28)
    half_rate   = np.clip(0.02 + (1-fit)*0.04 + np.random.normal(0,.01), 0.01, 0.10)
    ot_mean     = 2.8 if ot=='Yes' else 0.4

    for day in working_days:
        if not (hd <= day <= ed):
            continue
        r = random.random()
        if r < absent_rate:
            att_rows.append({
                'employee_id': eid, 'date': day.strftime('%Y-%m-%d'),
                'status': 'Absent',
                'absence_reason': pick_reason(absence_reasons_absent),
                'check_in_time': None, 'check_out_time': None,
                'overtime_hours': 0.0, 'worked_hours': 0.0,
                'early_leave_minutes': 0,
            })
        elif r < absent_rate + half_rate:
            ci = day.replace(hour=9, minute=random.randint(0,20))
            co = day.replace(hour=13, minute=random.randint(0,30))
            wh = round((co-ci).seconds/3600, 2)
            early = max(0, (17*60) - (co.hour*60+co.minute))
            att_rows.append({
                'employee_id': eid, 'date': day.strftime('%Y-%m-%d'),
                'status': 'Half-Day',
                'absence_reason': pick_reason(absence_reasons_half),
                'check_in_time': ci.strftime('%H:%M'),
                'check_out_time': co.strftime('%H:%M'),
                'overtime_hours': 0.0, 'worked_hours': wh,
                'early_leave_minutes': early,
            })
        elif r < absent_rate + half_rate + late_rate:
            late_min = random.randint(11, 95)
            ci = day.replace(hour=9) + timedelta(minutes=late_min)
            ot_extra = max(0, round(np.random.exponential(ot_mean),1))
            co = day.replace(hour=17) + timedelta(hours=ot_extra)
            wh = round((co-ci).seconds/3600, 2)
            early = max(0, (17*60)-(co.hour*60+co.minute)) if co.hour < 17 else 0
            att_rows.append({
                'employee_id': eid, 'date': day.strftime('%Y-%m-%d'),
                'status': 'Late',
                'absence_reason': 'Late Arrival',
                'check_in_time': ci.strftime('%H:%M'),
                'check_out_time': co.strftime('%H:%M'),
                'overtime_hours': round(max(0,wh-8),2),
                'worked_hours': wh,
                'early_leave_minutes': early,
            })
        else:
            ci = day.replace(hour=9, minute=random.randint(0,8))
            ot_extra = max(0, round(np.random.exponential(ot_mean),1))
            co = day.replace(hour=17) + timedelta(hours=ot_extra)
            wh = round((co-ci).seconds/3600, 2)
            reason = pick_reason(absence_reasons_present) if ot_extra==0 else 'Work From Home'
            att_rows.append({
                'employee_id': eid, 'date': day.strftime('%Y-%m-%d'),
                'status': 'Present',
                'absence_reason': None,
                'check_in_time': ci.strftime('%H:%M'),
                'check_out_time': co.strftime('%H:%M'),
                'overtime_hours': round(max(0,wh-8),2),
                'worked_hours': wh,
                'early_leave_minutes': 0,
            })

attendance = pd.DataFrame(att_rows)
attendance.to_csv('/home/claude/attendance.csv', index=False)
print(f"✅ attendance.csv ({len(attendance):,} records)")

# Attendance summary (for ML features)
att_sum = attendance.groupby('employee_id').agg(
    total_working_days   =('date',           'count'),
    present_days         =('status',         lambda x:(x=='Present').sum()),
    absent_days          =('status',         lambda x:(x=='Absent').sum()),
    late_days            =('status',         lambda x:(x=='Late').sum()),
    half_day_count       =('status',         lambda x:(x=='Half-Day').sum()),
    total_overtime_hours =('overtime_hours', 'sum'),
    avg_worked_hours     =('worked_hours',   'mean'),
    total_early_leave_min=('early_leave_minutes','sum'),
).reset_index()
att_sum['absence_rate']     = (att_sum['absent_days']   /att_sum['total_working_days']).round(4)
att_sum['late_rate']        = (att_sum['late_days']     /att_sum['total_working_days']).round(4)
att_sum['half_day_rate']    = (att_sum['half_day_count']/att_sum['total_working_days']).round(4)
att_sum['attendance_score'] = (att_sum['present_days']  /att_sum['total_working_days']*100).round(2)
att_sum.to_csv('/home/claude/attendance_summary.csv', index=False)
print("✅ attendance_summary.csv")

# ── 3. EVALUATIONS (all formula-based, no random scores) ──────
print("Building evaluations...")

# We need: completed_tasks, project_count, KPI data
# Generate per-employee work metrics first (used in formulas)
np.random.seed(44)
work_metrics = {}
for idx, emp in employees.iterrows():
    eid    = emp['employee_id']
    rid    = emp['job_role_id']
    level  = role_info[rid][2]
    tenure = emp['tenure_years']
    fit    = role_fit_scores.get(eid, 60) / 100

    # Tasks / projects scale with level and tenure
    task_base     = {'Junior':8,'Mid':15,'Senior':25,'Lead':30,'Manager':20}
    proj_base     = {'Junior':1,'Mid':2, 'Senior':4, 'Lead':5, 'Manager':6}
    tasks_per_period  = max(1, int(task_base.get(level,10)*fit + np.random.normal(0,2)))
    projects_per_period = max(0, int(proj_base.get(level,2)*fit + np.random.normal(0,0.5)))
    task_complexity   = {'Junior':1.5,'Mid':2.5,'Senior':3.5,'Lead':4.0,'Manager':3.5}.get(level,2.0)
    kpi_score         = round(np.clip(50 + fit*35 + np.random.normal(0,5), 30, 100), 1)
    work_metrics[eid] = {
        'tasks_per_period':    tasks_per_period,
        'projects_per_period': projects_per_period,
        'task_complexity':     task_complexity,
        'kpi_score':           kpi_score,
    }

eval_periods = [
    ('2023-H1','2023-01-01','2023-06-30'),
    ('2023-H2','2023-07-01','2023-12-31'),
    ('2024-H1','2024-01-01','2024-06-30'),
    ('2024-H2','2024-07-01','2024-12-31'),
    ('2025-H1','2025-01-01','2025-06-30'),
    ('2025-H2','2025-07-01','2025-12-31'),
]

eval_rows = []
for idx, emp in employees.iterrows():
    eid    = emp['employee_id']
    hd     = datetime.strptime(emp['hire_date'],'%Y-%m-%d')
    ed     = safe_end(emp['end_date'])
    fit    = role_fit_scores.get(eid,60)/100
    ot_flag= 1 if emp['overtime']=='Yes' else 0
    wm     = work_metrics[eid]

    # Get attendance stats for this employee
    att_row = att_sum[att_sum['employee_id']==eid]
    absence_r = float(att_row['absence_rate'].values[0])   if len(att_row) else 0.05
    late_r    = float(att_row['late_rate'].values[0])      if len(att_row) else 0.05
    att_sc    = float(att_row['attendance_score'].values[0]) if len(att_row) else 85.0

    for period, p_start_str, p_end_str in eval_periods:
        p_start = datetime.strptime(p_start_str,'%Y-%m-%d')
        p_end   = datetime.strptime(p_end_str,  '%Y-%m-%d')
        if hd > p_end or ed < p_start + timedelta(days=60):
            continue

        # ── TECHNICAL SCORE (formula) ──────────────────────────
        # = 40*(tasks_done/max_tasks) + 30*(projects/max_proj) + 20*complexity_factor + 10*timeliness
        tasks_done      = max(1, int(wm['tasks_per_period'] * np.random.uniform(0.7,1.0)))
        max_tasks       = wm['tasks_per_period'] + 5
        proj_done       = max(0, int(wm['projects_per_period'] * np.random.uniform(0.6,1.0)))
        max_proj        = max(1, wm['projects_per_period'] + 1)
        complexity_f    = wm['task_complexity'] / 5.0
        timeliness      = np.clip(1.0 - absence_r*2 - late_r, 0.4, 1.0)
        technical_score = round(np.clip(
            40*(tasks_done/max_tasks) +
            30*(proj_done/max_proj)  +
            20*complexity_f          +
            10*timeliness, 20, 100), 1)

        # ── SOFT SKILLS SCORE (formula) ────────────────────────
        # = 35*kpi_norm + 25*ot_contrib + 25*att_discipline + 15*peer_proxy
        kpi_norm      = wm['kpi_score'] / 100
        ot_contrib    = np.clip(0.5 + ot_flag*0.5, 0.3, 1.0)
        att_discipline= np.clip(att_sc/100 - late_r*0.5, 0.3, 1.0)
        peer_proxy    = np.clip(fit + np.random.normal(0,0.05), 0.3, 1.0)
        soft_score    = round(np.clip(
            35*kpi_norm + 25*ot_contrib + 25*att_discipline + 15*peer_proxy,
            20, 100), 1)

        # ── WORK-LIFE BALANCE (moves here from attendance) ─────
        wlb = round(np.clip(
            5 - (ot_flag*1.5) - (absence_r*10) + np.random.normal(0,0.4),
            1, 5), 1)

        # ── OVERALL SCORE ──────────────────────────────────────
        # weighted: 55% technical + 35% soft + 10% attendance
        overall = round(np.clip(
            0.55*technical_score + 0.35*soft_score + 0.10*att_sc,
            20, 100), 1)

        # ── PRODUCTIVITY ───────────────────────────────────────
        productivity = round(np.clip(
            (tasks_done/max_tasks)*60 + complexity_f*25 + timeliness*15,
            20, 100), 1)

        # ── RATING ─────────────────────────────────────────────
        rating = ('Exceptional'          if overall >= 88 else
                  'Exceeds Expectations' if overall >= 74 else
                  'Meets Expectations'   if overall >= 58 else
                  'Needs Improvement')

        # ── BONUS ELIGIBILITY ──────────────────────────────────
        bonus_pct    = role_info[emp['job_role_id']][6]
        bonus_eligible = overall >= 65 and tasks_done >= max_tasks*0.7

        eval_rows.append({
            'evaluation_id':        f'EVAL-{eid}-{period}',
            'employee_id':          eid,
            'period':               period,
            'evaluation_date':      p_end_str,
            'tasks_completed':      tasks_done,
            'projects_completed':   proj_done,
            'task_complexity_avg':  wm['task_complexity'],
            'timeliness_score':     round(timeliness*100, 1),
            'kpi_score':            wm['kpi_score'],
            'overtime_contribution':ot_flag,
            'attendance_discipline':round(att_discipline*100, 1),
            'technical_score':      technical_score,
            'soft_skills_score':    soft_score,
            'work_life_balance':    wlb,
            'productivity_score':   productivity,
            'overall_score':        overall,
            'performance_rating':   rating,
            'bonus_eligible':       bonus_eligible,
            'bonus_pct_if_eligible':bonus_pct,
            'evaluated_by':         emp['manager_id'] if emp['manager_id'] else 'HR',
        })

evaluations = pd.DataFrame(eval_rows)
evaluations.to_csv('/home/claude/evaluations.csv', index=False)
print(f"✅ evaluations.csv ({len(evaluations):,} rows, all formula-based)")

# Latest eval per employee (for downstream use)
latest_eval = (evaluations.sort_values('evaluation_date')
               .groupby('employee_id').last().reset_index()
               [['employee_id','overall_score','performance_rating',
                 'work_life_balance','kpi_score']]
               .rename(columns={'overall_score':'latest_eval_score',
                                'performance_rating':'latest_rating'}))

# Persist state
    'emp_skill_matrix': emp_skill_matrix,
    'role_fit_scores':  role_fit_scores,
    'att_sum':          att_sum,
    'evaluations':      evaluations,
    'latest_eval':      latest_eval,
    'work_metrics':     work_metrics,
    'attendance':       attendance,
}
print("✅ state2 saved")


np.random.seed(45)
random.seed(45)

    S = pickle.load(f)
    S2 = pickle.load(f)

employees          = S['employees']
emp_ids            = S['emp_ids']
hire_dates         = S['hire_dates']
end_dates          = S['end_dates']
tenure_years       = S['tenure_years']
job_role_ids       = S['job_role_ids']
salaries           = S['salaries']
overtime           = S['overtime']
role_info          = S['role_info']
role_ids_pool      = S['role_ids_pool']
sid                = S['sid']
all_skill_ids      = S['all_skill_ids']
prereq_lookup      = S['prereq_lookup']
jrr                = S['job_role_requirements']
req_by_role        = S['req_by_role']
learning_resources = S['learning_resources']
skill_chain_dag    = S['skill_chain_dag']
skills_catalog     = S['skills_catalog']
NOW                = S['NOW']
FOUNDED            = S['FOUNDED']

emp_skill_matrix   = S2['emp_skill_matrix']
role_fit_scores    = S2['role_fit_scores']
att_sum            = S2['att_sum']
evaluations        = S2['evaluations']
latest_eval        = S2['latest_eval']
work_metrics       = S2['work_metrics']

def safe_end(val):
    if val and str(val) != 'nan':
        return datetime.strptime(str(val),'%Y-%m-%d')
    return NOW

# ── 1. TRAINING HISTORY (many-to-many: one training → 1+ skills)
print("Building training history...")

# Junction table: training_id → skill_id (many-to-many)
train_rows       = []
train_skill_rows = []   # many-to-many bridge
train_id_counter = 1

for idx, emp in employees.iterrows():
    eid    = emp['employee_id']
    hd     = datetime.strptime(emp['hire_date'],'%Y-%m-%d')
    ed     = safe_end(emp['end_date'])
    tenure = emp['tenure_years']
    level  = role_info[emp['job_role_id']][2]

    level_base = {'Junior':0.6,'Mid':1.2,'Senior':2.0,'Lead':2.5,'Manager':2.0}
    n_courses  = max(0, int(tenure * level_base.get(level,1.0)
                            + np.random.normal(0,0.8)))
    n_courses  = min(n_courses, 10)

    picked = np.random.choice(
        learning_resources['resource_id'].tolist(),
        size=min(n_courses, len(learning_resources)), replace=False)

    for attempt_num, lr_id in enumerate(picked, start=1):
        lr_row    = learning_resources[learning_resources['resource_id']==lr_id].iloc[0]
        span      = max(30,(ed-hd).days-30)
        comp_date = hd + timedelta(days=random.randint(30,span))
        score     = int(np.clip(
            50 + (role_fit_scores.get(eid,60)/100)*35 + np.random.normal(0,8),
            40, 100))
        duration  = int(lr_row['duration_hours'])

        # validated_by_manager: formula — score > 50 → Yes
        validated = 'Yes' if score > 50 else 'No'

        # feedback_score: formula — based on score and attendance discipline
        att_row  = att_sum[att_sum['employee_id']==eid]
        att_disc = float(att_row['attendance_score'].values[0]) if len(att_row) else 80.0
        feedback = round(np.clip((score*0.7 + att_disc*0.3)/20, 1.0, 5.0), 1)

        tid = f'TRN-{train_id_counter:05d}'
        train_id_counter += 1

        train_rows.append({
            'training_id':          tid,
            'employee_id':          eid,
            'resource_id':          lr_id,
            'resource_title':       lr_row['title'],
            'completion_date':      comp_date.strftime('%Y-%m-%d'),
            'completion_score':     score,
            'duration_hours':       duration,
            'feedback_score':       feedback,
            'attempt_number':       attempt_num,
            'status':               'Completed',
            'validated_by_manager': validated,   # score>50 → Yes
        })

        # Many-to-many: primary skill (always) + optional secondary skill
        primary_skill = lr_row['target_skill_id']
        train_skill_rows.append({
            'training_id': tid,
            'skill_id':    primary_skill,
            'is_primary':  True,
        })

        # ~35% chance a training also develops a prerequisite skill
        prereqs = prereq_lookup.get(primary_skill, [])
        if prereqs and random.random() < 0.35:
            secondary = random.choice(prereqs)
            train_skill_rows.append({
                'training_id': tid,
                'skill_id':    secondary,
                'is_primary':  False,
            })

training_history    = pd.DataFrame(train_rows)
training_skill_map  = pd.DataFrame(train_skill_rows)
training_history.to_csv('/home/claude/training_history.csv', index=False)
training_skill_map.to_csv('/home/claude/training_skill_map.csv', index=False)
print(f"✅ training_history.csv ({len(training_history)} records)")
print(f"✅ training_skill_map.csv ({len(training_skill_map)} rows — many-to-many)")

train_summary = (training_history.groupby('employee_id')
    .agg(courses_completed  =('training_id',       'count'),
         avg_training_score =('completion_score',  'mean'),
         avg_feedback_score =('feedback_score',    'mean'),
         last_training_date =('completion_date',   'max'))
    .reset_index())
train_summary['avg_training_score'] = train_summary['avg_training_score'].round(1)
train_summary['avg_feedback_score'] = train_summary['avg_feedback_score'].round(2)

# ── 2. MONTHLY PAYROLL (all formula-based) ────────────────────
print("Building payroll...")

payroll_rows = []
payroll_id   = 1

# Generate monthly payroll for every month each employee was active
for idx, emp in employees.iterrows():
    eid       = emp['employee_id']
    hd        = datetime.strptime(emp['hire_date'],'%Y-%m-%d')
    ed        = safe_end(emp['end_date'])
    base_sal  = emp['salary_egp']
    rid       = emp['job_role_id']
    bonus_pct = role_info[rid][6] / 100.0
    level     = role_info[rid][2]

    # Get eval score for bonus eligibility
    ev_row    = latest_eval[latest_eval['employee_id']==eid]
    eval_sc   = float(ev_row['latest_eval_score'].values[0]) if len(ev_row) else 60.0
    bonus_eligible = eval_sc >= 65

    # Overtime rate: 1.5× hourly
    hourly_rate = base_sal / 176.0  # ~22 working days × 8 hrs

    # Iterate months
    cur_month = datetime(hd.year, hd.month, 1)
    end_month = datetime(ed.year, ed.month, 1)

    while cur_month <= end_month and cur_month <= NOW:
        month_str = cur_month.strftime('%Y-%m')

        # Get attendance for this month
        att_month = att_sum[att_sum['employee_id']==eid]
        # Use yearly totals prorated to monthly (~12 months avg)
        total_ot_hrs = float(att_month['total_overtime_hours'].values[0]) if len(att_month) else 0
        monthly_ot   = round(total_ot_hrs / max(1, int(emp['tenure_years']*12)), 2)

        # Deductions: late penalties + unpaid leave
        late_days_total = float(att_month['late_days'].values[0]) if len(att_month) else 0
        late_monthly    = late_days_total / max(1, int(emp['tenure_years']*12))
        late_penalty    = round(late_monthly * hourly_rate * 0.5, 2)   # 30 min pay per late

        absent_total    = float(att_month['absent_days'].values[0]) if len(att_month) else 0
        absent_monthly  = absent_total / max(1, int(emp['tenure_years']*12))
        unpaid_ded      = round(absent_monthly * (base_sal/22), 2)     # daily rate × absent days
        total_deductions= round(late_penalty + unpaid_ded, 2)

        # Overtime pay
        overtime_pay = round(monthly_ot * hourly_rate * 1.5, 2)

        # Bonus: paid in H2 months (July, December) if eligible
        bonus_month  = cur_month.month in (7, 12)
        bonus_amount = round((base_sal * bonus_pct) / 2, 2) if (bonus_eligible and bonus_month) else 0.0

        # Total salary
        total_salary = round(base_sal + bonus_amount + overtime_pay - total_deductions, 2)
        total_salary = max(base_sal * 0.7, total_salary)  # floor at 70% of base

        payroll_rows.append({
            'payroll_id':    f'PAY-{payroll_id:06d}',
            'employee_id':   eid,
            'month':         month_str,
            'base_salary':   base_sal,
            'bonus_amount':  bonus_amount,
            'overtime_hours':monthly_ot,
            'overtime_pay':  overtime_pay,
            'late_penalty':  late_penalty,
            'unpaid_leave_deduction': unpaid_ded,
            'total_deductions': total_deductions,
            # total = base + bonus + overtime_pay - deductions
            'total_salary':  total_salary,
        })
        payroll_id += 1
        # Next month
        if cur_month.month == 12:
            cur_month = datetime(cur_month.year+1, 1, 1)
        else:
            cur_month = datetime(cur_month.year, cur_month.month+1, 1)

monthly_payroll = pd.DataFrame(payroll_rows)
monthly_payroll.to_csv('/home/claude/monthly_payroll.csv', index=False)
print(f"✅ monthly_payroll.csv ({len(monthly_payroll):,} rows, all formula-based)")

# ── 3. LEAVE REQUESTS ─────────────────────────────────────────
print("Building leave requests...")
leave_rows = []
leave_types  = ['Annual Leave','Sick Leave','Compassionate Leave','Unpaid Leave']
leave_probs  = [0.55, 0.28, 0.10, 0.07]
leave_status = ['Approved','Approved','Approved','Rejected','Pending']

for idx, emp in employees.iterrows():
    eid    = emp['employee_id']
    hd     = datetime.strptime(emp['hire_date'],'%Y-%m-%d')
    ed     = safe_end(emp['end_date'])
    tenure = emp['tenure_years']
    n_leaves = max(1, int(tenure*2.2 + np.random.normal(0,0.8)))
    for _ in range(min(n_leaves,14)):
        span  = max(7,(ed-hd).days-7)
        start = hd + timedelta(days=random.randint(7,span))
        ltype = np.random.choice(leave_types, p=leave_probs)
        days  = {'Annual Leave':random.randint(1,10),
                 'Sick Leave':random.randint(1,5),
                 'Compassionate Leave':random.randint(1,3),
                 'Unpaid Leave':random.randint(1,5)}[ltype]
        leave_rows.append({
            'request_id':    f'LV-{len(leave_rows)+1:05d}',
            'employee_id':   eid,
            'leave_type':    ltype,
            'start_date':    start.strftime('%Y-%m-%d'),
            'end_date':      (start+timedelta(days=days)).strftime('%Y-%m-%d'),
            'days_requested':days,
            'status':        random.choice(leave_status),
            'submitted_date':(start-timedelta(days=random.randint(1,12))).strftime('%Y-%m-%d'),
            'approved_by':   emp['manager_id'] if emp['manager_id'] else 'HR',
        })

leave_requests = pd.DataFrame(leave_rows)
leave_requests.to_csv('/home/claude/leave_requests.csv', index=False)
print(f"✅ leave_requests.csv ({len(leave_requests)} rows)")

# ── 4. MOBILITY HISTORY (restructured) ────────────────────────
print("Building mobility history...")
mob_rows = []

change_types = ['Promotion','Lateral Transfer','Demotion',
                'Role Change','Level Upgrade','Salary Adjustment','Restructure Move']
change_probs = [0.30, 0.25, 0.05, 0.15, 0.10, 0.10, 0.05]

for _ in range(160):
    emp_row  = employees.sample(1).iloc[0]
    eid      = emp_row['employee_id']
    curr_rid = emp_row['job_role_id']
    new_rid  = random.choice([r for r in role_ids_pool if r!=curr_rid])

    old_dept = role_info[curr_rid][1]
    new_dept = role_info[new_rid][1]
    old_sal  = emp_row['salary_egp']
    new_sal  = int(np.clip(old_sal + np.random.normal(2000,1500),
                           role_info[new_rid][3], role_info[new_rid][4]+5000))

    # manager before/after
    mgr_pool = [e for e in emp_ids if e != eid]
    mgr_before = emp_row['manager_id'] if emp_row['manager_id'] else random.choice(mgr_pool)
    mgr_after  = random.choice(mgr_pool)

    # change_type based on salary and level direction
    old_lvl_rank = {'Junior':1,'Mid':2,'Senior':3,'Lead':4,'Manager':5}
    old_rank = old_lvl_rank.get(role_info[curr_rid][2], 2)
    new_rank = old_lvl_rank.get(role_info[new_rid][2],  2)
    if new_rank > old_rank:
        change_type = 'Promotion'
    elif new_rank < old_rank:
        change_type = 'Demotion'
    else:
        change_type = np.random.choice(
            ['Lateral Transfer','Role Change','Level Upgrade',
             'Salary Adjustment','Restructure Move'],
            p=[0.35,0.25,0.15,0.15,0.10])

    # success_score: formula — post-move performance proxy
    # based on role-fit at new role + salary improvement
    fit_new = role_fit_scores.get(eid, 60) / 100
    sal_imp = np.clip((new_sal-old_sal)/old_sal, -0.2, 0.3)
    ev_row  = latest_eval[latest_eval['employee_id']==eid]
    ev_sc   = float(ev_row['latest_eval_score'].values[0]) if len(ev_row) else 60.0
    success = round(np.clip(fit_new*3 + sal_imp*5 + (ev_sc/100)*2, 1, 5), 1)

    trans_date = (FOUNDED + timedelta(days=random.randint(90,1095))).strftime('%Y-%m-%d')

    mob_rows.append({
        'mobility_id':      f'MOB-{len(mob_rows)+1:04d}',
        'employee_id':      eid,
        'previous_role_id': curr_rid,
        'new_role_id':      new_rid,
        'old_department':   old_dept,
        'new_department':   new_dept,
        'salary_before':    old_sal,
        'salary_after':     new_sal,
        'manager_id_before':mgr_before,
        'manager_id_after': mgr_after,
        'change_type':      change_type,
        'transition_date':  trans_date,
        # success_score = formula: fit*3 + salary_improvement*5 + eval_score*2
        'success_score':    success,
    })

mobility_history = pd.DataFrame(mob_rows)
mobility_history.to_csv('/home/claude/mobility_history.csv', index=False)
print(f"✅ mobility_history.csv ({len(mobility_history)} rows)")

# ── 5. SKILL GAP DATASET (formula-based, not random) ──────────
print("Building skill gap dataset...")
gap_rows = []
for _, emp in employees.iterrows():
    eid = emp['employee_id']
    rid = emp['job_role_id']
    emp_skills_map = {
        r['skill_id']: r['proficiency']
        for _, r in emp_skill_matrix[emp_skill_matrix['employee_id']==eid].iterrows()
    }
    reqs = jrr[jrr['job_role_id']==rid]
    for _, req in reqs.iterrows():
        s_id   = req['required_skill_id']
        minp   = req['min_proficiency']
        actual = emp_skills_map.get(s_id, 0)
        gap    = max(0, minp - actual)

        # recommended resource: best match by skill + level
        lr_match = learning_resources[learning_resources['target_skill_id']==s_id]
        if len(lr_match):
            # pick beginner resource for gap>1, intermediate for gap=1
            level_pref = 'Beginner' if gap > 1 else 'Intermediate'
            level_match = lr_match[lr_match['skill_level']==level_pref]
            rec_id = level_match.iloc[0]['resource_id'] if len(level_match) else lr_match.iloc[0]['resource_id']
        else:
            rec_id = None

        # priority_score: formula = gap × importance_weight × complexity
        complexity = int(skills_catalog.loc[
            skills_catalog['skill_id']==s_id,'complexity_level'].values[0])
        priority_score = round(gap * req['importance_weight'] * complexity, 3)

        gap_rows.append({
            'employee_id':             eid,
            'job_role_id':             rid,
            'skill_id':                s_id,
            'required_proficiency':    minp,
            'current_proficiency':     actual,
            'gap':                     gap,
            'gap_severity':            ('None'   if gap==0 else
                                        'Low'    if gap==1 else
                                        'Medium' if gap==2 else 'High'),
            'importance_weight':       req['importance_weight'],
            'priority_score':          priority_score,  # formula-based
            'recommended_resource_id': rec_id,
        })

skill_gap_dataset = pd.DataFrame(gap_rows)
skill_gap_dataset.to_csv('/home/claude/skill_gap_dataset.csv', index=False)
print(f"✅ skill_gap_dataset.csv ({len(skill_gap_dataset):,} rows, formula-based)")

# ── 6. REPLACEMENT ML DATASET ─────────────────────────────────
print("Building replacement ML dataset...")
rep_rows = []
active_emps = employees[employees['status']=='Active']

for _, emp in active_emps.iterrows():
    eid      = emp['employee_id']
    curr_rid = emp['job_role_id']
    emp_sk   = {r['skill_id']:r['proficiency']
                for _,r in emp_skill_matrix[emp_skill_matrix['employee_id']==eid].iterrows()}
    ev_row   = latest_eval[latest_eval['employee_id']==eid]
    ev_sc    = float(ev_row['latest_eval_score'].values[0]) if len(ev_row) else 55.0
    tr_row   = train_summary[train_summary['employee_id']==eid]
    tr_cnt   = int(tr_row['courses_completed'].values[0]) if len(tr_row) else 0

    for target_rid in role_ids_pool:
        if target_rid == curr_rid: continue
        reqs = jrr[jrr['job_role_id']==target_rid]
        if reqs.empty: continue

        total_gap=0.0; met=0; total_w=0.0
        for _,req in reqs.iterrows():
            s_id=req['required_skill_id']; minp=req['min_proficiency']; w=req['importance_weight']
            actual=emp_sk.get(s_id,0)
            total_gap += max(0,minp-actual)*w; total_w+=w
            if actual>=minp: met+=1

        weighted_gap    = round(total_gap/total_w if total_w else 0,3)
        skill_match_pct = round(met/len(reqs)*100,1)

        prereqs_needed = set()
        for s_id in reqs['required_skill_id']:
            prereqs_needed.update(prereq_lookup.get(s_id,[]))
        prereq_met      = sum(1 for p in prereqs_needed if p in emp_sk)
        chain_readiness = round(prereq_met/len(prereqs_needed)*100 if prereqs_needed else 100,1)

        same_dept       = role_info[curr_rid][1]==role_info[target_rid][1]
        suitability     = 1 if (skill_match_pct>=55 and weighted_gap<1.8) else 0

        rep_rows.append({
            'employee_id':        eid,'current_role_id':curr_rid,'target_role_id':target_rid,
            'weighted_skill_gap': weighted_gap,'skill_match_pct':skill_match_pct,
            'chain_readiness':    chain_readiness,'role_similarity':1.0 if same_dept else 0.5,
            'tenure_years':       emp['tenure_years'],'total_working_years':emp['total_working_years'],
            'latest_eval_score':  ev_sc,'courses_completed':tr_cnt,
            'role_fit_score':     role_fit_scores.get(eid,60),
            'suitability_label':  suitability,
        })

replacement_ml = pd.DataFrame(rep_rows)
replacement_ml.to_csv('/home/claude/replacement_ml_dataset.csv', index=False)
print(f"✅ replacement_ml_dataset.csv  shape={replacement_ml.shape}")

# ── 7. TURNOVER ML DATASET (status label only — no pre-scores) ─
print("Building turnover ML dataset...")
ml = employees[['employee_id','job_role_id','department_id','gender','age',
                'tenure_years','total_working_years','years_since_last_promotion',
                'salary_egp','overtime','leave_balance',
                'commute_distance_km','commute_category','status']].copy()

ml = ml.merge(att_sum[['employee_id','absence_rate','late_rate','half_day_rate',
                        'total_overtime_hours','attendance_score','avg_worked_hours',
                        'total_early_leave_min']], on='employee_id', how='left')
ml = ml.merge(train_summary[['employee_id','courses_completed',
                              'avg_training_score','avg_feedback_score']],
              on='employee_id', how='left')
ml = ml.merge(latest_eval[['employee_id','latest_eval_score','kpi_score',
                            'work_life_balance']], on='employee_id', how='left')

ml['role_fit_score']       = ml['employee_id'].map(role_fit_scores).fillna(60)
ml['courses_completed']    = ml['courses_completed'].fillna(0).astype(int)
ml['avg_training_score']   = ml['avg_training_score'].fillna(0)
ml['latest_eval_score']    = ml['latest_eval_score'].fillna(55)
ml['kpi_score']            = ml['kpi_score'].fillna(50)
ml['work_life_balance']    = ml['work_life_balance'].fillna(3)
ml['commute_category_enc'] = ml['commute_category'].map({'Near':0,'Medium':1,'Far':2})
ml['overtime_enc']         = (ml['overtime']=='Yes').astype(int)
ml['gender_enc']           = (ml['gender']=='Male').astype(int)

# turnover_label = status only (no pre-generated risk scores)
ml['turnover_label'] = (ml['status']=='Inactive').astype(int)

final_cols = [
    'employee_id','job_role_id','department_id','gender_enc','age',
    'tenure_years','total_working_years','years_since_last_promotion',
    'salary_egp','overtime_enc','leave_balance',
    'commute_distance_km','commute_category_enc',
    'absence_rate','late_rate','half_day_rate','total_early_leave_min',
    'total_overtime_hours','attendance_score','avg_worked_hours',
    'courses_completed','avg_training_score','avg_feedback_score',
    'latest_eval_score','kpi_score','work_life_balance','role_fit_score',
    'turnover_label',
]
turnover_ml = ml[final_cols].copy()
turnover_ml.to_csv('/home/claude/turnover_ml_dataset.csv', index=False)
print(f"✅ turnover_ml_dataset.csv  shape={turnover_ml.shape}  "
      f"turnover_rate={turnover_ml['turnover_label'].mean()*100:.1f}%")

# ── FINAL SUMMARY ─────────────────────────────────────────────
tables = {
    'departments.csv':            'departments',
    'skills_catalog.csv':         'skills_catalog',
    'skill_chain_dag.csv':        'skill_chain_dag',
    'job_roles.csv':              'job_roles',
    'job_role_requirements.csv':  'job_role_requirements',
    'employees_core.csv':         'employees_core',
    'employee_skill_matrix.csv':  'employee_skill_matrix',
    'learning_resources.csv':     'learning_resources',
    'attendance.csv':             'attendance',
    'attendance_summary.csv':     'att_sum',
    'training_history.csv':       'training_history',
    'training_skill_map.csv':     'training_skill_map',
    'evaluations.csv':            'evaluations',
    'monthly_payroll.csv':        'monthly_payroll',
    'leave_requests.csv':         'leave_requests',
    'mobility_history.csv':       'mobility_history',
    'skill_gap_dataset.csv':      'skill_gap_dataset',
    'replacement_ml_dataset.csv': 'replacement_ml',
    'turnover_ml_dataset.csv':    'turnover_ml',
}
dfs = {
    'departments': None, 'skills_catalog': None, 'skill_chain_dag': None,
    'job_roles': None, 'job_role_requirements': None,
}

print("\n" + "="*60)
print("  ALL TABLES GENERATED")
print("="*60)
for fname in tables:
    try:
        df = pd.read_csv(f'/home/claude/{fname}')
        print(f"  {fname:<42} {len(df):>8,} rows")
    except:
        print(f"  {fname:<42}   (not found)")

from pandas import read_csv as rc
sc = rc('/home/claude/skills_catalog.csv')
dag= rc('/home/claude/skill_chain_dag.csv')
emp= rc('/home/claude/employees_core.csv')
print(f"\n  Skills in catalog        : {len(sc)}")
print(f"  Skills with complexity=5 : {(sc['complexity_level']==5).sum()}")
print(f"  DAG edges                : {len(dag)}")
print(f"  Active employees         : {(emp['status']=='Active').sum()}")
print(f"  Inactive employees       : {(emp['status']=='Inactive').sum()}")
print(f"  Turnover rate            : {(emp['status']=='Inactive').mean()*100:.1f}%")
print(f"  Avg role fit score       : {emp['role_fit_score'].mean():.1f}%")
