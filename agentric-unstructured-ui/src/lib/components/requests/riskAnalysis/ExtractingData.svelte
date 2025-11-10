<script lang="ts">
	import { page } from '$app/state';
	import { convertSnaketoFormatedCase } from '$lib/components/helper';
	import Error from '$lib/components/UI/Error.svelte';
	import Loading from '$lib/components/UI/Loading.svelte';
	import MultiTable from '$lib/components/UI/MultiTable.svelte';
	import { getExtractionData } from '$lib/query/requests';
	import { createQuery } from '@tanstack/svelte-query';
	let { mandatoriesField = [] }: { mandatoriesField: string[] } = $props();
	let classificationQuery = $derived(
		createQuery({
			queryKey: ['classi', page.params.req_id],
			queryFn: getExtractionData
		})
	);
</script>

<div class=" w-full rounded-b-lg transition-transform duration-300">
	<div class="border border-gray-200 bg-white">
		{#if $classificationQuery.isLoading}
			<div class="py-6">
				<Loading />
			</div>
		{:else if $classificationQuery.isError}
			<div class="py-6">
				<Error errMessage={'Extracted Data for this request is not founded.'} />
			</div>
		{:else if $classificationQuery.data}
			<div class="divide-y divide-gray-200 border-gray-200">
				{#each Object.entries($classificationQuery.data) as [key, value]}
					<p class="w-full py-3 pl-4 text-lg font-bold break-words text-gray-800">
						{convertSnaketoFormatedCase(key)}
						{#if mandatoriesField.includes(key)}
							<span class="text-grey-600">*</span>
						{/if}
					</p>

					<div class="w-full divide-y divide-slate-200">
						{#if Array.isArray(value)}
							<MultiTable data={value} />
						{:else if typeof value === 'object' && value !== null}
							{#each Object.entries(value) as [subKey, subVal]}
								{#if Array.isArray(subVal)}
									<div
										class="flex {subVal.length && typeof subVal[0] === 'object'
											? 'flex-col'
											: 'divide flex-row divide-x divide-gray-200 '}"
									>
										<p
											class="px-4 {subVal.length && typeof subVal[0] === 'object'
												? 'pt-3'
												: 'w-1/3 max-w-[200px]  py-4'} font-semibold break-words text-gray-800"
										>
											{convertSnaketoFormatedCase(subKey)}
											{#if mandatoriesField.includes(subKey)}
												<span class="text-grey-600">*</span>
											{/if}
										</p>
										<MultiTable data={subVal} />
									</div>
								{:else if typeof subVal === 'object' && subVal !== null}
									<div class="flex h-full flex-col divide-gray-200">
										<p class="w-full py-3 pl-4 font-medium break-words text-gray-800">
											{convertSnaketoFormatedCase(subKey)}
											{#if mandatoriesField.includes(subKey)}
												<span class="text-grey-600">*</span>
											{/if}
										</p>
										<div
											class="flex h-full flex-col divide-y divide-gray-200 border-t border-slate-200"
										>
											{#each Object.entries(subVal) as [lastKey, lastVal]}
												{#if Array.isArray(lastVal)}
													<div
														class="flex {lastVal.length && typeof lastVal[0] === 'object'
															? 'flex-col'
															: 'divide flex-row divide-x divide-gray-200'}"
													>
														<p
															class="px-4 {lastVal.length && typeof lastVal[0] === 'object'
																? 'pt-3'
																: 'w-1/3 max-w-[200px] py-4'} font-semibold break-words text-gray-800"
														>
															{convertSnaketoFormatedCase(lastKey)}
															{#if mandatoriesField.includes(lastKey)}
																<span class="text-grey-600">*</span>
															{/if}
														</p>
														<MultiTable data={lastVal} />
													</div>
												{:else if typeof lastVal === 'object' && lastVal !== null}
													<div class="flex h-full w-full flex-col divide-gray-200">
														<p class="w-full py-3 pl-4 font-medium break-words text-gray-800">
															{convertSnaketoFormatedCase(lastKey)}
															{#if mandatoriesField.includes(lastKey)}
																<span class="text-grey-600">*</span>
															{/if}
														</p>
														<div
															class="flex h-full w-full flex-col divide-y divide-gray-200 border-t border-slate-200"
														>
															{#each Object.entries(lastVal) as [finalKey, finalVal]}
																<div class="flex divide-x divide-slate-200">
																	<p
																		class="w-1/3 max-w-[200px] p-4 py-3 font-medium break-words text-gray-800"
																	>
																		{convertSnaketoFormatedCase(finalKey)}
																		{#if mandatoriesField.includes(finalKey)}
																			<span class="text-grey-600">*</span>
																		{/if}
																	</p>
																	<p
																		class="w-2/3 max-w-[500px] px-4 py-3 font-medium break-words {!finalVal
																			? 'text-slate-500'
																			: 'text-slate-500'}"
																	>
																		{#if typeof finalVal === 'boolean' && finalVal !== null}
																			{finalVal}
																		{:else}
																			{finalVal || 'Missing'}
																		{/if}
																	</p>
																</div>
															{/each}
														</div>
													</div>
												{:else}
													<div class="flex divide-x divide-slate-200">
														<p
															class="w-1/3 max-w-[200px] px-4 py-3 font-medium break-words text-gray-800"
														>
															{convertSnaketoFormatedCase(lastKey)}
															{#if mandatoriesField.includes(lastKey)}
																<span class="text-grey-600">*</span>
															{/if}
														</p>
														<p
															class="w-2/3 max-w-[500px] px-4 py-3 font-medium break-words {!lastVal
																? 'text-slate-500'
																: 'text-slate-500'}"
														>
															{#if typeof lastVal === 'boolean' && lastVal !== null}
																{lastVal}
															{:else}
																{lastVal || 'Missing'}
															{/if}
														</p>
													</div>
												{/if}
											{/each}
										</div>
									</div>
								{:else}
									<div class="flex h-full w-full divide-x divide-gray-200">
										<p class="w-1/3 max-w-[200px] px-4 py-3 font-medium break-words text-gray-800">
											{convertSnaketoFormatedCase(subKey)}
											{#if mandatoriesField.includes(subKey)}
												<span class="text-grey-600">*</span>
											{/if}
										</p>
										<p
											class="w-2/3 max-w-[500px] px-4 py-3 font-medium break-words {!subVal
												? 'text-slate-500'
												: 'text-slate-500'}"
										>
											{#if typeof subVal === 'boolean' && subVal !== null}
												{subVal}
											{:else}
												{subVal || 'Missing'}
											{/if}
										</p>
									</div>
								{/if}
							{/each}
						{:else}
							<div class="flex h-full w-full divide-x divide-gray-200">
								<p class="w-1/3 max-w-[200px] px-4 py-3 font-medium break-words text-gray-800">
									{convertSnaketoFormatedCase(key)}
									{#if mandatoriesField.includes(key)}
										<span class="text-grey-600">*</span>
									{/if}
								</p>
								<p
									class="w-2/3 max-w-[500px] px-4 py-3 font-medium break-words {!value
										? 'text-slate-500'
										: 'text-slate-500'} "
								>
									{#if typeof value === 'boolean' && value !== null}
										{value}
									{:else}
										{value || 'Missing'}
									{/if}
								</p>
							</div>
						{/if}
					</div>
				{/each}
			</div>
		{/if}
	</div>
</div>
