// lib/data/mock/mock_learning_items.dart
import '../../domain/entities/learning_item.dart';

final mockLearningItems = <LearningItem>[
  // ── Python / Data Science ─────────────────────────────────────────────────────
  const LearningItem(
    id: 'li01', title: 'Python for Data Science & AI', skillId: 'SK001',
    type: LearningType.course, duration: '40 hours', estimatedHours: 40, priority: 1,
    description: 'Comprehensive Python for data science and ML workflows using pandas, numpy and scikit-learn.',
    url: 'https://www.coursera.org/learn/python-for-applied-data-science-ai',
    platform: 'Coursera',
  ),
  const LearningItem(
    id: 'li_a01', title: 'Python Data Science Handbook', skillId: 'SK001',
    type: LearningType.article, duration: '12 min read', estimatedHours: 0, priority: 2,
    description: 'Free online handbook covering NumPy, Pandas, Matplotlib, and Scikit-Learn by Jake VanderPlas.',
    url: 'https://jakevdp.github.io/PythonDataScienceHandbook/',
    platform: 'Jake VanderPlas',
  ),

  // ── Machine Learning ──────────────────────────────────────────────────────────
  const LearningItem(
    id: 'li02', title: 'Machine Learning Specialization', skillId: 'SK025',
    type: LearningType.course, duration: '60 hours', estimatedHours: 60, priority: 1,
    description: 'Core ML algorithms, supervised & unsupervised learning, and model evaluation by Andrew Ng.',
    url: 'https://www.coursera.org/specializations/machine-learning-introduction',
    platform: 'Coursera',
  ),
  const LearningItem(
    id: 'li_a02', title: 'Machine Learning Glossary & Cheat Sheet', skillId: 'SK025',
    type: LearningType.article, duration: '8 min read', estimatedHours: 0, priority: 2,
    description: 'Quick reference for key ML concepts, algorithms, and terminology for practitioners.',
    url: 'https://ml-cheatsheet.readthedocs.io/en/latest/',
    platform: 'ml-cheatsheet.io',
  ),

  // ── Deep Learning ─────────────────────────────────────────────────────────────
  const LearningItem(
    id: 'li03', title: 'Deep Learning Specialization', skillId: 'SK026',
    type: LearningType.certification, duration: '120 hours', estimatedHours: 120, priority: 2,
    description: 'Neural networks, CNNs, RNNs, LSTMs and transformers by deeplearning.ai.',
    url: 'https://www.coursera.org/specializations/deep-learning',
    platform: 'Coursera',
  ),

  // ── SQL ───────────────────────────────────────────────────────────────────────
  const LearningItem(
    id: 'li04', title: 'SQL for Data Analysis', skillId: 'SK021',
    type: LearningType.course, duration: '20 hours', estimatedHours: 20, priority: 2,
    description: 'Advanced SQL queries, window functions, CTEs, and performance tuning for analysts.',
    url: 'https://www.datacamp.com/courses/sql-for-data-analysis-in-postgresql',
    platform: 'DataCamp',
  ),
  const LearningItem(
    id: 'li19', title: 'Advanced SQL & Performance Tuning', skillId: 'SK021',
    type: LearningType.course, duration: '15 hours', estimatedHours: 15, priority: 2,
    description: 'Query plans, indexes, partitioning and database optimization strategies.',
    url: 'https://www.datacamp.com/courses/database-design',
    platform: 'DataCamp',
  ),
  const LearningItem(
    id: 'li_a03', title: 'Use The Index, Luke — SQL Indexing Guide', skillId: 'SK021',
    type: LearningType.article, duration: '15 min read', estimatedHours: 0, priority: 3,
    description: 'Developer-focused guide explaining how SQL indexes work and how to design them for speed.',
    url: 'https://use-the-index-luke.com/',
    platform: 'use-the-index-luke.com',
  ),

  // ── React / Frontend ──────────────────────────────────────────────────────────
  const LearningItem(
    id: 'li05', title: 'React Basics Certification', skillId: 'SK012',
    type: LearningType.certification, duration: '50 hours', estimatedHours: 50, priority: 1,
    description: 'React hooks, state management, context, and performance optimisation.',
    url: 'https://www.coursera.org/learn/react-basics',
    platform: 'Coursera',
  ),

  // ── JavaScript ────────────────────────────────────────────────────────────────
  const LearningItem(
    id: 'li16', title: 'Advanced JavaScript Concepts', skillId: 'SK002',
    type: LearningType.course, duration: '25 hours', estimatedHours: 25, priority: 1,
    description: 'Closures, prototypes, async/await, design patterns, and the V8 engine internals.',
    url: 'https://javascript.info/',
    platform: 'javascript.info',
  ),
  const LearningItem(
    id: 'li17', title: 'TypeScript: The Complete Developer\'s Guide', skillId: 'SK003',
    type: LearningType.course, duration: '20 hours', estimatedHours: 20, priority: 1,
    description: 'TypeScript generics, decorators, advanced type system, and integration with React.',
    url: 'https://www.typescriptlang.org/docs/',
    platform: 'TypeScript Docs',
  ),
  const LearningItem(
    id: 'li_a04', title: 'JavaScript: The Definitive Guide (MDN)', skillId: 'SK002',
    type: LearningType.article, duration: '10 min read', estimatedHours: 0, priority: 2,
    description: 'Mozilla\'s comprehensive JavaScript reference — closures, prototypes, async, and more.',
    url: 'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide',
    platform: 'MDN Web Docs',
  ),
  const LearningItem(
    id: 'li25', title: 'Git Advanced Workflows', skillId: 'SK036',
    type: LearningType.course, duration: '8 hours', estimatedHours: 8, priority: 3,
    description: 'Branching strategies, rebasing, cherry-pick, monorepos, and conflict resolution.',
    url: 'https://www.atlassian.com/git/tutorials/comparing-workflows',
    platform: 'Atlassian',
  ),

  // ── Node.js / Backend ─────────────────────────────────────────────────────────
  const LearningItem(
    id: 'li06', title: 'Complete Node.js Developer Course', skillId: 'SK016',
    type: LearningType.course, duration: '35 hours', estimatedHours: 35, priority: 1,
    description: 'REST APIs, authentication, database integration, testing and deployment with Node.js.',
    url: 'https://nodejs.org/en/learn/getting-started/introduction-to-nodejs',
    platform: 'Node.js Docs',
  ),
  const LearningItem(
    id: 'li18', title: 'Node.js Microservices Architecture', skillId: 'SK016',
    type: LearningType.course, duration: '30 hours', estimatedHours: 30, priority: 1,
    description: 'Design, build and deploy microservices with Node.js, RabbitMQ and Docker.',
    url: 'https://microservices.io/patterns/microservices.html',
    platform: 'microservices.io',
  ),
  const LearningItem(
    id: 'li24', title: 'REST API Design Best Practices', skillId: 'SK016',
    type: LearningType.course, duration: '12 hours', estimatedHours: 12, priority: 2,
    description: 'Versioning, pagination, error handling, OpenAPI docs, and security patterns.',
    url: 'https://restfulapi.net/',
    platform: 'restfulapi.net',
  ),
  const LearningItem(
    id: 'li_a05', title: 'Node.js Best Practices Guide', skillId: 'SK016',
    type: LearningType.article, duration: '10 min read', estimatedHours: 0, priority: 2,
    description: 'Community-maintained guide of 80+ Node.js best practices for production apps.',
    url: 'https://github.com/goldbergyoni/nodebestpractices',
    platform: 'GitHub (goldbergyoni)',
  ),

  // ── Django / Backend Framework ────────────────────────────────────────────────
  const LearningItem(
    id: 'li26', title: 'Django REST Framework Mastery', skillId: 'SK017',
    type: LearningType.course, duration: '28 hours', estimatedHours: 28, priority: 1,
    description: 'Build production-ready REST APIs with Django, DRF, JWT authentication and PostgreSQL.',
    url: 'https://www.django-rest-framework.org/',
    platform: 'Django REST Framework',
  ),
  const LearningItem(
    id: 'li27', title: 'Django for Beginners to Advanced', skillId: 'SK017',
    type: LearningType.course, duration: '22 hours', estimatedHours: 22, priority: 2,
    description: 'Full Django web framework course covering models, views, templates, ORM, and deployment.',
    url: 'https://docs.djangoproject.com/en/stable/intro/tutorial01/',
    platform: 'Django Docs',
  ),

  // ── Java ──────────────────────────────────────────────────────────────────────
  const LearningItem(
    id: 'li28', title: 'Java Programming Masterclass', skillId: 'SK004',
    type: LearningType.course, duration: '45 hours', estimatedHours: 45, priority: 1,
    description: 'Core Java OOP, Collections, Streams, Concurrency, and Spring Boot fundamentals.',
    url: 'https://dev.java/learn/',
    platform: 'dev.java',
  ),
  const LearningItem(
    id: 'li29', title: 'Spring Boot in Practice', skillId: 'SK004',
    type: LearningType.course, duration: '30 hours', estimatedHours: 30, priority: 2,
    description: 'Build microservices and REST APIs with Spring Boot, Spring Security and JPA.',
    url: 'https://spring.io/guides',
    platform: 'Spring Guides',
  ),

  // ── DevOps / Docker ───────────────────────────────────────────────────────────
  const LearningItem(
    id: 'li07', title: 'Docker & Kubernetes: The Complete Guide', skillId: 'SK034',
    type: LearningType.course, duration: '45 hours', estimatedHours: 45, priority: 2,
    description: 'Containerization, orchestration, Helm charts and cloud deployment on AWS EKS.',
    url: 'https://docs.docker.com/get-started/',
    platform: 'Docker Docs',
  ),
  const LearningItem(
    id: 'li20', title: 'Docker & CI/CD Pipelines with GitHub Actions', skillId: 'SK036',
    type: LearningType.course, duration: '40 hours', estimatedHours: 40, priority: 1,
    description: 'Build Docker images, write CI/CD pipelines with GitHub Actions, deploy to cloud.',
    url: 'https://docs.github.com/en/actions/learn-github-actions/understanding-github-actions',
    platform: 'GitHub Docs',
  ),
  const LearningItem(
    id: 'li_a06', title: 'Docker Overview — Official Docs', skillId: 'SK034',
    type: LearningType.article, duration: '8 min read', estimatedHours: 0, priority: 3,
    description: 'Official Docker overview explaining containers, images, registries, and architecture.',
    url: 'https://docs.docker.com/get-started/overview/',
    platform: 'Docker Docs',
  ),

  // ── AWS / Cloud ───────────────────────────────────────────────────────────────
  const LearningItem(
    id: 'li08', title: 'AWS Cloud Practitioner Essentials', skillId: 'SK031',
    type: LearningType.certification, duration: '30 hours', estimatedHours: 30, priority: 2,
    description: 'AWS core services, pricing, security and architecture for the CLF-C02 exam.',
    url: 'https://www.coursera.org/learn/aws-cloud-practitioner-essentials',
    platform: 'Coursera',
  ),

  // ── Agile / Scrum ─────────────────────────────────────────────────────────────
  const LearningItem(
    id: 'li09', title: 'Project Management Professional (PMP) Prep', skillId: 'SK044',
    type: LearningType.certification, duration: '80 hours', estimatedHours: 80, priority: 1,
    description: 'PMI PMP certification preparation including predictive, agile and hybrid approaches.',
    url: 'https://www.coursera.org/learn/project-management-basics',
    platform: 'Coursera',
  ),
  const LearningItem(
    id: 'li10', title: 'Agile Scrum Master Certification (PSM I)', skillId: 'SK052',
    type: LearningType.certification, duration: '24 hours', estimatedHours: 24, priority: 1,
    description: 'Professional Scrum Master I exam prep — scrum framework, events, and artefacts.',
    url: 'https://www.scrum.org/assessments/professional-scrum-master-i-assessment',
    platform: 'Scrum.org',
  ),
  const LearningItem(
    id: 'li21', title: 'Scrum Master Preparation Practice Tests', skillId: 'SK052',
    type: LearningType.course, duration: '20 hours', estimatedHours: 20, priority: 1,
    description: 'Full PSM I practice exam sets with detailed explanations for every answer.',
    url: 'https://www.scrum.org/open-assessments/scrum-open',
    platform: 'Scrum.org',
  ),
  const LearningItem(
    id: 'li_a07', title: 'The Agile Manifesto Explained', skillId: 'SK051',
    type: LearningType.article, duration: '5 min read', estimatedHours: 0, priority: 3,
    description: 'Original Agile Manifesto with its 12 principles and how teams apply them today.',
    url: 'https://agilemanifesto.org/',
    platform: 'agilemanifesto.org',
  ),

  // ── Leadership / Mentorship ───────────────────────────────────────────────────
  const LearningItem(
    id: 'li11', title: 'Leadership & Mentorship Program', skillId: 'SK042',
    type: LearningType.mentorship, duration: '3 months', estimatedHours: 120, priority: 2,
    description: 'One-on-one mentoring with a senior leader on strategic thinking and team leadership.',
    url: 'https://www.coursera.org/learn/leadership-communication',
    platform: 'Coursera',
  ),
  const LearningItem(
    id: 'li30', title: 'Mentoring Skills for Technical Leads', skillId: 'SK049',
    type: LearningType.course, duration: '15 hours', estimatedHours: 15, priority: 2,
    description: 'Structured mentoring techniques for senior engineers — coaching, feedback, and growth plans.',
    url: 'https://www.coursera.org/learn/everyday-leadership-new-strategies',
    platform: 'Coursera',
  ),

  // ── Communication ─────────────────────────────────────────────────────────────
  const LearningItem(
    id: 'li31', title: 'Effective Business Communication', skillId: 'SK041',
    type: LearningType.course, duration: '12 hours', estimatedHours: 12, priority: 2,
    description: 'Written and verbal communication skills for technical professionals in the workplace.',
    url: 'https://www.coursera.org/learn/wharton-communication-skills',
    platform: 'Coursera',
  ),

  // ── Algorithms / Problem Solving ─────────────────────────────────────────────
  const LearningItem(
    id: 'li22', title: 'Algorithms & Data Structures in Python', skillId: 'SK043',
    type: LearningType.course, duration: '35 hours', estimatedHours: 35, priority: 2,
    description: 'Sorting, searching, graph algorithms, dynamic programming and competitive coding.',
    url: 'https://www.edx.org/learn/algorithms/massachusetts-institute-of-technology-introduction-to-algorithms',
    platform: 'edX',
  ),

  // ── Teamwork / Soft Skills ────────────────────────────────────────────────────
  const LearningItem(
    id: 'li23', title: 'Inspiring and Motivating Individuals', skillId: 'SK045',
    type: LearningType.course, duration: '10 hours', estimatedHours: 10, priority: 2,
    description: 'Science-backed frameworks for team motivation, feedback delivery, and conflict resolution.',
    url: 'https://www.coursera.org/learn/motivate-people-teams',
    platform: 'Coursera',
  ),

  // ── Mobile / Flutter ──────────────────────────────────────────────────────────
  const LearningItem(
    id: 'li12', title: 'Flutter & Dart — The Complete Guide', skillId: 'SK009',
    type: LearningType.course, duration: '55 hours', estimatedHours: 55, priority: 1,
    description: 'Complete Flutter app development: widgets, Riverpod, Firebase, animations and publishing.',
    url: 'https://docs.flutter.dev/get-started/codelab',
    platform: 'Flutter Docs',
  ),

  // ── UI/UX Design ─────────────────────────────────────────────────────────────
  const LearningItem(
    id: 'li13', title: 'Google UX Design Certificate', skillId: 'SK011',
    type: LearningType.certification, duration: '30 hours', estimatedHours: 30, priority: 2,
    description: 'End-to-end UX design: empathy maps, wireframes, prototypes and usability testing.',
    url: 'https://www.coursera.org/google-certificates/ux-design-certificate',
    platform: 'Coursera',
  ),

  // ── Cybersecurity ─────────────────────────────────────────────────────────────
  const LearningItem(
    id: 'li14', title: 'CompTIA Security+ Certification Prep', skillId: 'SK067',
    type: LearningType.certification, duration: '40 hours', estimatedHours: 40, priority: 1,
    description: 'CompTIA Security+ SY0-701 exam prep covering threats, cryptography and network security.',
    url: 'https://www.comptia.org/certifications/security',
    platform: 'CompTIA',
  ),

  // ── HR Analytics / Data Analysis ─────────────────────────────────────────────
  const LearningItem(
    id: 'li15', title: 'HR Analytics with Python — Capstone Project', skillId: 'SK022',
    type: LearningType.project, duration: '2 weeks', estimatedHours: 20, priority: 3,
    description: 'Apply data analysis techniques to real HR workforce planning and attrition scenarios.',
    url: 'https://www.datacamp.com/projects',
    platform: 'DataCamp',
  ),
  const LearningItem(
    id: 'li_a08', title: 'People Analytics: Using Data to Drive HR Decisions', skillId: 'SK022',
    type: LearningType.article, duration: '7 min read', estimatedHours: 0, priority: 2,
    description: 'Harvard Business Review article on how top companies use people analytics to improve retention.',
    url: 'https://hbr.org/2018/02/people-analytics-is-coming-of-age',
    platform: 'Harvard Business Review',
  ),

  // ── Statistics ────────────────────────────────────────────────────────────────
  const LearningItem(
    id: 'li32', title: 'Statistics for Data Science', skillId: 'SK024',
    type: LearningType.course, duration: '30 hours', estimatedHours: 30, priority: 2,
    description: 'Probability, distributions, hypothesis testing, regression, and Bayesian inference.',
    url: 'https://www.coursera.org/learn/statistics-for-data-science-python',
    platform: 'Coursera',
  ),

  // ── Linux / DevOps Foundation ─────────────────────────────────────────────────
  const LearningItem(
    id: 'li33', title: 'Linux Command Line & Shell Scripting', skillId: 'SK039',
    type: LearningType.course, duration: '20 hours', estimatedHours: 20, priority: 2,
    description: 'Shell fundamentals, Bash scripting, process management, and Linux system administration.',
    url: 'https://linuxcommand.org/tlcl.php',
    platform: 'linuxcommand.org',
  ),
  const LearningItem(
    id: 'li34', title: 'Bash Scripting Fundamentals', skillId: 'SK040',
    type: LearningType.course, duration: '10 hours', estimatedHours: 10, priority: 3,
    description: 'Automate Linux tasks with Bash — variables, loops, functions, and practical scripts.',
    url: 'https://www.gnu.org/software/bash/manual/',
    platform: 'GNU Bash Manual',
  ),
];
