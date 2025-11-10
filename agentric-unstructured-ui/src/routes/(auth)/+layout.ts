// src/routes/signin/+page.ts
import { browser } from '$app/environment';
import { validateToken } from '$lib/utils';
import { redirect, type Load } from '@sveltejs/kit';

export const load: Load = () => {
	if (browser) {
		const token = localStorage.getItem('accessToken');
		if (token && validateToken(token)) {
			throw redirect(302, '/');
		}
	}
};
