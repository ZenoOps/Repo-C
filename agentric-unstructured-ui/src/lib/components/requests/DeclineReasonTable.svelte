<script lang="ts">
	import { page } from '$app/state';
	import { getDeclineData } from '$lib/query/requests';
	import { createQuery } from '@tanstack/svelte-query';
	import Loading from '../UI/Loading.svelte';
	import Error from '../UI/Error.svelte';
	import Empty from '../UI/Empty.svelte';
	import { convertSnaketoFormatedCase } from '../helper';

	let deClineStatusQuery = $derived(
		createQuery({
			queryKey: ['decline_Data', page.params.req_id],
			queryFn: getDeclineData
		})
	);
	let declined_rules = $derived(
		$deClineStatusQuery.data
			? Object.entries($deClineStatusQuery.data.decline_rules).map(([key, value]) => {
					let temp = {
						name:
							$deClineStatusQuery.data.is_single_location &&
							['wood_construction', 'knockout_postcodes'].includes(key)
								? ['Single Location Submission', value.criteria]
								: [convertSnaketoFormatedCase(key), value.criteria],
						value: value.value,
						pass: value.pass,
						key: key
					};
					return temp;
				})
			: []
	);
</script>

{#if $deClineStatusQuery.isLoading}
	<Loading />
{:else if $deClineStatusQuery.isError}
	<Error />
{:else if $deClineStatusQuery.data}
	{#if Object.keys($deClineStatusQuery.data).length === 0}
		<Empty />
	{:else}
		<table class="w-full table-auto border-collapse bg-white">
			<thead>
				<tr class="bg-secondary divide-x divide-slate-300 border border-slate-200">
					<th class="px-4 py-4">Name and Criteria</th>
					<th class="px-4 py-4">Value</th>
					<th class="px-4 py-4">Pass</th>
				</tr>
			</thead>
			<tbody>
				{#each $deClineStatusQuery.data.is_single_location ? declined_rules : declined_rules.filter((ite) => !['wood_construction', 'knockout_postcodes'].includes(ite.key)) as item}
					<tr class="divide-x divide-slate-200 border border-slate-200 text-center text-slate-500">
						<td class="flex max-w-80 flex-col space-y-2 p-4">
							<span class="font-semibold text-slate-800">({item.name[0]})</span>
							<span> {item.name[1]}</span>
						</td>
						<td class="p-4">{item.value || 'N/A'}</td>
						<td class="p-4 {item.pass === true ? 'text-green-600' : 'text-red-600'} min-w-40"
							>{item.pass}</td
						>
					</tr>
				{/each}
				{#if $deClineStatusQuery.data.is_single_location === false}
					<tr class="divide-x divide-slate-200 border border-slate-200 text-center text-slate-500">
						<td colspan="2" class="text- px-4 py-4 font-semibold text-slate-800"
							>Single Location Submission</td
						>
						<td class="px-4 py-4 text-blue-500">{$deClineStatusQuery.data.is_single_location}</td>
					</tr>
				{/if}
				<!-- <tr class="divide-x divide-slate-200 border border-slate-200 text-center text-slate-500">
					<td class="flex max-w-80 flex-col space-y-2 p-4"
						><span class="font-semibold text-slate-800">Single Location</span>
					</td>
					<td class="p-4">---</td>
					<td
						class="p-4 {$deClineStatusQuery.data.is_single_location === true
							? 'text-green-600'
							: 'text-red-600'} min-w-40">{$deClineStatusQuery.data.is_single_location}</td
					>
				</tr> -->

				<tr class="divide-x divide-slate-200 border border-slate-200 text-center text-slate-500">
					<td colspan="2" class="text- px-4 py-4 font-semibold text-slate-800">Decline Reason</td>
					<td class="px-4 py-4 text-blue-500"
						>{convertSnaketoFormatedCase($deClineStatusQuery.data.decline_reason)}</td
					>
				</tr>
			</tbody>
		</table>
	{/if}
{/if}
