import axios from 'axios';
import { env } from '$env/dynamic/public';
import { browser } from '$app/environment';
import { logout } from '$lib/utils';

// --- Create axios instance ---
const axiosInstance = axios.create({
	baseURL: env.PUBLIC_API_URL,
	withCredentials: true,
	headers: {
		Accept: 'application/json'
	}
});

// --- Request interceptor ---
axiosInstance.interceptors.request.use(
	(config) => {
		// only run in browser to avoid SSR crash
		if (browser) {
			const accessToken = localStorage.getItem('accessToken');
			if (accessToken) {
				config.headers.Authorization = `Bearer ${accessToken}`;
			}
		}
		return config;
	},
	(error) => Promise.reject(error)
);

// --- Response interceptor ---
axiosInstance.interceptors.response.use(
	(response) => response,
	async (error) => {
		const originalRequest = error.config;

		if (!error.response) {
			console.error('Network error or server unreachable:', error.message);
			return Promise.reject(error);
		}

		if (error.response.status === 401 && !originalRequest._retry) {
			originalRequest._retry = true;

			/*
			try {
				const refreshToken = localStorage.getItem('refreshToken');
				if (!refreshToken) throw new Error('No refresh token found');

				const refreshResponse = await axios.post(
					`${env.PUBLIC_API_URL}/auth/refresh`,
					{ refresh_token: refreshToken },
					{ withCredentials: true }
				);

				const newAccessToken = refreshResponse.data.access_token;
				localStorage.setItem('accessToken', newAccessToken);

				originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
				return axiosInstance(originalRequest);
			} catch (refreshError) {
				console.error('Token refresh failed:', refreshError);
				logout();
			}
			*/

			logout();
		}

		return Promise.reject(error);
	}
);

export default axiosInstance;
