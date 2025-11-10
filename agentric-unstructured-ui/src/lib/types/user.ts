export enum UserRole {
	ANALYST = 'ZURICH_AGENT',
	ADMIN = 'ZURICH_ADMIN',
	CUSTOMER = 'CUSTOMER',
	TRAVEL_GUARD_ROLE = 'TRAVEL_GUARD',
	COVER_MORE_ROLE = 'COVERMORE'
}

export type User = {
	email: string;
	id: string;
	isSuperuser: boolean;
	name: string;
	role: string;
	teamId: string | null;
	teamName: string | null;
	token: string | null;
};

// export type PaginatedData<T> = {
// 	items: T[];
// 	limit: number;
// 	offset: number;
// 	total: number;
// };

export enum MemberType {
	ADMIN = 'ADMIN',
	MEMBER = 'MEMBER'
}

export type UserRoleType = {
	roleId: string;
	roleSlug: string;
	roleName: UserRole;
	assignedAt: string;
};

export type TeamMember = {
	id: string;
	name: string;
	email: string;
	memberType: MemberType;
	user_id: string;
	role: MemberType;
	isOwner: boolean;
};

export type Team = {
	id: string;
	name: string;
	description: string | null;
	members: TeamMember[];
};

export type UserProfile = {
	email: string;
	hasPassword: boolean;
	id: string;
	isActive: boolean;
	isSuperuser: boolean;
	isVerified: boolean;
	name: string;
	roles: UserRoleType[];
	teams: { teamName: string; id: string }[];
	oauthAccounts: [];
};

export type CreateUser = {
	email: string;
	password: string;
	teamId: string;
	name: string | null;
};

export type Role = {
	id: string;
	name: string;
};
