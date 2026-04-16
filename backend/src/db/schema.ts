// src/db/schema.ts  — All Drizzle ORM table definitions
import {
  pgTable, text, integer, doublePrecision, boolean,
  timestamp, date, jsonb, pgEnum, primaryKey, index,
} from 'drizzle-orm/pg-core';
import { relations } from 'drizzle-orm';

// ── Enums ─────────────────────────────────────────────────────────────────────
export const userRoleEnum    = pgEnum('user_role', ['employee', 'manager', 'hr_admin']);
export const roleLevelEnum   = pgEnum('role_level', ['junior', 'mid', 'senior', 'lead', 'manager']);
export const skillCategoryEnum = pgEnum('skill_category', ['technical', 'management', 'soft', 'domain']);
export const attendanceStatusEnum = pgEnum('attendance_status', ['present', 'absent', 'late', 'half_day', 'remote']);
export const attendanceTypeEnum   = pgEnum('attendance_type', ['office', 'remote', 'field']);
export const leaveTypeEnum   = pgEnum('leave_type', ['annual', 'sick', 'compassionate', 'unpaid', 'maternity', 'paternity']);
export const leaveStatusEnum = pgEnum('leave_status', ['pending', 'approved', 'rejected', 'cancelled']);
export const payrollStatusEnum = pgEnum('payroll_status', ['draft', 'processed', 'paid']);
export const todoPriorityEnum  = pgEnum('todo_priority', ['low', 'medium', 'high', 'urgent']);
export const notificationTypeEnum = pgEnum('notification_type', ['info', 'warning', 'success', 'error']);
export const resignationStatusEnum = pgEnum('resignation_status', ['pending', 'approved', 'rejected', 'withdrawn']);
export const holidayTypeEnum = pgEnum('holiday_type', ['public', 'company', 'optional']);
export const riskLevelEnum   = pgEnum('risk_level', ['low', 'medium', 'high', 'critical']);
export const learningTypeEnum = pgEnum('learning_type', ['course', 'certification', 'mentorship', 'project', 'book']);
export const commuteDistanceEnum = pgEnum('commute_distance', ['near', 'moderate', 'far', 'very_far']);

// ── 1. users ──────────────────────────────────────────────────────────────────
export const users = pgTable('users', {
  id:           text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  email:        text('email').notNull().unique(),
  passwordHash: text('password_hash').notNull(),
  createdAt:    timestamp('created_at').notNull().defaultNow(),
  updatedAt:    timestamp('updated_at').notNull().defaultNow(),
});

// ── 2. refresh_tokens ─────────────────────────────────────────────────────────
export const refreshTokens = pgTable('refresh_tokens', {
  id:        text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  userId:    text('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
  token:     text('token').notNull().unique(),
  expiresAt: timestamp('expires_at').notNull(),
  createdAt: timestamp('created_at').notNull().defaultNow(),
}, (t) => ({ userIdx: index('rt_user_idx').on(t.userId) }));

// ── 3. user_roles ─────────────────────────────────────────────────────────────
export const userRoles = pgTable('user_roles', {
  id:     text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  userId: text('user_id').notNull().unique().references(() => users.id, { onDelete: 'cascade' }),
  role:   userRoleEnum('role').notNull().default('employee'),
});

// ── 4. departments ────────────────────────────────────────────────────────────
export const departments = pgTable('departments', {
  id:          text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  name:        text('name').notNull().unique(),
  description: text('description').notNull().default(''),
  managerId:   text('manager_id'),   // FK set after employees table
  createdAt:   timestamp('created_at').notNull().defaultNow(),
  updatedAt:   timestamp('updated_at').notNull().defaultNow(),
});

// ── 5. job_roles ──────────────────────────────────────────────────────────────
export const jobRoles = pgTable('job_roles', {
  id:          text('id').primaryKey(),   // matches Flutter mock IDs: r01, r02 ...
  title:       text('title').notNull(),
  department:  text('department').notNull(),
  level:       roleLevelEnum('level').notNull(),
  description: text('description').notNull().default(''),
  createdAt:   timestamp('created_at').notNull().defaultNow(),
  updatedAt:   timestamp('updated_at').notNull().defaultNow(),
});

// ── 6. skills ─────────────────────────────────────────────────────────────────
export const skills = pgTable('skills', {
  id:          text('id').primaryKey(),   // sk01, sk02 ...
  name:        text('name').notNull().unique(),
  category:    skillCategoryEnum('category').notNull(),
  description: text('description').notNull().default(''),
  createdAt:   timestamp('created_at').notNull().defaultNow(),
});

// ── 7. related_skills (many-to-many) ──────────────────────────────────────────
export const relatedSkills = pgTable('related_skills', {
  fromSkillId: text('from_skill_id').notNull().references(() => skills.id, { onDelete: 'cascade' }),
  toSkillId:   text('to_skill_id').notNull().references(() => skills.id, { onDelete: 'cascade' }),
}, (t) => ({ pk: primaryKey({ columns: [t.fromSkillId, t.toSkillId] }) }));

// ── 8. skill_chains ───────────────────────────────────────────────────────────
export const skillChains = pgTable('skill_chains', {
  id:          text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  fromSkillId: text('from_skill_id').notNull().references(() => skills.id, { onDelete: 'cascade' }),
  toSkillId:   text('to_skill_id').notNull().references(() => skills.id, { onDelete: 'cascade' }),
  description: text('description').notNull().default(''),
}, (t) => ({ idx: index('sc_from_idx').on(t.fromSkillId) }));

// ── 9. role_required_skills ───────────────────────────────────────────────────
export const roleRequiredSkills = pgTable('role_required_skills', {
  id:             text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  roleId:         text('role_id').notNull().references(() => jobRoles.id, { onDelete: 'cascade' }),
  skillId:        text('skill_id').notNull().references(() => skills.id, { onDelete: 'cascade' }),
  minProficiency: integer('min_proficiency').notNull(),
}, (t) => ({ roleIdx: index('rrs_role_idx').on(t.roleId) }));

// ── 10. employees ─────────────────────────────────────────────────────────────
export const employees = pgTable('employees', {
  id:                text('id').primaryKey(),       // emp01 ... emp50
  userId:            text('user_id').references(() => users.id, { onDelete: 'set null' }),
  name:              text('name').notNull(),
  email:             text('email').notNull().unique(),
  avatarUrl:         text('avatar_url').notNull().default(''),
  currentRole:       text('current_role').notNull(),
  roleId:            text('role_id').notNull().references(() => jobRoles.id),
  department:        text('department').notNull(),
  joinDate:          date('join_date').notNull(),
  salary:            doublePrecision('salary').notNull(),
  phone:             text('phone').notNull().default(''),
  commuteDistance:   commuteDistanceEnum('commute_distance').notNull().default('moderate'),
  satisfactionScore: doublePrecision('satisfaction_score').notNull().default(70),
  createdAt:         timestamp('created_at').notNull().defaultNow(),
  updatedAt:         timestamp('updated_at').notNull().defaultNow(),
}, (t) => ({
  emailIdx:  index('emp_email_idx').on(t.email),
  roleIdx:   index('emp_role_idx').on(t.roleId),
  deptIdx:   index('emp_dept_idx').on(t.department),
}));

// ── 11. employee_skills ───────────────────────────────────────────────────────
export const employeeSkills = pgTable('employee_skills', {
  id:           text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  employeeId:   text('employee_id').notNull().references(() => employees.id, { onDelete: 'cascade' }),
  skillId:      text('skill_id').notNull().references(() => skills.id, { onDelete: 'cascade' }),
  proficiency:  integer('proficiency').notNull(),   // 1-5
  lastAssessed: date('last_assessed').notNull(),
  updatedAt:    timestamp('updated_at').notNull().defaultNow(),
}, (t) => ({ empIdx: index('es_emp_idx').on(t.employeeId) }));

// ── 12. attendance ────────────────────────────────────────────────────────────
export const attendance = pgTable('attendance', {
  id:         text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  employeeId: text('employee_id').notNull().references(() => employees.id, { onDelete: 'cascade' }),
  date:       date('date').notNull(),
  checkIn:    text('check_in'),    // HH:MM string
  checkOut:   text('check_out'),
  status:     attendanceStatusEnum('status').notNull().default('present'),
  type:       attendanceTypeEnum('type').notNull().default('office'),
  notes:      text('notes').notNull().default(''),
}, (t) => ({
  empIdx:  index('att_emp_idx').on(t.employeeId),
  dateIdx: index('att_date_idx').on(t.date),
}));

// ── 13. leave_balances ────────────────────────────────────────────────────────
export const leaveBalances = pgTable('leave_balances', {
  id:         text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  employeeId: text('employee_id').notNull().references(() => employees.id, { onDelete: 'cascade' }),
  leaveType:  leaveTypeEnum('leave_type').notNull(),
  totalDays:  integer('total_days').notNull(),
  usedDays:   integer('used_days').notNull().default(0),
  year:       integer('year').notNull(),
}, (t) => ({ empIdx: index('lb_emp_idx').on(t.employeeId) }));

// ── 14. leave_requests ────────────────────────────────────────────────────────
export const leaveRequests = pgTable('leave_requests', {
  id:         text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  employeeId: text('employee_id').notNull().references(() => employees.id, { onDelete: 'cascade' }),
  leaveType:  leaveTypeEnum('leave_type').notNull(),
  startDate:  date('start_date').notNull(),
  endDate:    date('end_date').notNull(),
  reason:     text('reason').notNull().default(''),
  status:     leaveStatusEnum('status').notNull().default('pending'),
  approvedBy: text('approved_by').references(() => employees.id),
  approvedAt: timestamp('approved_at'),
  createdAt:  timestamp('created_at').notNull().defaultNow(),
}, (t) => ({
  empIdx:    index('lr_emp_idx').on(t.employeeId),
  statusIdx: index('lr_status_idx').on(t.status),
}));

// ── 15. payroll ───────────────────────────────────────────────────────────────
export const payroll = pgTable('payroll', {
  id:           text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  employeeId:   text('employee_id').notNull().references(() => employees.id, { onDelete: 'cascade' }),
  month:        integer('month').notNull(),   // 1-12
  year:         integer('year').notNull(),
  basicSalary:  doublePrecision('basic_salary').notNull(),
  allowances:   doublePrecision('allowances').notNull().default(0),
  deductions:   doublePrecision('deductions').notNull().default(0),
  netSalary:    doublePrecision('net_salary').notNull(),
  status:       payrollStatusEnum('status').notNull().default('draft'),
  paidDate:     date('paid_date'),
  createdAt:    timestamp('created_at').notNull().defaultNow(),
  updatedAt:    timestamp('updated_at').notNull().defaultNow(),
}, (t) => ({ empIdx: index('pay_emp_idx').on(t.employeeId) }));

// ── 16. todos ─────────────────────────────────────────────────────────────────
export const todos = pgTable('todos', {
  id:          text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  employeeId:  text('employee_id').notNull().references(() => employees.id, { onDelete: 'cascade' }),
  title:       text('title').notNull(),
  description: text('description').notNull().default(''),
  dueDate:     date('due_date'),
  priority:    todoPriorityEnum('priority').notNull().default('medium'),
  completed:   boolean('completed').notNull().default(false),
  createdAt:   timestamp('created_at').notNull().defaultNow(),
  updatedAt:   timestamp('updated_at').notNull().defaultNow(),
}, (t) => ({ empIdx: index('todo_emp_idx').on(t.employeeId) }));

// ── 17. notifications ─────────────────────────────────────────────────────────
export const notifications = pgTable('notifications', {
  id:         text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  employeeId: text('employee_id').notNull().references(() => employees.id, { onDelete: 'cascade' }),
  title:      text('title').notNull(),
  message:    text('message').notNull(),
  type:       notificationTypeEnum('type').notNull().default('info'),
  read:       boolean('read').notNull().default(false),
  createdAt:  timestamp('created_at').notNull().defaultNow(),
}, (t) => ({ empIdx: index('notif_emp_idx').on(t.employeeId) }));

// ── 18. resignation_requests ──────────────────────────────────────────────────
export const resignationRequests = pgTable('resignation_requests', {
  id:                text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  employeeId:        text('employee_id').notNull().references(() => employees.id, { onDelete: 'cascade' }),
  lastWorkingDate:   date('last_working_date').notNull(),
  noticePeriodDays:  integer('notice_period_days').notNull().default(30),
  reason:            text('reason').notNull().default(''),
  status:            resignationStatusEnum('status').notNull().default('pending'),
  approvedBy:        text('approved_by').references(() => employees.id),
  approvedAt:        timestamp('approved_at'),
  createdAt:         timestamp('created_at').notNull().defaultNow(),
}, (t) => ({ empIdx: index('res_emp_idx').on(t.employeeId) }));

// ── 19. holidays ──────────────────────────────────────────────────────────────
export const holidays = pgTable('holidays', {
  id:          text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  name:        text('name').notNull(),
  date:        date('date').notNull().unique(),
  type:        holidayTypeEnum('type').notNull().default('public'),
  description: text('description').notNull().default(''),
});

// ── 20. audit_logs ────────────────────────────────────────────────────────────
export const auditLogs = pgTable('audit_logs', {
  id:         text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  userId:     text('user_id').references(() => users.id, { onDelete: 'set null' }),
  action:     text('action').notNull(),        // CREATE | READ | UPDATE | DELETE | LOGIN | LOGOUT
  entityType: text('entity_type').notNull(),   // employee, leave_request, payroll, ...
  entityId:   text('entity_id'),
  oldValues:  jsonb('old_values'),
  newValues:  jsonb('new_values'),
  ipAddress:  text('ip_address'),
  userAgent:  text('user_agent'),
  createdAt:  timestamp('created_at').notNull().defaultNow(),
}, (t) => ({
  userIdx:   index('al_user_idx').on(t.userId),
  entityIdx: index('al_entity_idx').on(t.entityType),
  timeIdx:   index('al_time_idx').on(t.createdAt),
}));

// ── 21. learning_items ────────────────────────────────────────────────────────
export const learningItems = pgTable('learning_items', {
  id:          text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  title:       text('title').notNull(),
  skillId:     text('skill_id').references(() => skills.id, { onDelete: 'set null' }),
  type:        learningTypeEnum('type').notNull().default('course'),
  url:         text('url').notNull().default(''),
  durationHrs: doublePrecision('duration_hrs').notNull().default(0),
  priority:    todoPriorityEnum('priority').notNull().default('medium'),
  description: text('description').notNull().default(''),
  createdAt:   timestamp('created_at').notNull().defaultNow(),
});

// ── 22. chat_messages ─────────────────────────────────────────────────────────
export const chatMessages = pgTable('chat_messages', {
  id:           text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  senderId:     text('sender_id').notNull().references(() => employees.id, { onDelete: 'cascade' }),
  receiverId:   text('receiver_id').references(() => employees.id, { onDelete: 'set null' }),
  content:      text('content').notNull(),
  isAiResponse: boolean('is_ai_response').notNull().default(false),
  createdAt:    timestamp('created_at').notNull().defaultNow(),
}, (t) => ({ senderIdx: index('cm_sender_idx').on(t.senderId) }));

// ── 23. turnover_risk_cache ───────────────────────────────────────────────────
export const turnoverRiskCache = pgTable('turnover_risk_cache', {
  id:              text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  employeeId:      text('employee_id').notNull().unique().references(() => employees.id, { onDelete: 'cascade' }),
  riskScore:       doublePrecision('risk_score').notNull(),
  riskLevel:       riskLevelEnum('risk_level').notNull(),
  factorBreakdown: jsonb('factor_breakdown').notNull(),
  calculatedAt:    timestamp('calculated_at').notNull().defaultNow(),
});

// ── Relations ─────────────────────────────────────────────────────────────────
export const usersRelations = relations(users, ({ one, many }) => ({
  role:            one(userRoles, { fields: [users.id], references: [userRoles.userId] }),
  refreshTokens:   many(refreshTokens),
  auditLogs:       many(auditLogs),
}));

export const employeesRelations = relations(employees, ({ one, many }) => ({
  user:               one(users, { fields: [employees.userId], references: [users.id] }),
  jobRole:            one(jobRoles, { fields: [employees.roleId], references: [jobRoles.id] }),
  skills:             many(employeeSkills),
  attendance:         many(attendance),
  leaveBalances:      many(leaveBalances),
  leaveRequests:      many(leaveRequests),
  payroll:            many(payroll),
  todos:              many(todos),
  notifications:      many(notifications),
  resignations:       many(resignationRequests),
  sentMessages:       many(chatMessages, { relationName: 'sentMessages' }),
  turnoverRiskCache:  one(turnoverRiskCache, { fields: [employees.id], references: [turnoverRiskCache.employeeId] }),
}));

export const jobRolesRelations = relations(jobRoles, ({ many }) => ({
  requiredSkills: many(roleRequiredSkills),
  employees:      many(employees),
}));

export const skillsRelations = relations(skills, ({ many }) => ({
  roleRequirements: many(roleRequiredSkills),
  employeeSkills:   many(employeeSkills),
  chainsFrom:       many(skillChains, { relationName: 'chainsFrom' }),
  chainsTo:         many(skillChains, { relationName: 'chainsTo' }),
  learningItems:    many(learningItems),
}));

// ── Type exports ──────────────────────────────────────────────────────────────
export type User            = typeof users.$inferSelect;
export type NewUser         = typeof users.$inferInsert;
export type Employee        = typeof employees.$inferSelect;
export type NewEmployee     = typeof employees.$inferInsert;
export type Skill           = typeof skills.$inferSelect;
export type JobRole         = typeof jobRoles.$inferSelect;
export type EmployeeSkill   = typeof employeeSkills.$inferSelect;
export type Attendance      = typeof attendance.$inferSelect;
export type LeaveRequest    = typeof leaveRequests.$inferSelect;
export type LeaveBalance    = typeof leaveBalances.$inferSelect;
export type Payroll         = typeof payroll.$inferSelect;
export type Todo            = typeof todos.$inferSelect;
export type Notification    = typeof notifications.$inferSelect;
export type AuditLog        = typeof auditLogs.$inferSelect;
export type ChatMessage     = typeof chatMessages.$inferSelect;
export type TurnoverCache   = typeof turnoverRiskCache.$inferSelect;
