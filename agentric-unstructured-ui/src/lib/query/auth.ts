import axios from 'axios';
import { env } from '$env/dynamic/public';
import type {
	CreateUser,
	MemberType,
	Role,
	Team,
	User,
	UserProfile,
	// UserRole
} from '$lib/types/user';
import axiosInstance from '$lib/query/axiosInstance';
import type { PaginatedData } from '$lib/types/request';
import type { QueryFunctionContext } from '@tanstack/svelte-query';

export const login = async (username: string, password: string) => {
	// , type: UserRole
	const params = new URLSearchParams();
	params.append('username', username);
	params.append('password', password);
	// params.append('type', type);

	return axios.post<
		undefined,
		{
			data: {
				access_token: string;
				token_type: string;
				refresh_token: string | null;
				expires_in: number;
			};
		}
	>(`${env.PUBLIC_API_URL}/api/access/login`, params, {
		headers: {
			'Content-Type': 'application/x-www-form-urlencoded'
		}
	});
};

export const refreshToken = async (refreshToken: string) => {
	return await axios.post(`${env.PUBLIC_API_URL}/api/tokens/refresh`, {
		refresh_token: refreshToken
	});
};

export const getUser = async () => {
	return (await axiosInstance.get<User>('/api/me')).data;
};

export const getUserList = async (arg: QueryFunctionContext) => {
	const currentPage = arg.queryKey[1] ?? 1;
	return (
		await axiosInstance.get<PaginatedData<UserProfile>>(
			`/api/users?currentPage=${currentPage}&pageSize=20&orderBy=updated_at&sortOrder=desc`
		)
	).data;
};

// for infinite scroll

export const getUserListScroll = async ({ page = 1 }: { page?: number }) => {
	const { data } = await axiosInstance.get<PaginatedData<UserProfile>>(
		`/api/users?currentPage=${page}&pageSize=20&orderBy=updated_at&sortOrder=desc`
	);
	return data;
};

export const createUser = async (data: CreateUser) => {
	return (await axiosInstance.post<UserProfile>('/api/access/signup', data)).data;
};

export const deleteUser = async (userId: string) => {
	return await axiosInstance.delete(`/api/users/${userId}`);
};

export const updateUser = async (data: {
	userId: string;
	data: { name?: string; email?: string; password?: string };
}) => {
	return (await axiosInstance.patch<UserProfile>(`/api/users/${data.userId}`, data.data)).data;
};

export const getRoles = async () => {
	return (await axiosInstance.get('api/roles/list')).data as Role[];
};

// ---- Team APIs ---- //

export const getTeams = async () => {
	return (await axiosInstance.get('/api/teams')).data as PaginatedData<Team>;
};
export const createTeam = async (data: { name: string; description: string }) => {
	return (await axiosInstance.post('/api/teams', data)).data as Team;
};

export const getTeamDetails = async (args: QueryFunctionContext) => {
	const team_id = args.queryKey[1];
	return (await axiosInstance.get(`/api/teams/${team_id}`)).data as Team;
};

export const addTeamMember = async (data: {
	team_id: string;
	data: {
		memberEmail: string;
		role: MemberType;
		isOwner: boolean;
	};
}) => {
	return (await axiosInstance.post(`/api/teams/${data.team_id}/members/add`, data.data)).data;
};

export const updateTeamMemberRole = async (data: {
	team_id: string;
	data: {
		memberEmail: string;
		role: MemberType;
		isOwner: boolean;
	};
}) => {
	return (await axiosInstance.put(`/api/teams/${data.team_id}/members/update`, data.data)).data;
};

export const removeTeamMember = async (data: {
	team_id: string;
	data: {
		memberEmail: string;
		role: MemberType;
		isOwner: boolean;
	};
}) => {
	return (await axiosInstance.post(`/api/teams/${data.team_id}/members/remove`, data.data)).data;
};
