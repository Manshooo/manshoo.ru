import type { ProjectStatus, ProjectType } from './types';

const monthYear = new Intl.DateTimeFormat('ru', { month: 'short', year: 'numeric' });

/** «июл. 2026 г. — н. в.» */
export function formatPeriod(start: string, end: string | null): string {
	const from = monthYear.format(new Date(start));
	const to = end ? monthYear.format(new Date(end)) : 'н. в.';
	return `${from} — ${to}`;
}

export const typeLabels: Record<ProjectType, string> = {
	work: 'работа',
	pet: 'пет-проект',
	oss: 'open source',
	freelance: 'фриланс'
};

export const statusLabels: Record<ProjectStatus, string> = {
	active: 'живой',
	wip: 'в разработке',
	archived: 'архив'
};
