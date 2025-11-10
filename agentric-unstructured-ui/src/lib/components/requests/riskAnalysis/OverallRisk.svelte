<script lang="ts">
	import { page } from '$app/state';
	import Error from '$lib/components/UI/Error.svelte';
	import Loading from '$lib/components/UI/Loading.svelte';
	import { getRiskScore } from '$lib/query/requests';
	import { APPETITESTATUS } from '$lib/types/request';
	import { createQuery } from '@tanstack/svelte-query';
	let { score, title, leftvalue, rightvalue, showStatusPill = true } = $props();
	const riskStatusCalculate = (score: number) => {
		if (title === 'In Appetite Score') {
			if (score === 100) {
				return {
					status: 'Excellent',
					color: 'green'
				};
			} else if (score >= 85) {
				return {
					status: 'Strong',
					color: 'yellow'
				};
			} else if (score >= 60) {
				return {
					status: 'Acceptable',
					color: 'orange'
				};
			}
			return {
				status: 'Un-Appetite',
				color: 'red'
			};
		}

		if (title === 'Overall Risk') {
			if (score <= 20)
				return {
					status: 'Low',
					color: 'green'
				};
			if (score >= 80)
				return {
					status: 'High',
					color: 'red'
				};
			return {
				status: 'Moderate',
				color: 'orange'
			};
		}
	};

	let riskStatus = $derived(
		riskStatusCalculate(score ? score : 0) as {
			status: string;
			color: string;
		}
	);
</script>

<div class="border-secondary w-full space-y-4 rounded-lg border border-t-4 bg-white p-4">
	<p class="text-sm font-medium">{title}</p>
	<!-- {#if $riskScoreQuery.isLoading}
		<Loading removeText={true} />
	{:else if $riskScoreQuery.isError}
		<Error />
	{:else if $riskScoreQuery.data} -->
	<div class="flex items-center justify-between">
		<span class="text-xl font-bold">{score}/100</span>
		<!-- {#if showStatusPill} -->
		<span
			class="rounded-full px-2 py-1 text-xs font-bold"
			class:bg-red-50={riskStatus.color === 'red'}
			class:bg-orange-50={riskStatus.color === 'orange'}
			class:bg-green-50={riskStatus.color === 'green'}
			class:text-red-500={riskStatus.color === 'red'}
			class:text-orange-500={riskStatus.color === 'orange'}
			class:text-green-500={riskStatus.color === 'green'}>{riskStatus.status} Risk</span
		>
		<!-- {/if} -->
	</div>
	<div class="space-y-2">
		<div class="h-2 w-full rounded-full border border-neutral-200 bg-neutral-100">
			<div
				class="h-2 rounded-full"
				class:bg-red-500={riskStatus.color === 'red'}
				class:bg-orange-500={riskStatus.color === 'orange'}
				class:bg-green-500={riskStatus.color === 'green'}
				class:bg-yellow-500={riskStatus.color === 'yellow'}
				style="width: {score}%"
			></div>
		</div>

		<div class="flex items-center justify-between text-xs text-slate-500">
			<span>{leftvalue}</span> <span>{rightvalue}</span>
		</div>
	</div>
	<!-- {:else}
		<p class="text-sm font-semibold text-red-600">Missing</p>
	{/if} -->
</div>
