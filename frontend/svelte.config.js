import adapter from '@sveltejs/adapter-node';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	preprocess: vitePreprocess(),
	kit: {
		adapter: adapter(),
		// Стилей на страницу — пара килобайт, поэтому вшиваем их в HTML:
		// три блокирующих запроса за CSS исчезают, рендер не ждёт сети.
		inlineStyleThreshold: 4096
	}
};

export default config;
