<script lang="ts">
	import { APPETITESTATUS, type Request, type RiskInfo } from '$lib/types/request';

	import OverallRisk from './OverallRisk.svelte';
	import Accordion from '$lib/components/UI/Accordion.svelte';
	import { convertSnaketoFormatedCase } from '$lib/components/helper';
	import Empty from '$lib/components/UI/Empty.svelte';
	import { createQuery } from '@tanstack/svelte-query';
	import { page } from '$app/state';
	import { getInAppetiteStatus } from '$lib/query/requests';
	import SvelteMarkdown from 'svelte-markdown';
	import Loading from '$lib/components/UI/Loading.svelte';
	import Error from '$lib/components/UI/Error.svelte';

	let { data, insurenceData }: { data: Request; insurenceData: RiskInfo } = $props();

	let inAppetiteStatus = $derived(
		createQuery({
			queryKey: ['appetite_score', page.params.req_id],
			queryFn: getInAppetiteStatus,
			enabled:
				data.status === APPETITESTATUS.APPROVED ||
				data.status === APPETITESTATUS.PAID ||
				data?.status === APPETITESTATUS.PARTIAL_PAYMENT
					? true
					: false
		})
	);

	let infoData = $derived([
		{
			title: 'Overall Risk',
			score: insurenceData.risk_score,
			infoTitle: 'Risk Factors',
			info: insurenceData.risk_factors,
			leftvalue: 'Low Risk',
			rightvalue: 'High Risk',
			showStatus: true
		},
		{
			title: 'In Appetite Score',
			score: $inAppetiteStatus.data?.appetite_score || 0,
			infoTitle: 'In Appetite Industry',
			info: $inAppetiteStatus.data?.in_appetite_industries || {},
			leftvalue: 'Un-Appetite',
			rightvalue: 'In Appetite',
			showStatus: false
		}
	]);
</script>

<div class="space-y-4 p-4">
	{#if $inAppetiteStatus.isLoading}
		<Loading />
	{:else if $inAppetiteStatus.isError}
		<Error />
	{:else if $inAppetiteStatus.data}
		{#each infoData as item}
			<div class="space-y-4">
				<OverallRisk
					score={item.score}
					title={item.title}
					leftvalue={item.leftvalue}
					rightvalue={item.rightvalue}
					showStatusPill={item.showStatus}
				/>
				<div class="border border-gray-200">
					{#if Object.keys(item.info).length === 0}
						<div class="p-4">
							<Empty />
						</div>
					{:else}
						<div class="divide-y divide-gray-200 border-y border-gray-200">
							{#each Object.entries(item.info) as [key, value]}
								{#if typeof value === 'object' && value !== null}
									{#each Object.entries(value) as [subKey, subVal]}
										{#if typeof subVal === 'object' && subVal !== null}
											<div class="flex h-full flex-col divide-gray-200">
												<p class="w-full py-3 pl-4 font-medium break-all text-gray-800">
													{subKey === '0'
														? parseInt(subKey) + 1
														: convertSnaketoFormatedCase(subKey)}
												</p>
												<div
													class="flex h-full flex-col divide-x divide-y divide-gray-200 border-t border-slate-200"
												>
													{#each Object.entries(subVal) as [lastKey, lastVal]}
														{#if typeof lastVal === 'object' && lastVal !== null}
															<div class="flex h-full w-full flex-col divide-gray-200">
																<p class="w-full py-3 pl-4 font-medium break-all text-gray-800">
																	{lastKey === '0'
																		? parseInt(lastKey) + 1
																		: convertSnaketoFormatedCase(lastKey)}
																</p>
																<div
																	class="flex h-full w-full flex-col divide-x divide-y divide-gray-200 border-t border-slate-200"
																>
																	{#each Object.entries(lastVal) as [finalKey, finalVal]}
																		<div class="flex divide-x divide-slate-200">
																			<p
																				class="w-1/3 max-w-[300px] min-w-[200px] p-4 py-3 font-medium break-all text-gray-800"
																			>
																				{finalKey === '0'
																					? parseInt(finalKey) + 1
																					: convertSnaketoFormatedCase(finalKey)}
																			</p>
																			<p
																				class="w-2/3 max-w-[500px] min-w-[300px] px-4 py-3 font-medium break-all {finalVal !==
																					0 && !finalVal
																					? 'text-red-600'
																					: ''}"
																			>
																				<SvelteMarkdown
																					source={typeof finalVal === 'string'
																						? finalVal
																						: finalVal === true ||
																							  (typeof finalVal === 'number' && finalVal === 1)
																							? 'Yes'
																							: finalVal === false ||
																								  (typeof finalVal === 'number' && finalVal === 0)
																								? 'No'
																								: typeof finalVal === 'number'
																									? finalVal.toString()
																									: 'N/A'}
																				/>
																			</p>
																		</div>
																	{/each}
																</div>
															</div>
														{:else}
															<div class="flex divide-x divide-slate-200">
																<p
																	class="w-1/3 max-w-[300px] min-w-[200px] px-4 py-3 font-medium break-all text-gray-800"
																>
																	{lastKey === '0'
																		? parseInt(lastKey) + 1
																		: convertSnaketoFormatedCase(lastKey)}
																</p>
																<p
																	class="w-2/3 max-w-[500px] min-w-[300px] px-4 py-3 font-medium break-all {lastVal !==
																		0 && !lastVal
																		? 'text-red-600'
																		: ''}"
																>
																	<SvelteMarkdown
																		source={typeof lastVal === 'string'
																			? lastVal
																			: lastVal === true ||
																				  (typeof lastVal === 'number' && lastVal === 1)
																				? 'Yes'
																				: lastVal === false ||
																					  (typeof lastVal === 'number' && lastVal === 0)
																					? 'No'
																					: typeof lastVal === 'number'
																						? lastVal.toString()
																						: '---'}
																	/>
																</p>
															</div>
														{/if}
													{/each}
												</div>
											</div>
										{:else}
											<div class="flex h-full w-full divide-x divide-gray-200">
												<p
													class="w-1/3 max-w-[300px] min-w-[200px] px-4 py-3 font-medium break-all text-gray-800"
												>
													{subKey === '0'
														? parseInt(subKey) + 1
														: convertSnaketoFormatedCase(subKey)}
												</p>
												<p
													class="w-2/3 max-w-[500px] min-w-[300px] px-4 py-3 font-medium break-all {subVal !==
														0 && !subVal
														? 'text-red-600'
														: ''}"
												>
													<SvelteMarkdown
														source={typeof subVal === 'string'
															? subVal
															: subVal === true || (typeof subVal === 'number' && subVal === 1)
																? 'Yes'
																: subVal === false || (typeof subVal === 'number' && subVal === 0)
																	? 'NO'
																	: typeof subVal === 'number'
																		? subVal.toString()
																		: 'N/A'}
													/>
												</p>
											</div>
										{/if}
									{/each}
								{:else}
									<div class="flex h-full w-full divide-x divide-gray-200">
										<p
											class="w-1/3 max-w-[300px] min-w-[200px] px-4 py-3 font-medium break-all text-gray-800"
										>
											{key === '0' ? parseInt(key) + 1 : convertSnaketoFormatedCase(key)}
										</p>
										<p
											class="w-2/3 max-w-[500px] min-w-[300px] px-4 py-3 font-medium break-all {value !==
												0 && !value
												? 'text-red-600'
												: ''}"
										>
											<SvelteMarkdown
												source={typeof value === 'string'
													? value
													: value === true || value === 1
														? 'Yes'
														: value === false || value === 0
															? 'NO'
															: typeof value === 'number'
																? value.toString()
																: 'N/A'}
											/>
										</p>
									</div>
								{/if}
							{/each}
						</div>
					{/if}
				</div>
			</div>
		{/each}
	{/if}
</div>
