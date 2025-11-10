<script lang="ts">
	import StatusPill from '$lib/components/UI/StatusPill.svelte';
	import type { Request } from '$lib/types/request';
	import Icon from '@iconify/svelte';
	import { slide } from 'svelte/transition';
	import { formatDate } from '../helper';
	let isOpen = $state();
	let {
		request
	}: {
		request: Request;
	} = $props();
</script>

<div class=" ">
	<button
		onclick={() => (isOpen = !isOpen)}
		class="flex w-full cursor-pointer items-center justify-between"
	>
		<div class="flex items-center justify-center space-x-3">
			<span class="text-sm font-bold"> {[request.unique_identifier]}</span>
			<StatusPill status={request.status} req_id={request.id} />
			<StatusPill status={request.submission_status} />
		</div>
	</button>
</div>
