<script lang="ts">
	import { page } from '$app/state';
	import CourseForm from '$lib/admin/CourseForm.svelte';
	import { api, ApiError } from '$lib/admin/client';
	import type { Course } from '$lib/types';

	let course = $state<Course | null>(null);
	let error = $state('');

	$effect(() => {
		const id = Number(page.params.id);
		// отдельного GET для курса нет: список маленький, берём из него
		api
			.listCourses()
			.then((list) => {
				course = list.find((c) => c.id === id) ?? null;
				if (!course) error = 'Курс не найден';
			})
			.catch((e) => (error = e instanceof ApiError ? e.message : 'Не удалось загрузить'));
	});
</script>

{#if error}
	<p class="error">{error}</p>
{:else if course}
	<h1>{course.title}</h1>
	{#key course.id}
		<CourseForm {course} />
	{/key}
{:else}
	<p class="muted">Загружаем…</p>
{/if}

<style>
	h1 {
		font-size: 1.5rem;
		margin: 0 0 1.5rem;
	}
	.muted {
		color: var(--muted);
	}
	.error {
		color: #dc2626;
	}
</style>
