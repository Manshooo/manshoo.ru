import { describe, expect, it } from 'vitest';
import { renderLectureMarkdown, renderMarkdown } from './markdown';

describe('renderMarkdown', () => {
	it('рендерит абзацы и выделение', () => {
		const html = renderMarkdown('Привет, **мир**!');
		expect(html).toContain('<strong>мир</strong>');
		expect(html).toContain('<p>');
	});

	it('рендерит списки', () => {
		expect(renderMarkdown('- один\n- два')).toContain('<li>два</li>');
	});
});

describe('renderLectureMarkdown', () => {
	it('не трогает LaTeX внутри $…$', () => {
		const { html } = renderLectureMarkdown('Пусть $a_1 + b_1 < c$ и $5 и $10.');
		expect(html).toContain('<span class="math">$a_1 + b_1 &lt; c$</span>');
		expect(html).not.toContain('<em>');
		expect(html).toContain('$5 и $10');
	});

	it('выделяет $$…$$ блоком', () => {
		const { html } = renderLectureMarkdown('$$|G| = |H| \\cdot [G : H]$$');
		expect(html).toContain('class="math math-display"');
	});

	it('строит оглавление по h2 без таймкодов', () => {
		const { html, toc } = renderLectureMarkdown(
			'## 1. Определение группы [00:02:15]\n\nтекст\n\n### Детали\n\n## Ёлки\n\n## Ёлки'
		);
		expect(toc).toEqual([
			{ id: '1-определение-группы', text: '1. Определение группы' },
			{ id: 'елки', text: 'Ёлки' },
			{ id: 'елки-2', text: 'Ёлки' }
		]);
		expect(html).toContain('<h2 id="1-определение-группы">1. Определение группы [00:02:15]</h2>');
		expect(html).toContain('<h3 id="детали">');
	});
});
