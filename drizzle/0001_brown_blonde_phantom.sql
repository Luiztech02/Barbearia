CREATE TABLE `sb_team_access` (
	`email` text PRIMARY KEY NOT NULL,
	`name` text NOT NULL,
	`barber_id` text,
	`enabled` integer DEFAULT 1 NOT NULL,
	`updated_at` integer NOT NULL
);
