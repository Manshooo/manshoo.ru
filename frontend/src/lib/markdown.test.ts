import { describe, expect, it } from 'vitest';
import { renderMarkdown } from './markdown';

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
