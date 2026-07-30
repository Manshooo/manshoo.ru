// Cloudflare Worker: прозрачный прокси к Telegram Bot API.
// Нужен, потому что api.telegram.org заблокирован с нашего хостинга
// (см. docs/05-uptime.md). Деплой: dash.cloudflare.com → Workers →
// Create → вставить этот файл → Deploy. Полученный адрес
// (https://<имя>.<аккаунт>.workers.dev) прописать в
// /var/www/manshoo/uptime/.env как TELEGRAM_API_BASE.
//
// Worker не хранит и не логирует токен — он лишь меняет хост запроса.
export default {
	async fetch(request) {
		const url = new URL(request.url);
		url.hostname = 'api.telegram.org';
		url.protocol = 'https:';
		url.port = '';
		return fetch(new Request(url, request));
	}
};
