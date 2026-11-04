// Структурированные данные для поисковиков (schema.org).
import { SITE_URL } from '$lib/seo';
import type { Profile, ProjectDetail } from '$lib/types';

type Json = Record<string, unknown>;

const socialUrls = (socials: Record<string, string>) =>
	Object.entries(socials)
		.filter(([key]) => key !== 'email')
		.map(([, url]) => url)
		.filter((url) => url.startsWith('http'));

export function personJsonLd(profile: Profile): Json {
	const person: Json = {
		'@context': 'https://schema.org',
		'@type': 'Person',
		'@id': `${SITE_URL}/#person`,
		name: profile.name,
		description: profile.headline,
		url: SITE_URL,
		knowsAbout: profile.skills
	};
	if (profile.location) person.homeLocation = { '@type': 'Place', name: profile.location };
	if (profile.photo_url) person.image = profile.photo_url;
	if (profile.socials.email) person.email = `mailto:${profile.socials.email}`;

	const sameAs = socialUrls(profile.socials);
	if (sameAs.length) person.sameAs = sameAs;
	return person;
}

export function webSiteJsonLd(profile: Profile): Json {
	return {
		'@context': 'https://schema.org',
		'@type': 'WebSite',
		'@id': `${SITE_URL}/#website`,
		url: SITE_URL,
		name: `${profile.name} — портфолио`,
		inLanguage: 'ru-RU',
		author: { '@id': `${SITE_URL}/#person` }
	};
}

/**
 * Проект — SoftwareSourceCode, когда есть репозиторий, иначе CreativeWork:
 * тип должен отражать суть, а не быть натянутым на всё подряд.
 */
export function projectJsonLd(project: ProjectDetail, profile: Profile): Json {
	const url = `${SITE_URL}/projects/${project.slug}`;
	const isCode = Boolean(project.links.repo);

	const work: Json = {
		'@context': 'https://schema.org',
		'@type': isCode ? 'SoftwareSourceCode' : 'CreativeWork',
		name: project.title,
		abstract: project.tagline,
		url,
		author: { '@id': `${SITE_URL}/#person` },
		dateCreated: project.period_start,
		dateModified: project.updated_at,
		inLanguage: 'ru-RU'
	};
	if (project.stack.length) {
		work.keywords = project.stack.join(', ');
		if (isCode) work.programmingLanguage = project.stack;
	}
	if (isCode) work.codeRepository = project.links.repo;
	const images = [project.cover_url, ...project.images.map((i) => i.url)].filter(Boolean);
	if (images.length) work.image = images;
	if (profile.name) work.creator = { '@id': `${SITE_URL}/#person` };
	return work;
}

export function breadcrumbsJsonLd(project: ProjectDetail): Json {
	return {
		'@context': 'https://schema.org',
		'@type': 'BreadcrumbList',
		itemListElement: [
			{ '@type': 'ListItem', position: 1, name: 'Главная', item: SITE_URL },
			{
				'@type': 'ListItem',
				position: 2,
				name: project.title,
				item: `${SITE_URL}/projects/${project.slug}`
			}
		]
	};
}

interface CourseLd {
	slug: string;
	title: string;
	description: string;
	lecturer: string;
	institution: string;
	language: string;
	license: { url: string };
}

const lecturerLd = (name: string) => ({ '@type': 'Person', name });

export function courseJsonLd(course: CourseLd): Json {
	const ld: Json = {
		'@context': 'https://schema.org',
		'@type': 'Course',
		name: course.title,
		description: course.description,
		url: `${SITE_URL}/lectures/${course.slug}`,
		inLanguage: course.language,
		instructor: lecturerLd(course.lecturer),
		license: course.license.url,
		isAccessibleForFree: true
	};
	if (course.institution) ld.provider = { '@type': 'Organization', name: course.institution };
	return ld;
}

interface LectureLd {
	slug: string;
	title: string;
	kind: 'transcript' | 'notes';
	lecturer: string;
	author: string;
	date: string;
	updated: string;
	language: string;
	license: { url: string };
	source: { url: string; title: string } | null;
	topics: string[];
	summary: string;
}

/**
 * Транскрипция — произведение лектора (author), конспект — составителя,
 * сделанный по лекции (isBasedOn). Так атрибуция видна и машинам.
 */
export function lectureJsonLd(course: CourseLd, l: LectureLd): Json {
	const ld: Json = {
		'@context': 'https://schema.org',
		'@type': 'LearningResource',
		name: l.title,
		abstract: l.summary,
		url: `${SITE_URL}/lectures/${course.slug}/${l.slug}`,
		learningResourceType: l.kind === 'transcript' ? 'Транскрипция лекции' : 'Конспект лекции',
		author: lecturerLd(l.author),
		dateCreated: l.date,
		dateModified: l.updated,
		inLanguage: l.language,
		license: l.license.url,
		isAccessibleForFree: true,
		encodingFormat: 'text/markdown',
		isPartOf: { '@type': 'Course', name: course.title, url: `${SITE_URL}/lectures/${course.slug}` }
	};
	if (l.topics.length) ld.keywords = l.topics.join(', ');
	if (l.kind === 'notes') ld.contributor = lecturerLd(l.lecturer);
	if (l.source) {
		ld.isBasedOn = {
			'@type': 'VideoObject',
			url: l.source.url,
			name: l.source.title || l.title,
			creator: lecturerLd(l.lecturer)
		};
	}
	return ld;
}

export function lectureBreadcrumbsJsonLd(course: CourseLd, lecture?: LectureLd): Json {
	const items = [
		{ name: 'Главная', item: SITE_URL },
		{ name: 'Лекции', item: `${SITE_URL}/lectures` },
		{ name: course.title, item: `${SITE_URL}/lectures/${course.slug}` }
	];
	if (lecture) {
		items.push({
			name: lecture.title,
			item: `${SITE_URL}/lectures/${course.slug}/${lecture.slug}`
		});
	}
	return {
		'@context': 'https://schema.org',
		'@type': 'BreadcrumbList',
		itemListElement: items.map((it, i) => ({ '@type': 'ListItem', position: i + 1, ...it }))
	};
}
