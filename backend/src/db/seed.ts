// src/db/seed.ts — Seeds all 50 employees, 28 skills, 22 roles, holidays, demo users
import 'dotenv/config';
import bcrypt from 'bcryptjs';
import { db, connectDB, closeDB } from './index';
import {
  users, userRoles, employees, employeeSkills,
  skills, relatedSkills, skillChains, jobRoles, roleRequiredSkills,
  leaveBalances, attendance, payroll, todos, notifications, holidays,
} from './schema';
import { logger } from '../config/logger';

// ── 1. Skills (28) ────────────────────────────────────────────────────────────
const SKILLS = [
  { id: 'sk01', name: 'Python',             category: 'technical'  as const, description: 'Python programming language' },
  { id: 'sk02', name: 'Machine Learning',   category: 'technical'  as const, description: 'ML algorithms and model training' },
  { id: 'sk03', name: 'Deep Learning',      category: 'technical'  as const, description: 'Neural networks and deep learning' },
  { id: 'sk04', name: 'SQL',                category: 'technical'  as const, description: 'Relational database querying' },
  { id: 'sk05', name: 'Data Analysis',      category: 'technical'  as const, description: 'Statistical analysis and data insights' },
  { id: 'sk06', name: 'JavaScript',         category: 'technical'  as const, description: 'Web frontend programming' },
  { id: 'sk07', name: 'React',              category: 'technical'  as const, description: 'React frontend framework' },
  { id: 'sk08', name: 'Node.js',            category: 'technical'  as const, description: 'Server-side JavaScript runtime' },
  { id: 'sk09', name: 'Flutter',            category: 'technical'  as const, description: 'Cross-platform mobile development' },
  { id: 'sk10', name: 'Dart',               category: 'technical'  as const, description: 'Dart programming language' },
  { id: 'sk11', name: 'DevOps',             category: 'technical'  as const, description: 'CI/CD and infrastructure automation' },
  { id: 'sk12', name: 'Docker',             category: 'technical'  as const, description: 'Containerization with Docker' },
  { id: 'sk13', name: 'Kubernetes',         category: 'technical'  as const, description: 'Container orchestration' },
  { id: 'sk14', name: 'Cloud AWS',          category: 'technical'  as const, description: 'Amazon Web Services cloud platform' },
  { id: 'sk15', name: 'Project Management', category: 'management' as const, description: 'Planning and managing projects' },
  { id: 'sk16', name: 'Agile/Scrum',        category: 'management' as const, description: 'Agile methodologies and Scrum' },
  { id: 'sk17', name: 'Leadership',         category: 'management' as const, description: 'Team leadership and mentoring' },
  { id: 'sk18', name: 'Communication',      category: 'soft'       as const, description: 'Verbal and written communication' },
  { id: 'sk19', name: 'Teamwork',           category: 'soft'       as const, description: 'Collaboration and team contribution' },
  { id: 'sk20', name: 'Problem Solving',    category: 'soft'       as const, description: 'Analytical thinking and solution design' },
  { id: 'sk21', name: 'Critical Thinking',  category: 'soft'       as const, description: 'Logical reasoning and evaluation' },
  { id: 'sk22', name: 'HR Management',      category: 'domain'     as const, description: 'Human resources processes and policies' },
  { id: 'sk23', name: 'Recruitment',        category: 'domain'     as const, description: 'Talent acquisition and hiring' },
  { id: 'sk24', name: 'Finance',            category: 'domain'     as const, description: 'Financial analysis and reporting' },
  { id: 'sk25', name: 'Accounting',         category: 'domain'     as const, description: 'Bookkeeping and financial records' },
  { id: 'sk26', name: 'Marketing',          category: 'domain'     as const, description: 'Digital and traditional marketing' },
  { id: 'sk27', name: 'UI/UX Design',       category: 'technical'  as const, description: 'User interface and experience design' },
  { id: 'sk28', name: 'Cybersecurity',      category: 'technical'  as const, description: 'Security practices and threat mitigation' },
];

const RELATED_SKILLS = [
  ['sk01','sk02'],['sk01','sk05'],['sk02','sk01'],['sk02','sk03'],['sk04','sk05'],
  ['sk06','sk07'],['sk06','sk08'],['sk07','sk06'],['sk08','sk06'],['sk09','sk10'],
  ['sk10','sk09'],['sk11','sk12'],['sk12','sk11'],['sk12','sk13'],['sk13','sk12'],
  ['sk14','sk11'],['sk15','sk16'],['sk16','sk15'],['sk17','sk15'],['sk18','sk19'],
  ['sk19','sk18'],['sk20','sk21'],['sk21','sk20'],['sk22','sk23'],['sk24','sk25'],
  ['sk26','sk27'],['sk27','sk06'],['sk28','sk14'],
];

const SKILL_CHAINS = [
  { from: 'sk01', to: 'sk02', desc: 'Python is the foundation for ML' },
  { from: 'sk02', to: 'sk03', desc: 'ML knowledge enables Deep Learning' },
  { from: 'sk04', to: 'sk05', desc: 'SQL skills support data analysis' },
  { from: 'sk06', to: 'sk07', desc: 'JavaScript is prerequisite for React' },
  { from: 'sk06', to: 'sk08', desc: 'JavaScript enables Node.js development' },
  { from: 'sk09', to: 'sk10', desc: 'Dart is core language for Flutter' },
  { from: 'sk12', to: 'sk13', desc: 'Docker is required before Kubernetes' },
  { from: 'sk11', to: 'sk14', desc: 'DevOps skills complement Cloud AWS' },
  { from: 'sk15', to: 'sk17', desc: 'Project management develops leadership' },
];

// ── 2. Job Roles (22) ─────────────────────────────────────────────────────────
const JOB_ROLES = [
  { id:'r01', title:'Junior Software Engineer',  dept:'Engineering',     level:'junior'  as const, req:[['sk06',2],['sk08',2],['sk19',2]] },
  { id:'r02', title:'Software Engineer',         dept:'Engineering',     level:'mid'     as const, req:[['sk06',3],['sk08',3],['sk04',2],['sk20',3]] },
  { id:'r03', title:'Senior Software Engineer',  dept:'Engineering',     level:'senior'  as const, req:[['sk06',4],['sk08',4],['sk12',3],['sk16',3],['sk20',4]] },
  { id:'r04', title:'Frontend Developer',        dept:'Engineering',     level:'mid'     as const, req:[['sk06',4],['sk07',4],['sk27',3]] },
  { id:'r05', title:'Backend Developer',         dept:'Engineering',     level:'mid'     as const, req:[['sk08',4],['sk04',3],['sk12',2]] },
  { id:'r06', title:'Data Scientist',            dept:'Data',            level:'mid'     as const, req:[['sk01',4],['sk02',4],['sk05',4],['sk04',3]] },
  { id:'r07', title:'Senior Data Scientist',     dept:'Data',            level:'senior'  as const, req:[['sk01',5],['sk02',5],['sk03',4],['sk05',4]] },
  { id:'r08', title:'DevOps Engineer',           dept:'Engineering',     level:'mid'     as const, req:[['sk11',4],['sk12',4],['sk13',3],['sk14',3]] },
  { id:'r09', title:'Mobile Developer',          dept:'Engineering',     level:'mid'     as const, req:[['sk09',4],['sk10',4],['sk20',2]] },
  { id:'r10', title:'Engineering Manager',       dept:'Engineering',     level:'manager' as const, req:[['sk15',4],['sk17',4],['sk16',4],['sk18',4]] },
  { id:'r11', title:'HR Specialist',             dept:'Human Resources', level:'mid'     as const, req:[['sk22',3],['sk23',3],['sk18',3]] },
  { id:'r12', title:'HR Manager',                dept:'Human Resources', level:'manager' as const, req:[['sk22',5],['sk17',4],['sk15',4]] },
  { id:'r13', title:'Financial Analyst',         dept:'Finance',         level:'mid'     as const, req:[['sk24',4],['sk25',3],['sk05',3]] },
  { id:'r14', title:'Marketing Specialist',      dept:'Marketing',       level:'mid'     as const, req:[['sk26',4],['sk18',3],['sk05',2]] },
  { id:'r15', title:'UI/UX Designer',            dept:'Design',          level:'mid'     as const, req:[['sk27',4],['sk18',3],['sk21',3]] },
  { id:'r16', title:'Tech Lead',                 dept:'Engineering',     level:'lead'    as const, req:[['sk06',5],['sk16',4],['sk17',4],['sk20',5]] },
  { id:'r17', title:'Data Analyst',              dept:'Data',            level:'junior'  as const, req:[['sk04',3],['sk05',3],['sk01',2]] },
  { id:'r18', title:'Cybersecurity Analyst',     dept:'IT Security',     level:'mid'     as const, req:[['sk28',4],['sk11',3],['sk14',3]] },
  { id:'r19', title:'Product Manager',           dept:'Product',         level:'senior'  as const, req:[['sk15',5],['sk16',4],['sk18',5],['sk21',4]] },
  { id:'r20', title:'Scrum Master',              dept:'Engineering',     level:'mid'     as const, req:[['sk16',5],['sk18',4],['sk19',4]] },
  { id:'r21', title:'Senior DevOps Engineer',    dept:'Engineering',     level:'senior'  as const, req:[['sk11',5],['sk12',5],['sk13',4],['sk14',4]] },
  { id:'r22', title:'Junior Data Analyst',       dept:'Data',            level:'junior'  as const, req:[['sk04',2],['sk05',2]] },
];

// ── 3. Employees (50) ─────────────────────────────────────────────────────────
type EmpDef = {
  id: string; name: string; email: string; role: string;
  roleId: string; dept: string; join: string; sal: number;
  phone: string; commute: 'near'|'moderate'|'far'|'very_far'; sat: number;
  skills: [string, number, string][];
};

const EMPLOYEES: EmpDef[] = [
  {id:'emp01',name:'Ahmed Hassan',      email:'ahmed.hassan@skillsync.dev',      role:'Software Engineer',          roleId:'r02',dept:'Engineering',     join:'2021-03-15',sal:18000,phone:'+20 100 123 4567',commute:'moderate',sat:72,skills:[['sk06',4,'2024-01-01'],['sk08',4,'2024-02-01'],['sk04',3,'2024-03-01'],['sk20',3,'2024-04-01'],['sk19',3,'2024-01-01']]},
  {id:'emp02',name:'Nour El-Sayed',     email:'nour.sayed@skillsync.dev',         role:'Data Scientist',             roleId:'r06',dept:'Data',            join:'2022-06-01',sal:22000,phone:'+20 101 234 5678',commute:'near',   sat:85,skills:[['sk01',5,'2024-01-01'],['sk02',4,'2024-02-01'],['sk05',4,'2024-03-01'],['sk04',3,'2024-04-01'],['sk21',4,'2024-05-01']]},
  {id:'emp03',name:'Omar Khalil',       email:'omar.khalil@skillsync.dev',        role:'DevOps Engineer',            roleId:'r08',dept:'Engineering',     join:'2020-01-10',sal:20000,phone:'+20 102 345 6789',commute:'far',    sat:60,skills:[['sk11',4,'2024-01-01'],['sk12',5,'2024-02-01'],['sk13',3,'2024-03-01'],['sk14',4,'2024-04-01']]},
  {id:'emp04',name:'Mariam Ibrahim',    email:'mariam.ibrahim@skillsync.dev',     role:'HR Specialist',              roleId:'r11',dept:'Human Resources', join:'2023-02-20',sal:12000,phone:'+20 103 456 7890',commute:'near',   sat:78,skills:[['sk22',3,'2024-01-01'],['sk23',3,'2024-02-01'],['sk18',4,'2024-03-01'],['sk19',3,'2024-04-01']]},
  {id:'emp05',name:'Karim Mostafa',     email:'karim.mostafa@skillsync.dev',      role:'Frontend Developer',         roleId:'r04',dept:'Engineering',     join:'2022-09-05',sal:16000,phone:'+20 104 567 8901',commute:'moderate',sat:80,skills:[['sk06',4,'2024-01-01'],['sk07',4,'2024-02-01'],['sk27',3,'2024-03-01'],['sk19',3,'2024-04-01']]},
  {id:'emp06',name:'Fatima Zahra',      email:'fatima.zahra@skillsync.dev',       role:'Senior Software Engineer',   roleId:'r03',dept:'Engineering',     join:'2019-07-01',sal:26000,phone:'+20 105 678 9012',commute:'near',   sat:91,skills:[['sk06',5,'2024-01-01'],['sk08',5,'2024-02-01'],['sk12',4,'2024-03-01'],['sk16',4,'2024-04-01'],['sk20',5,'2024-05-01']]},
  {id:'emp07',name:'Youssef Nabil',     email:'youssef.nabil@skillsync.dev',      role:'Mobile Developer',           roleId:'r09',dept:'Engineering',     join:'2023-01-15',sal:17000,phone:'+20 106 789 0123',commute:'very_far',sat:55,skills:[['sk09',4,'2024-01-01'],['sk10',4,'2024-02-01'],['sk20',3,'2024-03-01']]},
  {id:'emp08',name:'Layla Ahmed',       email:'layla.ahmed@skillsync.dev',        role:'Financial Analyst',          roleId:'r13',dept:'Finance',         join:'2021-11-08',sal:15000,phone:'+20 107 890 1234',commute:'moderate',sat:75,skills:[['sk24',4,'2024-01-01'],['sk25',3,'2024-02-01'],['sk05',3,'2024-03-01'],['sk21',3,'2024-04-01']]},
  {id:'emp09',name:'Hassan Ramzy',      email:'hassan.ramzy@skillsync.dev',       role:'Marketing Specialist',       roleId:'r14',dept:'Marketing',       join:'2024-03-01',sal:13000,phone:'+20 108 901 2345',commute:'near',   sat:68,skills:[['sk26',4,'2024-01-01'],['sk18',3,'2024-02-01'],['sk05',2,'2024-03-01']]},
  {id:'emp10',name:'Dina Fathy',        email:'dina.fathy@skillsync.dev',         role:'UI/UX Designer',             roleId:'r15',dept:'Design',          join:'2022-04-18',sal:15000,phone:'+20 109 012 3456',commute:'far',    sat:82,skills:[['sk27',4,'2024-01-01'],['sk18',4,'2024-02-01'],['sk21',3,'2024-03-01'],['sk06',2,'2024-04-01']]},
  {id:'emp11',name:'Tarek Mansour',     email:'tarek.mansour@skillsync.dev',      role:'Engineering Manager',        roleId:'r10',dept:'Engineering',     join:'2017-05-20',sal:35000,phone:'+20 110 123 4567',commute:'moderate',sat:88,skills:[['sk15',5,'2024-01-01'],['sk17',5,'2024-02-01'],['sk16',4,'2024-03-01'],['sk18',5,'2024-04-01'],['sk20',4,'2024-05-01']]},
  {id:'emp12',name:'Sara Mahmoud',      email:'sara.mahmoud@skillsync.dev',       role:'Senior Data Scientist',      roleId:'r07',dept:'Data',            join:'2020-08-12',sal:28000,phone:'+20 111 234 5678',commute:'near',   sat:90,skills:[['sk01',5,'2024-01-01'],['sk02',5,'2024-02-01'],['sk03',4,'2024-03-01'],['sk05',5,'2024-04-01'],['sk04',4,'2024-05-01']]},
  {id:'emp13',name:'Ali Samir',         email:'ali.samir@skillsync.dev',          role:'Backend Developer',          roleId:'r05',dept:'Engineering',     join:'2022-12-01',sal:16500,phone:'+20 112 345 6789',commute:'very_far',sat:62,skills:[['sk08',4,'2024-01-01'],['sk04',3,'2024-02-01'],['sk12',2,'2024-03-01']]},
  {id:'emp14',name:'Rana Essam',        email:'rana.essam@skillsync.dev',         role:'HR Manager',                 roleId:'r12',dept:'Human Resources', join:'2018-02-14',sal:30000,phone:'+20 113 456 7890',commute:'near',   sat:86,skills:[['sk22',5,'2024-01-01'],['sk17',4,'2024-02-01'],['sk15',4,'2024-03-01'],['sk18',4,'2024-04-01']]},
  {id:'emp15',name:'Khaled Gamal',      email:'khaled.gamal@skillsync.dev',       role:'Tech Lead',                  roleId:'r16',dept:'Engineering',     join:'2016-09-25',sal:40000,phone:'+20 114 567 8901',commute:'moderate',sat:93,skills:[['sk06',5,'2024-01-01'],['sk16',5,'2024-02-01'],['sk17',4,'2024-03-01'],['sk20',5,'2024-04-01'],['sk12',4,'2024-05-01']]},
  {id:'emp16',name:'Mona Sherif',       email:'mona.sherif@skillsync.dev',        role:'Data Analyst',               roleId:'r17',dept:'Data',            join:'2023-05-10',sal:11000,phone:'+20 115 678 9012',commute:'far',    sat:70,skills:[['sk04',3,'2024-01-01'],['sk05',3,'2024-02-01'],['sk01',2,'2024-03-01']]},
  {id:'emp17',name:'Islam Hany',        email:'islam.hany@skillsync.dev',         role:'Cybersecurity Analyst',      roleId:'r18',dept:'IT Security',     join:'2021-07-06',sal:21000,phone:'+20 116 789 0123',commute:'near',   sat:77,skills:[['sk28',4,'2024-01-01'],['sk11',3,'2024-02-01'],['sk14',3,'2024-03-01']]},
  {id:'emp18',name:'Heba Zaki',         email:'heba.zaki@skillsync.dev',          role:'Product Manager',            roleId:'r19',dept:'Product',         join:'2019-11-03',sal:34000,phone:'+20 117 890 1234',commute:'moderate',sat:89,skills:[['sk15',5,'2024-01-01'],['sk16',4,'2024-02-01'],['sk18',5,'2024-03-01'],['sk21',4,'2024-04-01']]},
  {id:'emp19',name:'Mahmoud Saber',     email:'mahmoud.saber@skillsync.dev',      role:'Scrum Master',               roleId:'r20',dept:'Engineering',     join:'2020-03-18',sal:22000,phone:'+20 118 901 2345',commute:'near',   sat:84,skills:[['sk16',5,'2024-01-01'],['sk18',4,'2024-02-01'],['sk19',4,'2024-03-01'],['sk15',3,'2024-04-01']]},
  {id:'emp20',name:'Noha Fouad',        email:'noha.fouad@skillsync.dev',         role:'Junior Software Engineer',   roleId:'r01',dept:'Engineering',     join:'2024-01-08',sal:10000,phone:'+20 119 012 3456',commute:'very_far',sat:58,skills:[['sk06',2,'2024-01-01'],['sk08',2,'2024-02-01'],['sk19',2,'2024-03-01']]},
  {id:'emp21',name:'Amr Wagih',         email:'amr.wagih@skillsync.dev',          role:'Senior DevOps Engineer',     roleId:'r21',dept:'Engineering',     join:'2018-08-22',sal:32000,phone:'+20 120 123 4567',commute:'far',    sat:74,skills:[['sk11',5,'2024-01-01'],['sk12',5,'2024-02-01'],['sk13',4,'2024-03-01'],['sk14',4,'2024-04-01']]},
  {id:'emp22',name:'Yasmine Adel',      email:'yasmine.adel@skillsync.dev',       role:'UI/UX Designer',             roleId:'r15',dept:'Design',          join:'2022-02-10',sal:14000,phone:'+20 121 234 5678',commute:'near',   sat:81,skills:[['sk27',5,'2024-01-01'],['sk18',3,'2024-02-01'],['sk21',4,'2024-03-01']]},
  {id:'emp23',name:'Hazem Nasser',      email:'hazem.nasser@skillsync.dev',       role:'Data Analyst',               roleId:'r17',dept:'Data',            join:'2023-09-14',sal:11500,phone:'+20 122 345 6789',commute:'moderate',sat:66,skills:[['sk04',3,'2024-01-01'],['sk05',2,'2024-02-01'],['sk01',2,'2024-03-01']]},
  {id:'emp24',name:'Asmaa Lotfy',       email:'asmaa.lotfy@skillsync.dev',        role:'HR Specialist',              roleId:'r11',dept:'Human Resources', join:'2021-04-29',sal:13000,phone:'+20 123 456 7890',commute:'near',   sat:79,skills:[['sk22',4,'2024-01-01'],['sk23',4,'2024-02-01'],['sk18',3,'2024-03-01']]},
  {id:'emp25',name:'Sherif Badawi',     email:'sherif.badawi@skillsync.dev',      role:'Software Engineer',          roleId:'r02',dept:'Engineering',     join:'2021-06-07',sal:17000,phone:'+20 124 567 8901',commute:'far',    sat:71,skills:[['sk06',3,'2024-01-01'],['sk08',3,'2024-02-01'],['sk04',2,'2024-03-01'],['sk20',3,'2024-04-01']]},
  {id:'emp26',name:'Rania Helmy',       email:'rania.helmy@skillsync.dev',        role:'Marketing Specialist',       roleId:'r14',dept:'Marketing',       join:'2022-07-19',sal:13500,phone:'+20 125 678 9012',commute:'near',   sat:73,skills:[['sk26',3,'2024-01-01'],['sk18',4,'2024-02-01'],['sk05',2,'2024-03-01']]},
  {id:'emp27',name:'Basem Taha',        email:'basem.taha@skillsync.dev',         role:'Backend Developer',          roleId:'r05',dept:'Engineering',     join:'2020-10-11',sal:17000,phone:'+20 126 789 0123',commute:'moderate',sat:76,skills:[['sk08',4,'2024-01-01'],['sk04',3,'2024-02-01'],['sk12',3,'2024-03-01'],['sk14',2,'2024-04-01']]},
  {id:'emp28',name:'Doaa Magdy',        email:'doaa.magdy@skillsync.dev',         role:'Junior Data Analyst',        roleId:'r22',dept:'Data',            join:'2024-02-05',sal:9000, phone:'+20 127 890 1234',commute:'very_far',sat:54,skills:[['sk04',2,'2024-01-01'],['sk05',2,'2024-02-01']]},
  {id:'emp29',name:'Wael Kamal',        email:'wael.kamal@skillsync.dev',         role:'Senior Software Engineer',   roleId:'r03',dept:'Engineering',     join:'2018-12-04',sal:27000,phone:'+20 128 901 2345',commute:'near',   sat:87,skills:[['sk06',5,'2024-01-01'],['sk08',4,'2024-02-01'],['sk12',4,'2024-03-01'],['sk16',3,'2024-04-01'],['sk20',4,'2024-05-01']]},
  {id:'emp30',name:'Amira Salah',       email:'amira.salah@skillsync.dev',        role:'Financial Analyst',          roleId:'r13',dept:'Finance',         join:'2022-03-16',sal:15500,phone:'+20 129 012 3456',commute:'moderate',sat:83,skills:[['sk24',4,'2024-01-01'],['sk25',4,'2024-02-01'],['sk05',3,'2024-03-01']]},
  {id:'emp31',name:'Mostafa Zidan',     email:'mostafa.zidan@skillsync.dev',      role:'Mobile Developer',           roleId:'r09',dept:'Engineering',     join:'2023-08-21',sal:16000,phone:'+20 130 123 4567',commute:'far',    sat:67,skills:[['sk09',3,'2024-01-01'],['sk10',3,'2024-02-01'],['sk06',2,'2024-03-01']]},
  {id:'emp32',name:'Nada Ragab',        email:'nada.ragab@skillsync.dev',         role:'Frontend Developer',         roleId:'r04',dept:'Engineering',     join:'2021-09-30',sal:15500,phone:'+20 131 234 5678',commute:'near',   sat:79,skills:[['sk06',4,'2024-01-01'],['sk07',3,'2024-02-01'],['sk27',4,'2024-03-01']]},
  {id:'emp33',name:'Tamer Ghazi',       email:'tamer.ghazi@skillsync.dev',        role:'Cybersecurity Analyst',      roleId:'r18',dept:'IT Security',     join:'2020-05-15',sal:22000,phone:'+20 132 345 6789',commute:'very_far',sat:61,skills:[['sk28',5,'2024-01-01'],['sk11',4,'2024-02-01'],['sk14',4,'2024-03-01'],['sk12',3,'2024-04-01']]},
  {id:'emp34',name:'Samar Refai',       email:'samar.refai@skillsync.dev',        role:'HR Specialist',              roleId:'r11',dept:'Human Resources', join:'2022-11-27',sal:12500,phone:'+20 133 456 7890',commute:'moderate',sat:74,skills:[['sk22',3,'2024-01-01'],['sk23',3,'2024-02-01'],['sk18',3,'2024-03-01']]},
  {id:'emp35',name:'Adel Korany',       email:'adel.korany@skillsync.dev',        role:'Data Scientist',             roleId:'r06',dept:'Data',            join:'2023-03-08',sal:20000,phone:'+20 134 567 8901',commute:'near',   sat:82,skills:[['sk01',4,'2024-01-01'],['sk02',4,'2024-02-01'],['sk05',3,'2024-03-01'],['sk04',3,'2024-04-01']]},
  {id:'emp36',name:'Ghada Barakat',     email:'ghada.barakat@skillsync.dev',      role:'Product Manager',            roleId:'r19',dept:'Product',         join:'2020-06-23',sal:33000,phone:'+20 135 678 9012',commute:'near',   sat:88,skills:[['sk15',5,'2024-01-01'],['sk16',4,'2024-02-01'],['sk18',4,'2024-03-01'],['sk21',5,'2024-04-01']]},
  {id:'emp37',name:'Fady Samaan',       email:'fady.samaan@skillsync.dev',        role:'Junior Software Engineer',   roleId:'r01',dept:'Engineering',     join:'2024-04-01',sal:10000,phone:'+20 136 789 0123',commute:'far',    sat:64,skills:[['sk06',2,'2024-01-01'],['sk08',1,'2024-02-01'],['sk19',2,'2024-03-01']]},
  {id:'emp38',name:'Eman Ashraf',       email:'eman.ashraf@skillsync.dev',        role:'Scrum Master',               roleId:'r20',dept:'Engineering',     join:'2021-01-20',sal:21000,phone:'+20 137 890 1234',commute:'moderate',sat:80,skills:[['sk16',4,'2024-01-01'],['sk18',4,'2024-02-01'],['sk19',4,'2024-03-01']]},
  {id:'emp39',name:'Ihab Desoky',       email:'ihab.desoky@skillsync.dev',        role:'DevOps Engineer',            roleId:'r08',dept:'Engineering',     join:'2022-08-14',sal:19000,phone:'+20 138 901 2345',commute:'very_far',sat:59,skills:[['sk11',3,'2024-01-01'],['sk12',4,'2024-02-01'],['sk13',2,'2024-03-01'],['sk14',3,'2024-04-01']]},
  {id:'emp40',name:'Lobna Hassan',      email:'lobna.hassan@skillsync.dev',       role:'Marketing Specialist',       roleId:'r14',dept:'Marketing',       join:'2023-06-05',sal:12000,phone:'+20 139 012 3456',commute:'near',   sat:69,skills:[['sk26',3,'2024-01-01'],['sk18',3,'2024-02-01'],['sk05',2,'2024-03-01']]},
  {id:'emp41',name:'Salma Mohsen',      email:'salma.mohsen@skillsync.dev',       role:'Senior Software Engineer',   roleId:'r03',dept:'Engineering',     join:'2019-04-08',sal:25000,phone:'+20 140 123 4567',commute:'near',   sat:91,skills:[['sk06',5,'2024-01-01'],['sk08',5,'2024-02-01'],['sk12',3,'2024-03-01'],['sk16',4,'2024-04-01'],['sk20',4,'2024-05-01']]},
  {id:'emp42',name:'Sameh Abdo',        email:'sameh.abdo@skillsync.dev',         role:'Data Analyst',               roleId:'r17',dept:'Data',            join:'2022-10-17',sal:11000,phone:'+20 141 234 5678',commute:'moderate',sat:72,skills:[['sk04',3,'2024-01-01'],['sk05',3,'2024-02-01'],['sk01',2,'2024-03-01']]},
  {id:'emp43',name:'Amany Gaber',       email:'amany.gaber@skillsync.dev',        role:'Financial Analyst',          roleId:'r13',dept:'Finance',         join:'2020-12-09',sal:16000,phone:'+20 142 345 6789',commute:'far',    sat:76,skills:[['sk24',4,'2024-01-01'],['sk25',3,'2024-02-01'],['sk05',4,'2024-03-01'],['sk21',3,'2024-04-01']]},
  {id:'emp44',name:'Walid Abdou',       email:'walid.abdou@skillsync.dev',        role:'Tech Lead',                  roleId:'r16',dept:'Engineering',     join:'2017-02-28',sal:38000,phone:'+20 143 456 7890',commute:'near',   sat:92,skills:[['sk06',5,'2024-01-01'],['sk16',5,'2024-02-01'],['sk17',5,'2024-03-01'],['sk20',5,'2024-04-01'],['sk12',4,'2024-05-01']]},
  {id:'emp45',name:'Reham Zakaria',     email:'reham.zakaria@skillsync.dev',      role:'UI/UX Designer',             roleId:'r15',dept:'Design',          join:'2023-07-24',sal:13000,phone:'+20 144 567 8901',commute:'very_far',sat:56,skills:[['sk27',3,'2024-01-01'],['sk18',3,'2024-02-01'],['sk21',2,'2024-03-01']]},
  {id:'emp46',name:'Hesham Selim',      email:'hesham.selim@skillsync.dev',       role:'Backend Developer',          roleId:'r05',dept:'Engineering',     join:'2021-05-13',sal:16000,phone:'+20 145 678 9012',commute:'moderate',sat:78,skills:[['sk08',3,'2024-01-01'],['sk04',3,'2024-02-01'],['sk12',2,'2024-03-01'],['sk01',2,'2024-04-01']]},
  {id:'emp47',name:'Maha Rizk',         email:'maha.rizk@skillsync.dev',          role:'Senior Data Scientist',      roleId:'r07',dept:'Data',            join:'2019-03-06',sal:29000,phone:'+20 146 789 0123',commute:'near',   sat:90,skills:[['sk01',5,'2024-01-01'],['sk02',5,'2024-02-01'],['sk03',4,'2024-03-01'],['sk05',5,'2024-04-01'],['sk04',3,'2024-05-01']]},
  {id:'emp48',name:'Nabil Hosny',       email:'nabil.hosny@skillsync.dev',        role:'Software Engineer',          roleId:'r02',dept:'Engineering',     join:'2022-05-30',sal:17500,phone:'+20 147 890 1234',commute:'far',    sat:65,skills:[['sk06',3,'2024-01-01'],['sk08',3,'2024-02-01'],['sk04',2,'2024-03-01'],['sk20',2,'2024-04-01']]},
  {id:'emp49',name:'Hind Kamal',        email:'hind.kamal@skillsync.dev',         role:'HR Specialist',              roleId:'r11',dept:'Human Resources', join:'2024-01-22',sal:11500,phone:'+20 148 901 2345',commute:'near',   sat:73,skills:[['sk22',2,'2024-01-01'],['sk23',2,'2024-02-01'],['sk18',3,'2024-03-01']]},
  {id:'emp50',name:'Zaher Samy',        email:'zaher.samy@skillsync.dev',         role:'Junior Software Engineer',   roleId:'r01',dept:'Engineering',     join:'2024-03-11',sal:10000,phone:'+20 149 012 3456',commute:'very_far',sat:50,skills:[['sk06',1,'2024-01-01'],['sk08',1,'2024-02-01'],['sk19',1,'2024-03-01']]},
];

// Demo users matching Flutter login_form.dart credentials
const DEMO_USERS = [
  { email: 'ahmed.hassan@skillsync.dev',  password: 'Employee@123', role: 'employee'  as const },
  { email: 'tarek.mansour@skillsync.dev', password: 'Manager@123',  role: 'manager'   as const },
  { email: 'rana.essam@skillsync.dev',    password: 'Admin@123',    role: 'hr_admin'  as const },
];

// Egyptian public holidays 2024-2025
const HOLIDAYS = [
  { name: 'New Year\'s Day',         date: '2025-01-01', type: 'public'  as const },
  { name: 'Coptic Christmas',        date: '2025-01-07', type: 'public'  as const },
  { name: 'Revolution Day',          date: '2025-01-25', type: 'public'  as const },
  { name: 'Sinai Liberation Day',    date: '2025-04-25', type: 'public'  as const },
  { name: 'Labour Day',              date: '2025-05-01', type: 'public'  as const },
  { name: 'Revolution Day (July)',   date: '2025-07-23', type: 'public'  as const },
  { name: 'Armed Forces Day',        date: '2025-10-06', type: 'public'  as const },
  { name: 'Company Foundation Day',  date: '2025-03-15', type: 'company' as const },
];

// ── Main seed function ─────────────────────────────────────────────────────────
async function seed() {
  await connectDB();
  logger.info('🌱 Starting database seed...');

  // 1. Skills
  logger.info('Seeding skills...');
  for (const s of SKILLS) {
    await db.insert(skills).values(s).onConflictDoNothing();
  }

  // 2. Related skills
  for (const [from, to] of RELATED_SKILLS) {
    await db.insert(relatedSkills).values({ fromSkillId: from, toSkillId: to }).onConflictDoNothing();
  }

  // 3. Skill chains
  for (const c of SKILL_CHAINS) {
    await db.insert(skillChains).values({ fromSkillId: c.from, toSkillId: c.to, description: c.desc }).onConflictDoNothing();
  }
  logger.info(`✅  ${SKILLS.length} skills + chains seeded`);

  // 4. Job Roles
  logger.info('Seeding job roles...');
  for (const r of JOB_ROLES) {
    await db.insert(jobRoles).values({ id: r.id, title: r.title, department: r.dept, level: r.level, description: '' }).onConflictDoNothing();
    for (const [skillId, minProf] of r.req) {
      await db.insert(roleRequiredSkills).values({ roleId: r.id, skillId: skillId as string, minProficiency: minProf as number }).onConflictDoNothing();
    }
  }
  logger.info(`✅  ${JOB_ROLES.length} roles seeded`);

  // 5. Employees
  logger.info('Seeding employees...');
  for (const e of EMPLOYEES) {
    await db.insert(employees).values({
      id: e.id, name: e.name, email: e.email, currentRole: e.role,
      roleId: e.roleId, department: e.dept, joinDate: e.join,
      salary: e.sal, phone: e.phone, commuteDistance: e.commute,
      satisfactionScore: e.sat, avatarUrl: '',
    }).onConflictDoNothing();

    for (const [skillId, proficiency, lastAssessed] of e.skills) {
      await db.insert(employeeSkills).values({
        employeeId: e.id, skillId: skillId as string,
        proficiency: proficiency as number, lastAssessed: lastAssessed as string,
      }).onConflictDoNothing();
    }
  }
  logger.info(`✅  ${EMPLOYEES.length} employees seeded`);

  // 6. Demo user accounts
  logger.info('Seeding demo users...');
  for (const du of DEMO_USERS) {
    const userId        = crypto.randomUUID();
    const passwordHash  = await bcrypt.hash(du.password, 12);
    await db.insert(users).values({ id: userId, email: du.email, passwordHash }).onConflictDoNothing();
    await db.insert(userRoles).values({ userId, role: du.role }).onConflictDoNothing();

    // Link to employee
    const empRow = EMPLOYEES.find((e) => e.email === du.email);
    if (empRow) {
      await db.update(employees).set({ userId }).where(
        // Use raw SQL for conditional update without drizzle eq import complexity
        (await import('drizzle-orm')).eq(employees.id, empRow.id),
      );
    }
  }
  logger.info('✅  Demo users seeded (Employee@123, Manager@123, Admin@123)');

  // 7. Leave balances for all employees (current year)
  logger.info('Seeding leave balances...');
  const year = new Date().getFullYear();
  for (const e of EMPLOYEES) {
    await db.insert(leaveBalances).values([
      { employeeId: e.id, leaveType: 'annual',        totalDays: 21, usedDays: 0, year },
      { employeeId: e.id, leaveType: 'sick',           totalDays: 10, usedDays: 0, year },
      { employeeId: e.id, leaveType: 'compassionate',  totalDays: 5,  usedDays: 0, year },
    ]).onConflictDoNothing();
  }
  logger.info('✅  Leave balances seeded');

  // 8. Holidays
  logger.info('Seeding holidays...');
  for (const h of HOLIDAYS) {
    await db.insert(holidays).values({ id: crypto.randomUUID(), ...h }).onConflictDoNothing();
  }
  logger.info(`✅  ${HOLIDAYS.length} holidays seeded`);

  logger.info('🎉  Seed complete!');
  await closeDB();
}

seed().catch((err) => {
  logger.error('Seed failed', { error: (err as Error).message });
  process.exit(1);
});
