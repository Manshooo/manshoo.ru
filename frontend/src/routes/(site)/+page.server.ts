import { renderMarkdown } from '$lib/markdown';
import { getProjects } from '$lib/server/api';
import { getMonitorMap } from '$lib/server/uptime';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch, parent }) => {
	const [{ profile }, projects, monitors] = await Promise.all([
		parent(),
		getProjects(fetch),
		getMonitorMap(fetch)
	]);
	// Markdown разворачиваем на сервере: иначе marked (~43 КБ) уезжает в
	// клиентский бандл и на гидратации заново парсит то, что уже в HTML.
	return { projects, monitors, bioHtml: renderMarkdown(profile.bio_md) };
};
