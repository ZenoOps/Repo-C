<script lang="ts">
	import * as pdfjsLib from 'pdfjs-dist';
	import pdfWorker from 'pdfjs-dist/build/pdf.worker.min?url';
	import { env } from '$env/dynamic/public';
	import { page } from '$app/stores';
	import { slide } from 'svelte/transition';
	import Icon from '@iconify/svelte';
	import { createQuery } from '@tanstack/svelte-query';
	import { listAttachements } from '$lib/query/requests';
	import { derived, writable } from 'svelte/store';
	import Error from '../UI/Error.svelte';
	import Loading from '../UI/Loading.svelte';
	import Empty from '../UI/Empty.svelte';

	pdfjsLib.GlobalWorkerOptions.workerSrc = pdfWorker;

	const req_id = derived(page, ($page) => $page.params.req_id);

	const openAttachmentId = writable<string | null>(null);

	let fileUrl: string | null = $state(null);

	let listAttachQuery = createQuery({
		queryKey: ['attachments-list', $req_id],
		queryFn: listAttachements
	});

	const handleData = async (attachmentId: string) => {
		openAttachmentId.update((current) => (current === attachmentId ? null : attachmentId));

		const res = await fetch(`${env.PUBLIC_API_URL}/api/requests/attachments/${attachmentId}`, {
			method: 'GET',
			headers: {
				Authorization: `Bearer ${localStorage.getItem('accessToken')}`
			}
		});

		if (!res.ok) {
			alert('Fail to fetch');
			return;
		}

		const blob = await res.blob();
		fileUrl = URL.createObjectURL(blob);
	};
</script>

<div class="flex w-full flex-col space-y-6 rounded-md">
	{#if $listAttachQuery.isLoading}
		<Loading />
	{:else if $listAttachQuery.isError}
		<Error />
	{:else if $listAttachQuery.data}
		{#if $listAttachQuery.data.length}
			{#each $listAttachQuery.data as attachment}
				<div class="flex flex-col overflow-hidden rounded-md shadow-md">
					<button
						class="flex w-full items-center justify-start space-x-4 bg-white px-4 py-4.5 text-left hover:bg-gray-100"
						onclick={() => handleData(attachment.id)}
					>
						<span transition:slide={{ duration: 300 }}>
							<Icon
								icon={$openAttachmentId === attachment.id ? 'oui:arrow-up' : 'oui:arrow-right'}
								width="20"
								height="20"
							/>
						</span>
						<span class="font-normal">{attachment.file_name}</span>
					</button>

					{#if $openAttachmentId === attachment.id}
						<div class="h-[500px] w-full overflow-auto border-slate-200">
							{#if fileUrl && attachment.file_name.split('.').pop() === 'pdf'}
								<iframe
									src={fileUrl}
									class="h-full w-full"
									frameborder="0"
									title={attachment.file_name}
								></iframe>
							{:else if fileUrl && ['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(attachment.file_name
										.split('.')
										.pop())}
								<img src={fileUrl} alt="attachment" class="h-full w-full object-contain" />
							{/if}
						</div>
					{/if}
				</div>
			{/each}
		{:else}
			<Empty />
		{/if}
	{/if}
</div>
