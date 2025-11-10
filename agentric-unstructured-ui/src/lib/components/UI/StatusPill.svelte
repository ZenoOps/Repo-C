<script lang="ts">
	import { getStatusReason } from '$lib/query/requests';
	import { APPETITESTATUS, RequestSubmissionStatus } from '$lib/types/request';
	import Icon from '@iconify/svelte';
	import { createQuery } from '@tanstack/svelte-query';
	type CombinedStatus = APPETITESTATUS | RequestSubmissionStatus;
	let {
		status,
		icon,
		req_id
	}: { status: CombinedStatus; icon?: string; description?: string; req_id?: string } = $props();

	let showTooltip = $state(false);

	let statusReason = $derived(
		createQuery({
			queryKey: ['status_reason', req_id],
			queryFn: getStatusReason,
			enabled: false
		})
	);

	let statusTypeMap: Record<CombinedStatus, 'pending' | 'danger' | 'success' | 'secondary'> =
		$derived({
			[RequestSubmissionStatus.PROCESSING]: 'pending',
			[RequestSubmissionStatus.INREVIEW]: 'pending',
			[RequestSubmissionStatus.ERROR]: 'danger',
			[RequestSubmissionStatus.CLOSED]: 'danger',
			[APPETITESTATUS.PAID]: 'success',
			[APPETITESTATUS.PARTIAL_PAYMENT]: 'success',
			[APPETITESTATUS.DECLINED]: 'danger',
			[APPETITESTATUS.MISSING]: 'danger',
			[APPETITESTATUS.APPROVED]: 'success',
			[APPETITESTATUS.DECIDING]: 'pending',
			[APPETITESTATUS.DUPLICATE]: 'pending',
			[APPETITESTATUS.PENDING]: 'pending'
		});

	let borderColorstyle = $state('border-yellow-600 bg-yellow-50 text-yellow-600');
	$effect(() => {
		switch (statusTypeMap[status]) {
			case 'danger':
				borderColorstyle = 'border-red-600 bg-red-50 text-red-600';
				break;
			case 'success':
				borderColorstyle = 'border-green-600 bg-green-50 text-green-600';
				break;
			case 'secondary':
				borderColorstyle = 'border-gray-600 bg-gray-50 text-gray-600';
		}
	});
</script>

<div
	role="button"
	onkeydown={() => {}}
	tabindex="0"
	class="relative flex w-fit {$statusReason.data
		? 'cursor-pointer'
		: ''} items-center rounded-full border {borderColorstyle} px-2 py-1 text-xs font-semibold"
	onmouseenter={() => {
		showTooltip = true;
		if (!$statusReason.data && req_id) {
			$statusReason.refetch();
		}
	}}
	onmouseleave={() => (showTooltip = false)}
>
	<span>{status}</span>
	{#if icon}
		<Icon {icon} class="inline h-4 w-4" />
	{/if}

	{#if showTooltip && $statusReason.data}
		<div
			class="border-primary/30 text-primary absolute top-0 -right-2 z-40 min-w-80 translate-x-full -translate-y-2 rounded border bg-gray-50 px-2 py-1.5 text-start text-xs shadow-md"
		>
			{$statusReason.data.status_reason ?? 'No description'}
		</div>
	{/if}
</div>
