<script lang="ts">
	import Icon from '@iconify/svelte';
	import { extractBase64FromMime, extractHeaders } from '../helper';
	import { openOverlay } from '$lib/store/openOverlay';
	import { createQuery } from '@tanstack/svelte-query';
	import { getEmail } from '$lib/query/chat';
	import { page } from '$app/state';
	import Button from '../UI/Button.svelte';

	let emailQuery = $derived(
		createQuery({
			queryKey: ['email_tem', page.params.req_id],
			queryFn: getEmail
		})
	);

	let mailString = $derived($emailQuery.data?.email || '');
	let headers = $derived(extractHeaders(mailString));
	let base64 = $derived(extractBase64FromMime(mailString));
	let html = $derived(base64 ? atob(base64) : '');
</script>

<div class="space-y-6 px-8 py-6">
	<div class="flex justify-between">
		<h2 class="flex items-center space-x-4 text-slate-800">
			<Icon icon="carbon:email" width="20" height="20" /><span class="text-xl font-bold"
				>Request Additional Information</span
			>
		</h2>
		<!-- <Button class="" onclick={() => openOverlay.set({ name: '', id: '' })}
			><Icon icon="codex:cross" width="24" height="24" /></Button
		> -->
	</div>
	<div class="space-y-4">
		<p class="flex justify-between">
			<span class="font-semibold">To:</span> <span class="text-end">{headers['To']}</span>
		</p>
		<p class="flex justify-between">
			<span class="font-semibold">Subject:</span>
			<span class="max-w-96 text-end">{headers['Subject']}</span>
		</p>
	</div>
	<h6 class="font-semibold">Email Body:</h6>
	{@html html}
	<div class="flex justify-end space-x-2.5">
		<Button
			class="border-primary text-primary flex cursor-pointer items-center space-x-2.5 rounded-md border px-6 py-2.5"
			><Icon icon="line-md:edit-twotone" width="20" height="20" /><span>Edit</span></Button
		>
		<Button
			class="border-primary text-primary cursor-pointer rounded-md border px-6 py-2.5"
			onclick={() => openOverlay.set({ name: '', id: '' })}>Cancel</Button
		>
		<Button
			class="bg-primary border-primary flex cursor-pointer items-center space-x-2.5 rounded-md border px-6 py-2.5 text-white"
			><Icon icon="mynaui:send-solid" width="20" height="20" /> <span>Email</span></Button
		>
	</div>
</div>
