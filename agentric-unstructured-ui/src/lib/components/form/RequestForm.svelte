<script lang="ts">
	import Icon from '@iconify/svelte';
	import FileUpload from '../UI/FileUpload.svelte';
	import { openOverlay } from '$lib/store/openOverlay';
	import { createMutation, useQueryClient } from '@tanstack/svelte-query';
	import { createClaim } from '$lib/query/chat';
	import toast from 'svelte-french-toast';
	import { agentCreateChatClaim, agentuploadClaim, deleteChat } from '$lib/query/chat';

	import { v4 as uuidv4 } from 'uuid';
	import { onMount, tick } from 'svelte';
	import Modal from '../UI/Modal.svelte';
	import { browser } from '$app/environment';
	import Button from '../UI/Button.svelte';
	import Input from '../UI/Input.svelte';

	let uniqueId: string | null = $state(null);
	const client = useQueryClient();

	let uuid = uuidv4();
	let ramdom_chatid = $state('');

	onMount(() => {
		ramdom_chatid = uuid;
	});
	let isError = $state(false);

	let createReqMutation = createMutation({
		mutationFn: createClaim,
		onSuccess: () => {
			openOverlay.set({ name: '', id: '' });
			client.invalidateQueries({ queryKey: ['list_req_home'] });
			toast.success('File are uploaded successfully and Request is now created');
		},
		onError: (e) => {
			console.log(e);
			toast.error(e.message);
			isError = true;
		}
	});

	let scrollContainer: HTMLDivElement | null = $state(null);
	let scrollAtStart = $state(true);
	let scrollAtEnd = $state(false);
	let canScroll = $state(false);

	function checkScroll() {
		if (!scrollContainer) return;
		const { scrollWidth, clientWidth } = scrollContainer;
		canScroll = scrollWidth > clientWidth + 1;
		handleScroll();
	}

	function handleScroll() {
		if (scrollContainer) {
			const { scrollLeft, scrollWidth, clientWidth } = scrollContainer;
			scrollAtStart = scrollLeft <= 0;
			scrollAtEnd = scrollLeft + clientWidth >= scrollWidth - 5;
		}
	}

	onMount(() => {
		checkScroll();
		if (scrollContainer && browser) {
			window.addEventListener('resize', checkScroll);
		}
		return () => window.removeEventListener('resize', checkScroll);
	});

	$effect(() => {
		if (scrollContainer && browser) {
			checkScroll();
			window.addEventListener('resize', checkScroll);
		}
	});

	let deleteChatMutation = createMutation({
		mutationFn: deleteChat,
		onSuccess: () => {
			openOverlay.set({ name: '', id: '' });
			client.invalidateQueries({ queryKey: ['list_req_home'] });
		},
		onError: (e) => {
			console.log(e);
			toast.error(e.message);
			isError = true;
		}
	});

	let selectedFilesPolicy: File[] | [] = $state([]);
	let uploadedIndexsPolicy: number[] = $state([]);
	let isUploading = $state(false);
	let policyUploaded = $state(false);
	let notoutsideclose = $state(true);

	const handleUploadPolict = async (e: Event) => {
		const target = e.target as HTMLInputElement;
		let files = target.files as FileList | [];

		selectedFilesPolicy = Array.from(files);
		isUploading = true;
		try {
			let index = 0;
			for (const file of selectedFilesPolicy) {
				const formData = new FormData();
				let attachmentId = '';
				formData.append('files', file);
				attachmentId = await agentuploadClaim({
					data: formData,
					chat_id: ramdom_chatid
				});
				uploadedIndexsPolicy = [...uploadedIndexsPolicy, index];
				index++;
			}
		} catch (e) {
			isUploading = false;
			toast.error('Failed to upload File.');
		} finally {
			isUploading = false;
			policyUploaded = true;
		}
	};

	const handleCreateReq = () => {
		let formadata = new FormData();
		if (policyUploaded) {
			if (uniqueId) {
				formadata.append('unique_identifier', uniqueId);
			}
			$createReqMutation.mutate({chat_id: ramdom_chatid, uniqueId: formadata});
		}
	};
</script>

<div class="min-w-[400px] space-y-2 border border-slate-200 p-1">
	<div class="bg-primary flex items-center justify-between rounded-t-md p-4 text-white">
		<h1 class="text-xl font-semibold">Create request</h1>
		<Button
			class="cursor-pointer"
			onclick={() => {
				if (policyUploaded) {
					openOverlay.set({ name: 'create_req', id: ramdom_chatid });
				} else {
					openOverlay.set({ name: '', id: '' });
				}
			}}
		>
			<Icon icon="basil:cross-outline" width="24" height="24" />
		</Button>
	</div>
	<div class="flex flex-col space-y-4 px-4 py-4">
		<p class="text-sm text-slate-500">Pls upload evidence files that support your claim</p>
		<!-- <FileUpload label="" required={true} disabled={false} bind:vlaue={files} /> -->
		<FileUpload
			label=""
			isMultiple={true}
			required={true}
			disabled={false}
			onChangeAddFunction={handleUploadPolict}
		/>
		{#if selectedFilesPolicy.length}
			<div class=" flex h-20 w-full max-w-[600px] items-center space-x-2">
				{#if canScroll && !scrollAtStart}
					<Button
						type="button"
						class="z-10 hover:bg-slate-100"
						onclick={() => {
							if (scrollContainer) {
								scrollContainer.scrollBy({ left: -200, behavior: 'smooth' });
							}
						}}
					>
						<Icon icon="mdi:chevron-left" width="20" height="20" />
					</Button>
				{/if}

				<div
					bind:this={scrollContainer}
					onscroll={handleScroll}
					class="relative flex h-full w-full flex-1 space-x-2 overflow-x-auto scroll-smooth py-2"
				>
					{#each selectedFilesPolicy as file, i}
						<div
							class="bg-secondary relative flex h-full shrink-0 space-x-2 rounded-lg border border-slate-200 px-3 py-2"
						>
							<p class="flex h-full items-center justify-center rounded-md bg-white px-3 py-1">
								{#if isUploading && !uploadedIndexsPolicy.includes(i)}
									<Icon icon="line-md:loading-twotone-loop" width="24" height="24" />
								{:else}
									<Icon icon="ph:file-light" width="16" height="16" class="text-primary" />
								{/if}
							</p>
							<div class="flex h-full flex-col items-start space-y-1">
								<p class="h-full max-w-20 truncate text-sm font-medium text-slate-800">
									{file.name}
								</p>
								<p class="h-full max-w-20 truncate text-xs text-slate-500">{file.size}</p>
							</div>
							<Button
								class="absolute -top-2 -right-2 cursor-pointer"
								type="button"
								onclick={() => {
									selectedFilesPolicy = selectedFilesPolicy.filter((ite) => ite !== file);
									tick().then(checkScroll);
								}}
							>
								<Icon icon="mdi:cross-circle" width="24" height="24" class="text-slate-400" />
							</Button>
						</div>
					{/each}
				</div>

				{#if canScroll && !scrollAtEnd}
					<Button
						type="button"
						class="z-10 p-2 hover:bg-slate-100"
						onclick={() => {
							if (scrollContainer) {
								scrollContainer.scrollBy({ left: 200, behavior: 'smooth' });
							}
						}}
					>
						<Icon icon="mdi:chevron-right" width="20" height="20" />
					</Button>
				{/if}
			</div>
		{/if}
		{#if isError}
			<div class="flex items-center space-x-1 text-red-400">
				<Icon icon="fluent:warning-12-filled" width="18" height="18 " />
				<small class="font-semibold">Failed to create the Request.</small>
			</div>
		{/if}
		<hr class="border-dashed border-slate-200" />
		<form>
			<div>
				<label for="claim_number" class="mb-2 block text-sm font-normal text-slate-900">
					Custom Identifier <span class=" text-xs text-slate-500">(Optional)</span>
				</label>
				<Input
					type="text"
					bind:value={uniqueId}
					id="claim_number"
					placeholder="Please enter custom identifier"
					required
				/>
			</div>
		</form>
	</div>
	<div class=" border-secondary flex justify-end space-x-4 border-t pt-2 pb-1 text-white">
		<Button
			class="text-primary cursor-pointer underline"
			onclick={() => {
				if (policyUploaded) {
					openOverlay.set({ name: 'create_req', id: ramdom_chatid });
				} else {
					openOverlay.set({ name: '', id: '' });
				}
			}}>Cancel</Button
		>
		<div>
			<Button
			onclick={handleCreateReq}
		>
			{#if $createReqMutation.isPending}
				<Icon icon="line-md:loading-twotone-loop" width="24" height="24" class="mx-4" />
			{:else}
				<span>Create</span>
			{/if}
		</Button>
		</div>
	</div>
</div>
{#if $openOverlay.id}
	<Modal {notoutsideclose}>
		<div class="border-primary space-y-4 border bg-white p-4">
			<p class="text-primary text-lg font-semibold">Are You Sure to cancel this Process?</p>
			<div class="flex items-center justify-end space-x-2">
				<Button
					class="text-primary border-primary cursor-pointer rounded-lg border px-4 py-1.5"
					type="button"
					onclick={() => openOverlay.set({ name: 'create_req', id: '' })}>No</Button
				>
				<Button
					class="cursor-pointer rounded-lg border border-red-400 bg-red-400 px-4 py-1.5 text-white"
					type="button"
					onclick={() => {
						$deleteChatMutation.mutate({ chatId: ramdom_chatid });
					}}>Yes</Button
				>
			</div>
		</div>
	</Modal>
{/if}
