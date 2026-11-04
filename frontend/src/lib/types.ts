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

// Ответ uptime-чекера (uptime/internal/api/api.go)
export interface MonitorStatus {
	slug: string;
	name: string;
	url: string;
	status: 'up' | 'down' | 'unknown';
	since: string;
	uptime_24h: number | null;
	uptime_7d: number | null;
	uptime_30d: number | null;
	median_latency_ms_24h: number | null;
	last_check: {
		at: string;
		ok: boolean;
		http_status: number;
		latency_ms: number;
		error?: string;
	} | null;
	tls_days_left: number | null;
	tls_not_after: string | null;
}

// Кадр галереи: превью для сетки, полный размер — для просмотра по клику
export interface ProjectImage {
	id: number;
	url: string;
	thumb_url: string;
	width: number;
	height: number;
	caption: string;
}

export interface ProjectDetail extends ProjectCard {
	id: number;
	description_md: string;
	highlights: string[];
	links: Record<string, string>;
	is_published: boolean;
	sort_order: number;
	images: ProjectImage[];
}

// --- Лекции (api/content/lectures_api.py) ---

export type LectureKind = 'transcript' | 'notes';
export type LectureQuality = 'asr' | 'edited' | 'verified';

export interface License {
	id: string;
	name: string;
	url: string;
}

export interface LectureCard {
	id: number;
	slug: string;
	title: string;
	number: number | null;
	kind: LectureKind;
	date: string;
	updated: string;
	summary: string;
	duration: string;
	is_published: boolean;
}

export interface Course {
	id: number;
	slug: string;
	title: string;
	description: string;
	body_md: string;
	lecturer: string;
	institution: string;
	year: string;
	language: string;
	license: License;
	is_published: boolean;
	sort_order: number;
	lectures: LectureCard[];
}

export type CourseBrief = Pick<
	Course,
	'slug' | 'title' | 'description' | 'lecturer' | 'institution' | 'language' | 'license'
>;

export interface Lecture {
	slug: string;
	title: string;
	number: number | null;
	kind: LectureKind;
	lecturer: string;
	author: string;
	date: string;
	updated: string;
	language: string;
	license: License;
	quality: LectureQuality;
	is_published: boolean;
	source: { url: string; title: string; duration: string } | null;
	topics: string[];
	summary: string;
	body_md: string;
	course: CourseBrief;
	prev: { slug: string; title: string } | null;
	next: { slug: string; title: string } | null;
}

export interface DatasetRecord {
	id: string;
	course: string;
	title: string;
	number: number | null;
	kind: LectureKind;
	lecturer: string;
	author: string;
	institution: string | null;
	date: string;
	updated: string;
	language: string;
	license: string;
	quality: LectureQuality;
	source_url: string | null;
	topics: string[];
	summary: string;
	text: string;
}
