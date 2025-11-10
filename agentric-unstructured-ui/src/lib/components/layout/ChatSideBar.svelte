<script lang="ts">
	import type { Chat } from '$lib/types/chat';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { get } from 'svelte/store';
	import logo from '$lib/assets/logo.png';
	import Modal from '$lib/components/UI/Modal.svelte';
	import { getChatList, deleteChat, createChat } from '$lib/query/chat';
	import { createQuery, createMutation, useQueryClient } from '@tanstack/svelte-query';
	import Icon from '@iconify/svelte';
	import { browser } from '$app/environment';
	import { openOverlay } from '$lib/store/openOverlay';
	import { v4 as uuidv4 } from 'uuid';
	import Button from '../UI/Button.svelte';
	import SearchBar from '../UI/SearchBar.svelte';

	const uuid = uuidv4();
	const client = useQueryClient();

	let filter = $state('');
	let showDelete = $state(false);
	let deleteChatId: string | null = $state(null);
	let user = $derived(browser ? JSON.parse(localStorage.getItem('user') ?? '') : null);
	let listChatsQuery = $derived(
		createQuery({
			queryFn: getChatList,
			queryKey: ['chat-list'],
			refetchOnWindowFocus: false,
			refetchOnMount: true,
			enabled: !user.teamId && !user.isSuperuser ? true : false
		})
	);

	const startNewChat = async () => {
		const randomUUID = uuidv4();
		location.replace('/chat/' + randomUUID);
		await client.invalidateQueries({ queryKey: ['chat-list'] });
	};

	const deleteChatMutation = createMutation({
		mutationFn: deleteChat,
		onSuccess: () => {
			showDelete = false;
			client.invalidateQueries({
				queryKey: ['chat-list']
			});
			deleteChatId = null;

			if (deleteChatId === page.params.chatId) {
				goto('/');
			}
		},
		onError: () => {
			showDelete = false;
		}
	});
	let chats = $derived($listChatsQuery.data ? $listChatsQuery.data : []);

	$effect(() => {
		if (chats.length > 0) {
			localStorage.setItem('isChatHad', 'true');
		} else {
			localStorage.removeItem('isChatHad');
		}
	});
</script>

{#if $openOverlay.name === 'open_delete'}
	<Modal bind:show={showDelete}>
		<div class="w-[22rem] rounded-xl bg-white p-6 shadow-lg">
			<h2 class="text-lg font-semibold text-gray-800">Delete this chat?</h2>
			<p class="mt-1 text-sm text-gray-500">This action cannot be undone.</p>

			<div class="mt-5 flex justify-end gap-4 text-sm">
				<Button
					onclick={() => (showDelete = false)}
					class="font-semibold text-gray-700 hover:text-gray-900 disabled:opacity-50"
					disabled={$deleteChatMutation.isPending}
				>
					Cancel
				</Button>
				<Button
					onclick={() => {
						if (deleteChatId) $deleteChatMutation.mutate({ chatId: deleteChatId });
					}}
					class="rounded-lg bg-red-500 px-4 py-2 font-semibold text-white hover:bg-red-700 disabled:opacity-50"
					disabled={$deleteChatMutation.isPending}
				>
					Delete
				</Button>
			</div>
		</div>
	</Modal>
{/if}
{#if page.url.pathname === '/' || page.url.pathname.startsWith('/chat')}
	<nav class=" flex w-full flex-col bg-white lg:h-screen lg:max-w-xs">
		<div class="flex items-center justify-between px-4 py-4">
			<img src={logo} alt="Cover-More Logo" class="h-7" />
			<Button
				class="bg-primary-600 bg-primary hover:bg-primary-700 flex h-8 w-8 cursor-pointer items-center justify-center rounded-lg text-white"
				onclick={startNewChat}
			>
				<Icon icon="bitcoin-icons:plus-filled" width="20" height="20" />
			</Button>
		</div>

		{#if page.url.pathname === '/'}
			<SearchBar bind:value={filter} />
		{/if}
		<!-- Chat List -->
		<div
			class="flex-1 overflow-y-auto px-4 {page.url.pathname.startsWith('/chat')
				? 'hidden lg:block'
				: ''}"
		>
			<div
				class="flex w-full items-center justify-between border-b border-dashed border-slate-200 py-2"
			>
				<h3 class="text-sm font-semibold text-gray-500">Chats</h3>
				<span>
					<Icon icon="prime:bell" width="16" height="16" />
				</span>
			</div>

			{#if chats.length > 0}
				<div class="flex flex-col space-y-1 py-3">
					{#each chats as chat}
						<div
							class="{page.params.chatId === chat.id
								? 'border-primary rounded-none border-l'
								: ''} group relative flex items-center justify-between rounded-lg px-3 py-3 hover:bg-gray-100"
						>
							<Button
								class="block flex-grow cursor-pointer truncate text-start text-sm font-medium text-gray-800"
								onclick={() => {
									goto(`/chat/${chat.id}`);
								}}
							>
								{chat.title}
							</Button>

							<Button
								class="invisible cursor-pointer text-xs text-gray-400 group-hover:visible hover:text-red-500"
								onclick={(event: any) => {
									event.stopPropagation();
									event.preventDefault();
									showDelete = true;
									openOverlay.set({ name: 'open_delete', id: '' });
									deleteChatId = chat.id;
								}}
							>
								Delete
							</Button>
						</div>
					{/each}
				</div>
			{:else}
				<p class="mt-6 text-center text-sm text-gray-400">No chat found</p>
			{/if}
		</div>
	</nav>
{/if}
