import type { ProjectStatus, ProjectType } from './types';

const monthYear = new Intl.DateTimeFormat('ru', { month: 'short', year: 'numeric' });

/** «июл. 2026 г. — н. в.» */
export function formatPeriod(start: string, end: string | null): string {
	const from = monthYear.format(new Date(start));
	const to = end ? monthYear.format(new Date(end)) : 'н. в.';
	return `${from} — ${to}`;
}

/** «99.9%» или «нет данных», если проверок за период не было. */
export function formatUptime(percent: number | null): string {
	if (percent === null) return 'нет данных';
	return `${percent.toFixed(percent === 100 ? 0 : 2)}%`;
}

const dateTime = new Intl.DateTimeFormat('ru', { dateStyle: 'short', timeStyle: 'short' });

/** «в этом статусе с 01.08.2026, 14:05» */
export function formatSince(iso: string): string {
	return dateTime.format(new Date(iso));
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
