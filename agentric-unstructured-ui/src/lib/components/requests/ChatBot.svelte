<script lang="ts">
	import Icon from '@iconify/svelte';
	import SvelteMarkdown from 'svelte-markdown';

	import { page } from '$app/state';
	import { slide } from 'svelte/transition';

	import { AgentRole, type StreamChat, type ConversationItem } from '$lib/types/chat';
	import { env } from '$env/dynamic/public';
	import { onMount, tick } from 'svelte';
	import DataTable from '../UI/DataTable.svelte';
	import { browser } from '$app/environment';
	import { openOverlay } from '$lib/store/openOverlay';

	import { createQuery, useQueryClient } from '@tanstack/svelte-query';
	import { getChatMessageHistory } from '$lib/query/chat';
	import People from '$lib/dummy/People.svelte';

	import Modal from '../UI/Modal.svelte';
	import DragAndDrop from '../UI/DragAndDrop.svelte';
	import { getTime } from '../helper';
	import { isReviewOpen } from '$lib/store/uiStore';

	let {
		worktype = 'initial',
		conversations = $bindable([])
	}: {
		worktype?: string;
		conversations?: ConversationItem[];
	} = $props();

	const client = useQueryClient();

	let scrollAnchor: HTMLDivElement | null = $state(null);

	let user = $derived(browser ? JSON.parse(localStorage.getItem('user') || '{}') : {});

	let isOpenThought = $state(false);
	let userText = $state('');
	let isLoading = $state(false);
	let isLoadingThoughts = $state(false);
	let isUploading = $state(false);
	let uploadedIndexs: number[] = $state([]);
	let attachmentIds: string[] = $state([]);
	let isMounted = $state(false);
	let previewEmail = $state('');
	let uploadURL = $state('');
	let uploadeMethod = $state('');
	let lastChatId: string | null = null;

	let fileList: FileList | [] = $state([]);
	let historyFile: { file_name: string; file_size: string } | null = $state(null);

	let lastWorktype = $derived([] as string[]);
	let quotationAccepted = $state(false);
	let closeQuatation = $state(false);
	let textareaElement: HTMLTextAreaElement | null = $state(null);

	let displayTypes = [
		{
			name: 'table',
			snippet: tableSnippet
		},
		{
			name: 'tool_call',
			snippet: textSnippet
		},
		{
			name: 'tool_result',
			snippet: textSnippet
		},
		{
			name: 'text',
			snippet: textSnippet
		},
		{
			name: 'button',
			snippet: btnSnippet
		},

		{
			name: 'three-btns',
			snippet: threeBtnSnippet
		},
		{
			name: 'upload',
			snippet: fileUploadSnippet
		}
	];

	let getChatHistoryQuery = $derived(
		createQuery({
			queryKey: ['chat_history_message', page.params.chatId],
			queryFn: getChatMessageHistory,
			enabled: page.params.chatId ? true : false
		})
	);

	function pushMessage(msg: Omit<ConversationItem, 'time'>) {
		conversations.push({ ...msg, time: getTime() });
		conversations = [...conversations];
	}

	function safeJSONParse(line: string): any | null {
		try {
			return JSON.parse(line);
		} catch (err) {
			console.error('Invalid JSON chunk:', line, err);
			pushMessage({
				message: `Error: invalid JSON chunk`,
				role: AgentRole.ZURICH_ANALYST_AGENT,
				type: 'text',
				displayType: 'text'
			});
			return null;
		}
	}

	function resizeTextarea() {
		if (!textareaElement) return;

		textareaElement.style.height = 'auto';

		const scrollHeight = textareaElement.scrollHeight;

		if (scrollHeight <= 80) {
			textareaElement.style.height = `${scrollHeight}px`;
			textareaElement.style.overflowY = 'hidden';
		} else {
			textareaElement.style.height = `${80}px`;
			textareaElement.style.overflowY = 'auto';
		}
	}

	function updateLastMessage(message: string, loading = false, append = true) {
		let lastIndex = conversations.length - 1;
		if (lastIndex < 0) return;

		let last = conversations[lastIndex];
		if (!last || last.type !== 'text') return;

		if (append) {
			last.message = (last.message || '') + message;
		} else {
			last.message = message;
		}

		last.loading = loading;

		conversations = [...conversations];
	}

	function handleToolResult(
		toolResult: any,
		role: string,
		type: string,
		is_thought_included: boolean,
		thought: string
	) {
		const base = { role, type, time: getTime(), is_thought_included, thought };
		const handlers: Record<string, () => void> = {
			CLASSIFICATION_REQUEST: () =>
				pushMessage({
					...base,
					message: toolResult.results,
					displayType: 'table'
				}),
			DECLINE_REASON: () =>
				pushMessage({
					...base,
					message: toolResult.reason,
					displayType: 'text'
				}),
			SUCCESS: () =>
				pushMessage({
					...base,
					message: toolResult.message,
					displayType: 'text'
				}),
			SCORE: () =>
				pushMessage({
					...base,
					message: [toolResult.scores],
					displayType: 'table'
				}),
			CONFIRMATION: () =>
				pushMessage({
					...base,
					message: toolResult.reason,
					displayType: 'three-btns'
				}),
			EMAIL: () => {
				previewEmail = toolResult.email;
				uploadeMethod = toolResult.method;
				pushMessage({
					...base,
					message: 'Below is the draft of the email I have prepared for you.',
					displayType: 'button'
				});
			},
			CLAIM_FORM: () => {
				uploadURL = toolResult.url;
				uploadeMethod = toolResult.method;
				pushMessage({
					...base,
					message:
						'Perfect! Could you please upload that cancellation email or a screenshot of it here?\n Just tap the button and attach your file.',
					displayType: 'upload'
				});
			},
			FILE: () => {
				historyFile = {
					file_name: toolResult.message.file_name,
					file_size: toolResult.message.file_size
				};
				pushMessage({
					...base,
					type: 'file_his',
					message: historyFile,
					displayType: 'file_show'
				});
			}
		};

		(
			handlers[toolResult.type] ??
			(() =>
				pushMessage({
					...base,
					message: `${toolResult.message || JSON.stringify(toolResult)}`,
					displayType: 'text'
				}))
		)();
	}

	export const userInputStreamChat = async ({
		chatId,
		data,
		onMessage,
		mode = 'stream'
	}: {
		chatId: string;
		mode?: 'stream' | 'workflow';
		data: StreamChat;
		onMessage?: (parsedChunk: any) => void;
	}) => {
		isLoading = true;
		userText = '';
		const url =
			mode === 'workflow'
				? !user.teamId
					? `/api/chats/workflow/${chatId}?step=${worktype}`
					: `/api/requests/workflow/${page.params.req_id}?step=${worktype}`
				: !user.teamId
					? `/api/chats/customer-assistant/stream/${chatId}`
					: `/api/chats/stream/${page.params.req_id}`;

		const option: RequestInit = {
			method: mode === 'workflow' ? 'GET' : 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${localStorage.getItem('accessToken')}`
			},
			body: mode === 'stream' ? JSON.stringify({ message: data.message }) : undefined
		};

		try {
			const response = await fetch(`${env.PUBLIC_API_URL}${url}`, option);
			if (!response.body) {
				updateLastMessage('Error: Could not get response.');
				isLoading = false;
				return null;
			}

			if (!response.ok) {
				// updateLastMessage('Error: Could not get response.');
				isLoading = false;
				pushMessage({
					message: 'Error: Could not get Response due to Server Issue.',
					role:
						user.role === AgentRole.USER
							? AgentRole.ZURICH_CLAIM_AGENT
							: AgentRole.ZURICH_ANALYST_AGENT,
					type: 'error',
					displayType: 'text'
				});
				return null;
			}
			const reader = response.body.getReader();
			const decoder = new TextDecoder('utf-8');
			while (true) {
				const { done, value } = await reader.read();
				if (done) {
					// isLoading = false;
					break;
				}

				const chunk = decoder.decode(value, { stream: true });

				const lines = chunk.split(/(?<=})\s*(?={)/).filter(Boolean);

				for (const line of lines) {
					const parsed = safeJSONParse(line);
					if (!parsed) continue;

					if (parsed.role === 'system') {
						pushMessage({
							message: `System: ${parsed.message}`,
							role: parsed.role,
							type: '',
							displayType: 'text',
							is_thought_included: parsed.message.is_thought_included,
							thought: parsed.message.thought
						});
						continue;
					}

					if (parsed.type === 'tool_call') {
						pushMessage({
							message: parsed.message,
							role: parsed.role,
							type: parsed.type,
							displayType: 'tool_call',
							is_thought_included: parsed.message.is_thought_included,
							thought: parsed.message.thought
						});
						continue;
					}

					if (parsed.type === 'tool_result' || (parsed.type === 'text' && isMounted)) {
						try {
							let toolResult =
								parsed.type === 'text' && isMounted
									? parsed.message
									: typeof parsed.message === 'string'
										? JSON.parse(parsed.message.replace(/```json\n|\n```/g, ''))
										: parsed.message;
							handleToolResult(
								toolResult,
								parsed.role,
								parsed.type,
								parsed.message.is_thought_included,
								parsed.message.thought
							);
						} catch (e) {
							console.error('Error parsing tool_result JSON:', e);
							pushMessage({
								message: parsed.message,
								role: parsed.role,
								type: parsed.type,
								displayType: 'text',
								is_thought_included: parsed.message.is_thought_included,
								thought: parsed.message.thought
							});
						}
						continue;
					}
					if (parsed.type === 'text') {
						const last = conversations[conversations.length - 1];
						const previousType = last?.type;

						if (previousType === 'text' && last?.role === parsed.role) {
							last.message += JSON.stringify(parsed.message);

							conversations = [...conversations];
						} else {
							pushMessage({
								message: parsed.message,
								role: parsed.role,
								type: parsed.type,
								displayType: 'text',
								loading: false,
								is_thought_included: parsed.message.is_thought_included,
								thought: parsed.message.thought
							});
						}
					}

					onMessage?.(parsed);
					openOverlay.set({ name: '', id: '' });
				}
			}
		} catch (e) {
			console.error('Error during stream:', e);
			updateLastMessage('Error: Could not get response.');
		} finally {
			isLoading = false;

			scrollToBottom();
			isMounted = false;
		}

		const last = conversations[conversations.length - 1];
		if (last && last.loading) last.loading = false;

		isMounted = false;
		scrollToBottom();
		const placeholderMsg = conversations.find(
			(c) => c.loading && c.message === 'Generating response...'
		);
		if (placeholderMsg) {
			const index = conversations.indexOf(placeholderMsg);
			conversations.splice(index, 1);
			conversations = [...conversations];
		}
	};

	function parseMessage(msg: string) {
		if (!msg) return '';

		msg = msg?.replace(/```json\n?|```/g, '').trim();

		if (msg.startsWith('{') || msg.startsWith('[')) {
			try {
				return JSON.parse(msg);
			} catch (e) {
				console.warn('Failed to parse JSON message:', e);
				return msg;
			}
		}
		return msg;
	}

	onMount(async () => {
		const chatId = page.params.chatId || page.params.req_id;
		if (!chatId) return;

		if (page.params.chatId) {
			const history = await $getChatHistoryQuery.refetch();
			const hasHistory = (history.data?.length ?? 0) > 0;

			if (!hasHistory) {
				await userInputStreamChat({
					chatId,
					data: { message: 'Please check current request status' },
					mode: 'workflow'
				});
			}
		} else if (page.params.req_id) {
			await userInputStreamChat({
				chatId: page.params.req_id,
				data: { message: 'Please check current request status' },
				mode: 'workflow'
			});
		}
		if ($getChatHistoryQuery.isError) {
			console.error('Error during stream:');
			updateLastMessage('Error: Could not get response.');
		}

		isMounted = true;
		lastWorktype = [...lastWorktype, worktype];
	});

	$effect(() => {
		const chatId = page.params.chatId || page.params.req_id;
		scrollToBottom();
		if (page.params.chatId) {
			const data = $getChatHistoryQuery.data;

			if (data && chatId && chatId !== lastChatId) {
				lastChatId = chatId;
				conversations = [];

				data
					.slice()
					.reverse()
					.forEach((item) => {
						const parsed = parseMessage(item.message);
						if (typeof parsed === 'object') {
							handleToolResult(
								parsed,
								item.role,
								item.type,
								parsed.message.is_thought_included,
								parsed.message.thought
							);
						} else {
							pushMessage({
								message: parsed,
								role: item.role,
								type: item.type,
								displayType: 'text',
								loading: false,
								is_thought_included: parsed.message.is_thought_included,
								thought: parsed.message.thought
							});
						}
					});
			}
			if ($getChatHistoryQuery.isError) {
				console.error('Error during stream:');
				updateLastMessage('Error: Could not get response.');
			}
		}
	});

	let hasStreamed = false;

	$effect(() => {
		if (
			!lastWorktype.includes(worktype) &&
			!isMounted &&
			(page.params.req_id || $getChatHistoryQuery.data?.length === 0) &&
			!hasStreamed
		) {
			isMounted = true;
			hasStreamed = true;
			lastWorktype = [...lastWorktype, worktype];
		}
	});

	// For uploading attachement ids to stream
	let isUploadingDone = $state(false);
	const handleUploadSubmit = async () => {
		isLoading = true;
		isUploadingDone = false;
		let selectedFiles = Array.from(fileList);
		if (selectedFiles.length) {
			conversations.push({
				message: selectedFiles as File[],
				role: AgentRole.USER,
				type: 'file',
				displayType: 'file',
				time: new Date().toLocaleTimeString('en-us', {
					hour: '2-digit',
					minute: '2-digit',
					hour12: true
				})
			});

			isUploadingDone = true;
			openOverlay.set({ name: '', id: '' });
			await userInputStreamChat({
				chatId: page.params.chatId || page.params.req_id,
				data: {
					message: `I HAVE UPLOADED. ${JSON.stringify({ UPLOADED_DOC_IDs: attachmentIds })} ${userText}`
				},

				mode: 'stream'
			});
			isLoading = false;
		}
	};

	// For send string to stream
	const handleSubmit = async () => {
		if (userText) {
			conversations.push({
				message: userText,
				role: AgentRole.USER,
				type: 'text',
				displayType: 'text',
				time: new Date().toLocaleTimeString('en-us', {
					hour: '2-digit',
					minute: '2-digit',
					hour12: true
				})
			});
		}
		tick().then(() => resizeTextarea());
		conversations = [...conversations];
		scrollToBottom();
		await userInputStreamChat({
			chatId: page.params.chatId || page.params.req_id,
			data: {
				message: quotationAccepted ? "update this request's status to PAID" : userText
			},

			mode: 'stream'
		});

		quotationAccepted = false;
		userText = '';

		await client.invalidateQueries({ queryKey: ['req_detail', page.params.req_id] });
		await client.invalidateQueries({ queryKey: ['chat-list'] });
	};

	function scrollToBottom() {
		if (scrollAnchor) {
			requestAnimationFrame(() => {
				scrollAnchor?.scrollIntoView({ behavior: 'smooth', block: 'end' });
			});
		}
	}
	onMount(() => {
		if (browser) {
			resizeTextarea();
		}
	});
</script>

<div
	class="flex {page.params.req_id
		? 'h-full min-h-0'
		: 'h-full max-h-[89vh]'} w-full flex-col justify-center p-4"
	id={page.params.chatId || page.params.req_id}
>
	<div class="max-w-full flex-1 space-y-4 overflow-y-auto">
		{#each conversations as c}
			<div class="flex {c.role === AgentRole.USER ? 'justify-end' : 'justify-start'} ">
				{#if c.role === AgentRole.USER}
					<!-- User input text message -->
					{#if c.type === 'file'}
						<div class="flex max-w-2/3 flex-col items-end space-y-2">
							{#each c.message as File[] as file, i}
								<div
									class="bg-secondary relative flex space-x-2 rounded-lg border border-slate-200 px-3 py-2"
								>
									<p class="flex items-center justify-center rounded-md bg-white px-3 py-2">
										{#if isUploading && !uploadedIndexs.includes(i)}
											<Icon icon="line-md:loading-twotone-loop" width="24" height="24" />
										{:else}
											<Icon icon="ph:file-light" width="16" height="16" class="text-primary" />
										{/if}
									</p>
									<div class="flex flex-col items-start space-y-1">
										<span class="max-w-20 truncate text-sm font-medium text-slate-800"
											>{(file as File).name}</span
										>
										<span class="max-w-20 truncate text-xs text-slate-500"
											>{(file as File).size}</span
										>
									</div>
								</div>
							{/each}
							<span class="text-xs text-slate-500">{c.time}</span>
						</div>
					{:else if c.type === 'file_his'}
						<div
							class="bg-secondary relative flex space-x-2 rounded-lg border border-slate-200 px-3 py-2"
						>
							<p class="flex items-center justify-center rounded-md bg-white px-3 py-2">
								<Icon icon="ph:file-light" width="16" height="16" class="text-primary" />
							</p>
							<div class="flex flex-col items-start space-y-1">
								<span class="max-w-20 truncate text-sm font-medium text-slate-800"
									>{(c.message as { file_name: string; file_size: string }).file_name}</span
								>
								<span class="max-w-20 truncate text-xs text-slate-500"
									>{(c.message as { file_name: string; file_size: string }).file_size}</span
								>
							</div>
						</div>
					{:else}
						<div class="flex max-w-2/3 flex-col items-end space-y-2">
							<p
								class="bg-secondary rounded-xl border border-slate-200 px-4 py-3 text-sm font-medium break-words text-gray-600"
							>
								{c.message}
							</p>
							<span class="text-xs text-slate-500">{c.time}</span>
						</div>
					{/if}
				{:else}
					<!-- Chat bot messages -->

					<div class="w-full pe-24 space-y-2 break-words">
						<div class="flex items-start space-x-4">
							<p
								class="h-fit w-fit rounded-full border border-green-100 bg-green-50 px-1 py-1 text-slate-500"
							>
								<People />
							</p>

							<div class="space-y-2">
								<p class="text-primary text-sm font-semibold">Clara</p>
								{#if c.type === 'error'}
									<p
										class="bg-secondary rounded-xl border border-slate-200 px-4 py-3 text-sm font-medium break-words text-red-600"
									>
										{c.message}
									</p>
								{:else if c.is_thought_included}
									<!-- Thinking Animation -->
									<div class="space-y-2">
										<div class=" rounded-xl border border-slate-100 bg-white shadow-sm">
											<div
												class="flex items-center justify-between border-b border-dotted border-slate-200 px-3 py-2"
											>
												<div class="flex items-center gap-2">
													<Icon
														icon="ph:star-four-duotone"
														width="16"
														height="16"
														class="text-primary "
													/>

													<div class=" bg-secondary flex items-center rounded-sm px-3 py-1">
														<span class="text-xs font-medium text-gray-900">
															{isLoadingThoughts && !isUploading ? 'Thinking...' : 'Thoughts'}
														</span>
														{#if isLoadingThoughts && !isUploading}
															<img
																src="/idea.gif"
																alt="LogoCover"
																class="h-6 w-8 shrink-0 object-contain"
															/>
														{/if}
													</div>
												</div>

												<span
													class="text-primary rounded-full border border-slate-100 px-2 py-1 text-[10px]"
													>Auto</span
												>
											</div>
											{#if isOpenThought && !isLoadingThoughts}
												<div
													class="border-b border-dotted border-slate-200 px-3 py-4"
													transition:slide={{ duration: 300 }}
												>
													{#if c.is_thought_included}
														<SvelteMarkdown source={c.thought as string} options={{ gfm: true }} />
													{/if}
												</div>
											{/if}
											<div class="flex items-center justify-between px-3 py-2 text-xs">
												<span
													class={isLoadingThoughts && !isUploading
														? ' text-primary font-semibold'
														: 'font-medium text-slate-500'}
												>
													{#if isLoadingThoughts && !isUploading}
														Analyzing the Claims...
													{:else if !isOpenThought}
														{c.message}
													{:else}
														Collapse to hide thoughts
													{/if}
												</span>
												<button
													class=" px-1 py-0.5"
													onclick={() => {
														isOpenThought = !isOpenThought;
													}}
												>
													<Icon
														icon={isOpenThought ? 'oui:arrow-up' : 'oui:arrow-down'}
														width="15"
														height="15"
														class={isOpenThought ? 'text-slate-900' : 'text-primary'}
													/>
												</button>
											</div>
										</div>
									</div>
									<!-- Thinking Animation End-->
									<!-- {@render displayTypes.find((ite) => ite.name === c.displayType)?.snippet(c)} -->
								{:else}
									{@render displayTypes.find((ite) => ite.name === c.displayType)?.snippet(c)}
								{/if}
								<span class="text-xs text-slate-500">{c.time}</span>
							</div>
						</div>
					</div>
				{/if}
			</div>
		{/each}
		{#if isLoading && !isUploading}
			<div class="w-fit max-w-4/5 space-y-2 break-words">
				<div class="flex items-start space-x-4">
					<p
						class="h-fit w-fit rounded-full border border-green-100 bg-green-50 px-1 py-1 text-slate-500"
					>
						<People />
					</p>

					<div class="space-y-2">
						<p class="text-primary text-sm font-semibold">Clara</p>

						<div class="flex w-fit rounded-md border border-slate-100 bg-white px-4 py-2 shadow-lg">
							<span class="text-primary text-sm font-medium">Thinking</span><Icon
								icon="eos-icons:three-dots-loading"
								width="24"
								height="24"
								class="text-slate-600"
							/>
						</div>
					</div>
				</div>
			</div>
		{/if}

		<div bind:this={scrollAnchor}></div>
	</div>

	<!-- Text Box section -->

	<form
		class="relative flex w-full items-center space-x-3 rounded-xl border border-slate-100 bg-slate-50 px-4 py-3 shadow-lg"
		onsubmit={handleSubmit}
	>
		<textarea
			bind:this={textareaElement}
			oninput={resizeTextarea}
			rows="1"
			bind:value={userText}
			placeholder={'Ask a question...'}
			class="h-fit flex-1 resize-none appearance-none rounded-lg ring-0 outline-none focus:outline-none {isLoading
				? 'placeholder:text-slate-200'
				: 'placeholder:text-slate-400'} px-2 transition-all duration-100 ease-in-out focus:ring-0 focus:outline-none"
			disabled={isLoading}
			onkeydown={(e) => {
				if (e.key === 'Enter' && !e.shiftKey) {
					e.preventDefault();
					handleSubmit();
				}
			}}
		></textarea>
		{#if isLoading}
			<Icon icon="eos-icons:loading" class="text-primary" width="24" height="24" />
		{:else}
			<button class="bg-primary cursor-pointer rounded-full p-2 text-white" disabled={isLoading}>
				<Icon icon="iconoir:send-solid" width="16" height="16" />
			</button>
		{/if}
	</form>
</div>

<!-- Snippet for all chat types -->

{#snippet threeBtnSnippet(chat: ConversationItem)}
	<div class=" space-y-3 rounded-lg bg-white p-3 text-sm leading-6 text-slate-500">
		<div class="px-2">
			{#if chat.loading}
				<span class="text-gray-500">{@html chat.message || 'Generating response...'}</span>
			{:else}
				<SvelteMarkdown source={chat.message as string} options={{ gfm: true }} />
			{/if}
		</div>
		{#if !closeQuatation}
			<div class="flex space-x-2">
				{#each [{ name: 'full-payment', icon: 'fluent:coin-multiple-16-filled' }, { name: 'partial-payment', icon: 'tabler:coin' }] as item}
					<button
						class="flex cursor-pointer items-center space-x-2.5 rounded-lg border {item.name ==
						'full-payment'
							? 'bg-green-600'
							: 'bg-blue-600'} px-3 py-2 text-slate-50"
						onclick={() => {
							quotationAccepted = true;
							userText = item.name;
							handleSubmit();
							closeQuatation = true;
						}}
						><Icon icon={item.icon} width="20" height="20" />
						<span class="text-sm font-semibold">{item.name}</span></button
					>
				{/each}
			</div>
		{/if}
	</div>
{/snippet}

{#snippet textSnippet(chat: ConversationItem)}
	<div
		class="w-fit rounded-md border border-slate-100 {chat.role === 'system'
			? 'bg-red-50 text-red-500'
			: 'bg-white text-slate-800'} p-3 text-sm leading-6 font-medium shadow-lg"
	>
		{#if chat.loading}
			<span class=" text-sm text-gray-500">{@html chat.message || 'Generating response...'}</span>
		{:else}
			<div class="overflow-auto text-xs break-words whitespace-pre-wrap lg:w-full lg:text-base">
				<SvelteMarkdown
					source={(chat.message as string)
						.toString()
						.replace(/^"(.*)"$/, '$1')
						.replace(/\\n/g, '  \n')}
					options={{ gfm: true }}
				/>
			</div>
		{/if}
	</div>
{/snippet}

{#snippet btnSnippet(chat: ConversationItem)}
	<div
		class=" space-y-3 rounded-lg border border-slate-100 bg-white p-3 text-sm leading-6 text-slate-500 shadow-lg"
	>
		<p>
			{#if chat.loading}
				<span class="text-gray-500">{@html chat.message || 'Generating response...'}</span>
			{:else}
				<SvelteMarkdown source={chat.message as string} options={{ gfm: true }} />
			{/if}
		</p>
		<button
			class="flex cursor-pointer items-center space-x-2 rounded-md border border-green-700 p-1.5 text-green-700"
			onclick={() => {
				openOverlay.set({ name: 'email_preview', id: '' });
			}}
			><Icon icon="bxs:file" width="20" height="20" />
			<span class="font-semibold">Preview Email</span></button
		>
	</div>
{/snippet}

{#snippet fileUploadSnippet(chat: ConversationItem)}
	<div
		class=" space-y-2 rounded-lg border border-slate-100 bg-white p-3 text-sm leading-6 font-semibold text-gray-600 shadow-lg"
	>
		<p>
			{#if chat.loading}
				<span class="text-gray-500">{@html chat.message || 'Generating response...'}</span>
			{:else}
				<SvelteMarkdown source={chat.message as string} options={{ gfm: true }} />
			{/if}
		</p>
		{#if isUploadingDone}
			<div class="flex items-center space-x-1">
				<Icon
					icon="sidekickicons:check-double-20-solid"
					width="16"
					height="16"
					class="text-green-600"
				/>
				<span class="text-sm font-medium text-green-600">Uploaded</span>
			</div>
		{:else}
			<button
				disabled={isLoading}
				class="border-primary text-primary flex w-fit cursor-pointer items-center justify-center space-x-2 rounded-md border px-3 py-1.5"
				onclick={() => {
					openOverlay.set({ name: 'openUpload', id: '' });
				}}
			>
				<Icon icon="mynaui:upload-solid" width="20" height="20" />
				<span class="text-sm font-semibold">Upload Document</span></button
			>
		{/if}
	</div>
	{#if $openOverlay.name === 'openUpload'}
		<Modal>
			<DragAndDrop
				bind:uploadedFiles={fileList}
				onsubmit={handleUploadSubmit}
				bind:isloading={isLoading}
				bind:attachmentIds
				{uploadURL}
				{uploadeMethod}
			/>
		</Modal>
	{/if}
{/snippet}

{#snippet tableSnippet(chat: ConversationItem)}
	<div class="w-full border border-slate-100 bg-white shadow-lg">
		<DataTable
			data={chat.message as object[]}
			title={chat.type === 'SCORE' ? 'Analysis Score' : 'Classification Data'}
		/>
	</div>
{/snippet}
