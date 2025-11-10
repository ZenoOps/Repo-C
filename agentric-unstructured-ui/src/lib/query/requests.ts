// import { env } from '$env/dynamic/public';
import type { PolicyStatisticData } from '$lib/types/chat';
import type {
	CoverageRecommendation,
	DeclineValues,
	RiskInfo,
	Request,
	AppetiteInfo,
	CoverageItem,
	ClaimResponse
} from '$lib/types/request';
import type { QueryFunctionContext } from '@tanstack/svelte-query';
// import axios from 'axios';
import axiosInstance from './axiosInstance';

export const createReq = async (data: FormData) => {
	// const token = localStorage.getItem('accessToken');

	return (await axiosInstance.post(`/api/requests/create`, data)).data as ClaimResponse;
};

export const mapRequestToChat = async (requestId: string, chatId: string) => {
	return await axiosInstance.post(`/api/requests/chat-mapping/${chatId}/${requestId}`);
};

export const getReqList = async () => {
	return (await axiosInstance.get(`/api/requests/list`)).data as Request[];
};

export const getReqDetail = async (args: QueryFunctionContext) => {
	const req_id = args.queryKey[1];
	return (await axiosInstance.get(`/api/requests/${req_id}`)).data as Request;
};

export const deleteReq = async (req_id: string) => {
	return await axiosInstance.post(`/api/requests/delete/${req_id}`);
};

export const getClassification = async (args: QueryFunctionContext) => {
	const req_id = args.queryKey[1];
	return (await axiosInstance.get(`/api/requests/classification/${req_id}`)).data;
};

export const getRiskScore = async (args: QueryFunctionContext) => {
	const req_id = args.queryKey[1];
	return (await axiosInstance.get(`/api/requests/risk_score/${req_id}`)).data as {
		request_id: string;
		risk_score: number;
	};
};

export const listAttachements = async (args: QueryFunctionContext) => {
	const req_id = args.queryKey[1];
	return (await axiosInstance.get(`/api/requests/attachments-list/${req_id}`)).data;
};

export const getAttachement = async (data: { attachment_id: string }) => {
 
	const res = await axiosInstance.get(`/api/requests/attachments/${data.attachment_id}`);
	return {
		file: res.data,
		fileName: res.headers['content-disposition']?.split('filename=')[1]?.replace(/"/g, '')
	};
};

export const getStatisticsResult = async (args: QueryFunctionContext) => {
	const req_id = args.queryKey[1];
	return (await axiosInstance.get(`/api/requests/statistics/${req_id}`))
		.data as PolicyStatisticData;
};

export const getClaimData = async (args: QueryFunctionContext) => {
	const req_id = args.queryKey[1];
	return (await axiosInstance.get(`/api/requests/risk_info/${req_id}`)).data as RiskInfo;
};
export const getDeclineData = async (args: QueryFunctionContext) => {
	const req_id = args.queryKey[1];

	return (await axiosInstance.get(`/api/requests/request/${req_id}`)).data as DeclineValues;
};

export const getCoverageRecommendation = async (args: QueryFunctionContext) => {
	const req_id = args.queryKey[1];
	return (await axiosInstance.get(`/api/requests/coverage_recommendation/${req_id}`))
		.data as CoverageRecommendation;
};

export const getExtractionData = async (args: QueryFunctionContext) => {
	const req_id = args.queryKey[1];
	return (await axiosInstance.get(`/api/requests/extraction/${req_id}`)).data;
};

export const getInAppetiteStatus = async (args: QueryFunctionContext) => {
	const req_id = args.queryKey[1];
	return (await axiosInstance.get(`/api/requests/appetite_info/${req_id}`)).data as AppetiteInfo;
};

export const getStatusReason = async (args: QueryFunctionContext) => {
	const req_id = args.queryKey[1];
	return (await axiosInstance.get(`/api/requests/status_reason/${req_id}`)).data as {
		status_reason: string;
	};
};
export const getperils = async (args: QueryFunctionContext) => {
	const req_id = args.queryKey[1];
	return (await axiosInstance.get(`/api/requests/perils/${req_id}`)).data as {
		coverage_items: CoverageItem[];
	};
};
// /api/requests/perils/{request_id:uuid}
export const getCusDetail = async (args: QueryFunctionContext) => {
	const cus_id = args.queryKey[1];
	return (await axiosInstance.get(`/api/customers/${cus_id}`)).data as {
		id: string;
		name: string;
		address: string;
		requests: Request[];
	};
};

export const getCusList = async () => {
	return (await axiosInstance.get(`/api/customers/list`)).data as {
		id: string;
		name: string;
		address: string;
		requests: Request[];
	}[];
};

export const reSubmitReq = async (data: { req_id: string; data: FormData }) => {
	return await axiosInstance.post(`/api/requests/missing/${data.req_id}`, data.data);
};
