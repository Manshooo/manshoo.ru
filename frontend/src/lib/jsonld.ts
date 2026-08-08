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
	if (project.cover_url) work.image = project.cover_url;
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
