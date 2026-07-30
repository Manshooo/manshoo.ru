import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vitest/config';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		host: true,
		port: 5173,
		strictPort: true,
		watch: {
			// inotify не работает через volume-mount под Docker Desktop на Windows
			usePolling: process.env.VITE_USE_POLLING === '1'
		}
	},
	test: {
		include: ['src/**/*.test.ts']
	}
});
