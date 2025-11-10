import { env } from '$env/dynamic/public';
import type { Chat, ChatMessage, StreamChat } from '$lib/types/chat';
import type { QueryFunctionContext } from '@tanstack/svelte-query';
import axios from 'axios';
import axiosInstance from './axiosInstance';

export const getChatID = async (args: QueryFunctionContext) => {
	const req_id = args.queryKey[1];
	return (await axios.get(`${env.PUBLIC_API_URL}/api/chats/chats/requests/${req_id}`)).data as {
		chat_id: string;
	};
};

export const getChatList = async () => {
	return (await axiosInstance.get(`${env.PUBLIC_API_URL}/api/chats/list`)).data as Chat[];
};

export const updateChatInfo = async (data: { chat_id: string; request_id: string }) => {
	return await axiosInstance.post(`${env.PUBLIC_API_URL}/api/requests/update-chat-info`, data);
};

export const getMessages = async (args: QueryFunctionContext) => {
	const chat_id = args.queryKey[1];
	return (await axios.get(`${env.PUBLIC_API_URL}/api/chats/messages/${chat_id}`))
		.data as ChatMessage[];
};

export const userInputStreamChat = async (data: { req_id: string; data: StreamChat }) => {
	const token = localStorage.getItem('accessToken');

	const response = await fetch(`${env.PUBLIC_API_URL}/api/chats/stream/${data.req_id}`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			message: data.data.message
		})
	});

	if (!response.body) {
		console.error('No stream in response.');
		return;
	}

	const reader = response.body.getReader();
	const decoder = new TextDecoder('utf-8');

	let fullText = '';

	while (true) {
		const { done, value } = await reader.read();
		if (done) break;

		const chunk = decoder.decode(value, { stream: true });
		fullText += chunk;
	}
	return fullText as string;
};

export const getInitialWorkflow = async (data: { chatId: string; data: StreamChat }) => {
	const token = localStorage.getItem('accessToken');

	const response = await fetch(`${env.PUBLIC_API_URL}/api/requests/workflow/${data.chatId}`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			message: data.data.message
		})
	});

	if (!response.body) {
		console.error('No stream in response.');
		return;
	}

	const reader = response.body.getReader();
	const decoder = new TextDecoder('utf-8');

	let fullText = '';

	while (true) {
		const { done, value } = await reader.read();
		if (done) break;

		const chunk = decoder.decode(value, { stream: true });
		fullText += chunk;
	}
	return fullText as string;
};

export const getClassificationStatus = async (args: QueryFunctionContext) => {
	const req_id = args.queryKey[1];
	return (await axios.get(`${env.PUBLIC_API_URL}/api/chats/classification/${req_id}`))
		.data as Request;
};

export const deleteChatHistory = async (request_id: string) => {
	return await axiosInstance.post(`${env.PUBLIC_API_URL}/api/chats/clean/${request_id}`);
};
export const createChat = async (message: string) => {
	return await axiosInstance.post(`${env.PUBLIC_API_URL}/api/chats`, {
		message: message
	});
};
// export const deleteChat = async (chatId: string) => {
// 	return (await axiosInstance.post(`${env.PUBLIC_API_URL}/api/chats/delete/${chatId}`)).data;
// };

export const getEmail = async (arg: QueryFunctionContext) => {
	const req_id = arg.queryKey[1];

	return (await axiosInstance.get(`${env.PUBLIC_API_URL}/api/requests/email/${req_id}`)).data as {
		request_id: string;
		email: string;
	};
};

export const uploadClaimFile = async (data: { data: FormData; url: string; method: string }) => {
	// const token = localStorage.getItem('accessToken');
	return (
		await axiosInstance({
			method: data.method, // or 'get', 'put', 'delete', 'patch', etc.
			url: `${data.url}`,
			headers: {
				'Content-Type': 'multipart/form-data'
			},
			data: data.data
		})
	).data as { attachment_id: string };
};
// api/requests/create-claim

export const createClaim = async (data: { chat_id: string, uniqueId: FormData  }) => {
	// const token = localStorage.getItem('accessToken');
 
	const body =  data.uniqueId ? data.uniqueId : {}
	return (await axiosInstance.post(`${env.PUBLIC_API_URL}/api/chats/${data.chat_id}/create-claim`,body))
		.data as { request_id: string; chat_id: string; claim_document_ids: string[] };
};

export const getChatMessageHistory = async (args: QueryFunctionContext) => {
	const chat_id = args.queryKey[1];
	return (await axiosInstance.get(`${env.PUBLIC_API_URL}/api/chats/chat-messages/${chat_id}`))
		.data as ChatMessage[];
};

export const agentuploadClaim = async (data: { data: FormData; chat_id: string }) => {
	return (
		await axiosInstance.post(
			`${env.PUBLIC_API_URL}/api/chats/${data.chat_id}/submit-claim`,
			data.data
		)
	).data;
};

export const agentCreateChatClaim = async (data: { chat_id: string }) => {
	return (
		await axiosInstance.post(`${env.PUBLIC_API_URL}/api/chats/${data.chat_id}/create-claim`, null)
	).data;
};

export const deleteChat = async (data: { chatId: string }) => {
	return (await axiosInstance.post(`${env.PUBLIC_API_URL}/api/chats/${data.chatId}/delete`)).data;
};
