<script lang="ts">
	import { createQuery } from '@tanstack/svelte-query';
	import { page } from '$app/state';
	import { getStatisticsResult } from '$lib/query/requests';
	import { convertSnaketoFormatedCase } from '$lib/components/helper';
	import Error from '$lib/components/UI/Error.svelte';

	let { data, isloading = $bindable(false), isError } = $props();
	let getStatisticsResultsQuery = $derived(
		createQuery({
			queryKey: ['extraction_results', page.params.req_id],
			queryFn: getStatisticsResult,
			enabled: false
		})
	);

	let quoteSummary = $derived(
		$getStatisticsResultsQuery.data
			? Object.fromEntries(
					Object.entries($getStatisticsResultsQuery.data).filter(
						([key, value]) => key === 'highlevel_info'
					)
				)
			: {}
	) as {
		highlevel_info: {
			premium_amount: number;
			coverage_amount: number;
			deductible_amounts: Record<string, unknown>;
		};
	};
</script>

<div class="h-full space-y-4 rounded-lg border border-slate-200 p-4">
	<div
		class="border-t-secondary flex flex-col space-y-2 rounded-lg border border-t-4 border-slate-200 p-4"
	>
		{#if isError}
			<Error />
		{:else if data}
			<span class="text-lg font-semibold"
				>Premium Amount :
				{#if data.premium_amount}
					<span class="px-2 text-base text-slate-500">$ {data.premium_amount}</span>
				{:else}
					N/A
				{/if}
			</span>
		{/if}
		{#if isError}
			<Error />
		{:else}
			<span class="text-lg font-semibold"
				>Coverage Amount :
				{#if data.maximum_coverage_amount}
					<span class="px-2 text-base text-slate-500"> ${data.maximum_coverage_amount}</span>
				{:else}
					N/A
				{/if}
				{#if $getStatisticsResultsQuery.isError}
					<Error />
				{:else if quoteSummary.highlevel_info && quoteSummary.highlevel_info.deductible_amounts}
					<div class="space-y-2">
						<h3 class="text-lg font-semibold">Deductible Amounts:</h3>
						<div class="divide-y divide-slate-200 border border-slate-200">
							{#each Object.entries(quoteSummary.highlevel_info.deductible_amounts) as [key, value]}
								<div class="flex h-full w-full divide-x divide-gray-200">
									<p
										class="w-1/3 max-w-[300px] min-w-[200px] px-4 py-3 font-medium break-all text-gray-800"
									>
										{convertSnaketoFormatedCase(key)}
									</p>
									<p
										class="w-2/3 max-w-[500px] min-w-[300px] px-4 py-3 font-medium break-all {value !==
											0 && !value
											? ''
											: ''}"
									>
										{value || 0}
									</p>
								</div>
							{/each}
						</div>
					</div>
				{/if}
			</span>
		{/if}
	</div>

	<!-- Claim Decision Narrative Section -->
	{#if isError}
		<Error />
	{:else}
		<div class="space-y-4">
			<h2 class="border-b border-dashed border-slate-200 pb-2 text-2xl font-bold text-gray-900">
				Claim Decision Narrative
			</h2>

			<div>
				<h4 class="text-lg font-semibold text-gray-800">Case Summary</h4>
				<p class="mt-2 leading-relaxed text-gray-700">{data.description || 'N/A'}</p>
			</div>
			<div>
				<h4 class="text-lg font-semibold text-gray-800">Payment Reason</h4>
				<p class="mt-2 leading-relaxed text-gray-700">{data.payment_reason || 'N/A'}</p>
			</div>

			<div>
				<h4 class="text-lg font-semibold text-gray-800">Decision Reason</h4>
				<p class="mt-2 leading-relaxed text-gray-700">{data.decision_reason || 'N/A'}</p>
			</div>
		</div>
	{/if}
</div>
