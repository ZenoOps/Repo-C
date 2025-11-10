import { jwtDecode } from 'jwt-decode';
import { invalidate } from '$app/navigation';

interface JwtPayload {
	exp?: number;
}

export function validateToken(token: string | null | undefined): boolean {
	if (!token) return false;

	try {
		const decoded = jwtDecode<JwtPayload>(token);
		if (!decoded || typeof decoded !== 'object') return false;

		if (decoded.exp) {
			const now = Math.floor(Date.now() / 1000); // current time in seconds
			if (decoded.exp < now) return false; // token expired
		}

		return true; // token exists and not expired (or no expiry set)
	} catch (e) {
		console.log(e);
		return false;
	}
}

export function logout() {
	localStorage.removeItem('accessToken');
	localStorage.removeItem('refreshToken');
	invalidate('app:auth').then(() => {
		location.reload();
	});
}
