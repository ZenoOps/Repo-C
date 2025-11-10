export function formatDate(input: string): string {
	const date = new Date(input);
	const options: Intl.DateTimeFormatOptions = {
		day: '2-digit',
		month: 'short',
		year: 'numeric'
	};

	return date.toLocaleDateString('en-US', options).replace(',', ',');
}

export function formatTime(input: string): string {
	const date = new Date(input);
	return date.toLocaleTimeString('en-US', {
		hour: '2-digit',
		minute: '2-digit'
	});
}

export function extractBase64FromMime(mimeText: string): string | null {
	const base64Match = mimeText.match(/Content-Transfer-Encoding: base64\s+([\s\S]*?)\n--/);
	if (!base64Match) return '';
	return base64Match[1].trim();
}
export function extractHeaders(mime: string): Record<string, string> {
	const headers: Record<string, string> = {};
	const lines = mime.split(/\r?\n/);

	for (const line of lines) {
		if (line.trim() === '') break;
		const [key, ...rest] = line.split(':');
		if (key && rest.length) {
			headers[key.trim()] = rest.join(':').trim();
		}
	}
	return headers;
}

export function convertSnaketoFormatedCase(text: string) {
	return text.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
}

export const logOut = () => {
	localStorage.removeItem('accessToken');
	localStorage.removeItem('user');
	localStorage.removeItem('isChatHad');
	location.replace('/signin');
};

export function getTime() {
	return new Date().toLocaleTimeString('en-us', {
		hour: '2-digit',
		minute: '2-digit',
		hour12: true
	});
}

export function toTitleCase(str: string): string {
	return str
		.toLowerCase()
		.split(' ')
		.map((word) => word.charAt(0).toUpperCase() + word.slice(1))
		.join(' ');
}
