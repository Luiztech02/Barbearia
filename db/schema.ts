import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';
export const appState=sqliteTable('sb_state',{id:integer('id').primaryKey(),data:text('data').notNull(),revision:integer('revision').notNull()});
export const history=sqliteTable('sb_history',{id:integer('revision').primaryKey(),data:text('data').notNull(),savedAt:integer('saved_at').notNull()});
export const rateLimit=sqliteTable('sb_rate_limit',{key:text('key').primaryKey(),count:integer('count').notNull(),resetAt:integer('reset_at').notNull()});
export const teamAccess=sqliteTable('sb_team_access',{email:text('email').primaryKey(),name:text('name').notNull(),barberId:text('barber_id'),enabled:integer('enabled').notNull().default(1),updatedAt:integer('updated_at').notNull()});
