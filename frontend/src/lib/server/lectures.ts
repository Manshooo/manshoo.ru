// Каталог лекций нужен почти каждой странице (пункт меню, sitemap, llms.txt),
// а меняется редко — держим его в памяти процесса минуту, чтобы не дёргать api
// на каждый запрос. Тексты лекций сюда не входят: они грузятся постранично.
import { error } from '@sveltejs/kit';
import { getLectureCatalog } from '$lib/server/api';
import type { Course } from '$lib/types';

const TTL_MS = 60_000;
let cached: { at: number; courses: Course[] } | null = null;

export async function getCatalog(fetchFn: typeof fetch): Promise<Course[]> {
	if (cached && Date.now() - cached.at < TTL_MS) return cached.courses;
	const courses = await getLectureCatalog(fetchFn);
	cached = { at: Date.now(), courses };
	return courses;
}

export async function getCourse(fetchFn: typeof fetch, slug: string): Promise<Course> {
	const course = (await getCatalog(fetchFn)).find((c) => c.slug === slug);
	if (!course) error(404, 'Не найдено');
	return course;
}
