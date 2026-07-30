// Контракт с api (см. api/content/schemas.py).
// Пока вручную: контракт маленький; генерация из OpenAPI — вместе с админкой (Phase 3).

export interface Profile {
	name: string;
	headline: string;
	bio_md: string;
	location: string;
	skills: string[];
	socials: Record<string, string>;
	meta_description: string;
	photo_url: string | null;
}

export type ProjectType = 'work' | 'pet' | 'oss' | 'freelance';
export type ProjectStatus = 'active' | 'wip' | 'archived';

export interface ProjectCard {
	slug: string;
	title: string;
	tagline: string;
	role: string;
	org: string;
	project_type: ProjectType;
	status: ProjectStatus;
	period_start: string; // ISO-дата
	period_end: string | null;
	stack: string[];
	is_featured: boolean;
	uptime_monitor_slug: string;
	cover_url: string | null;
	updated_at: string; // ISO-датавремя
}

export interface ProjectDetail extends ProjectCard {
	id: number;
	description_md: string;
	highlights: string[];
	links: Record<string, string>;
	is_published: boolean;
	sort_order: number;
}
