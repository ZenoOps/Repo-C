<script lang="ts">
	import { goto } from '$app/navigation';
	import { formatDate, formatTime } from '$lib/components/helper';
	import Button from '$lib/components/UI/Button.svelte';
	import Empty from '$lib/components/UI/Empty.svelte';
	import Error from '$lib/components/UI/Error.svelte';
	import FilterButton from '$lib/components/UI/FilterButton.svelte';
	import Loading from '$lib/components/UI/Loading.svelte';
	import StatusPill from '$lib/components/UI/StatusPill.svelte';
	import Table from '$lib/components/UI/Table.svelte';
	import { deleteReq, getCusList, getReqList } from '$lib/query/requests';
	import { APPETITESTATUS, RequestSubmissionStatus } from '$lib/types/request';
	import Icon from '@iconify/svelte';
	import { createMutation, createQuery, useQueryClient } from '@tanstack/svelte-query';

	let reqListReqQuery = $derived(
		createQuery({
			queryKey: ['req_list'],
			queryFn: getReqList,
			refetchInterval: (data) => {
				const hasPending = data.state.data?.some((req) => req.status === APPETITESTATUS.PENDING);
				return hasPending ? 5000 : false;
			}
		})
	);

	let filterstatus: APPETITESTATUS[] = $state([]);

	let userListQuery = $derived(
		createQuery({
			queryKey: ['user_list'],
			queryFn: getCusList
		})
	);

	let tabs = $derived([
		{
			title: 'All',
			count: $reqListReqQuery.data ? $reqListReqQuery.data.length : 0,
			value: $reqListReqQuery.data ? $reqListReqQuery.data : []
		},
		{
			title: 'New Requests',
			count: $reqListReqQuery.data
				? $reqListReqQuery.data.filter(
						(ite) => ite.submission_status === RequestSubmissionStatus.PROCESSING
					).length
				: 0,
			value: $reqListReqQuery.data
				? $reqListReqQuery.data.filter(
						(ite) => ite.submission_status === RequestSubmissionStatus.PROCESSING
					)
				: []
		},
		{
			title: 'Open Requests',
			count: $reqListReqQuery.data
				? $reqListReqQuery.data.filter((ite) => ite.status !== APPETITESTATUS.PAID).length
				: 0,
			value: $reqListReqQuery.data
				? $reqListReqQuery.data.filter((ite) => ite.status !== APPETITESTATUS.PAID)
				: []
		},
		{
			title: 'In Progress',
			count: $reqListReqQuery.data
				? $reqListReqQuery.data.filter(
						(ite) =>
							ite.submission_status === RequestSubmissionStatus.INREVIEW ||
							ite.status === APPETITESTATUS.PENDING
					).length
				: 0,
			value: $reqListReqQuery.data
				? $reqListReqQuery.data.filter(
						(ite) =>
							ite.submission_status === RequestSubmissionStatus.INREVIEW ||
							ite.status === APPETITESTATUS.PENDING
					)
				: []
		},
		{
			title: 'Closed Requests',
			count: ` ${$reqListReqQuery.data?.filter((ite) => ite.status === APPETITESTATUS.PAID || ite.submission_status === RequestSubmissionStatus.CLOSED).length || 0}`,
			value: $reqListReqQuery.data
				? $reqListReqQuery.data?.filter((ite) => ite.status === APPETITESTATUS.PAID)
				: []
		}
	]);
	let openedTab = $state('All');

	let data = $derived(tabs.find((ite) => ite.title === openedTab));

	const client = useQueryClient();
	let deleteReqMutation = $derived(
		createMutation({
			mutationFn: deleteReq,
			onSuccess: async () => {
				await client.invalidateQueries({ queryKey: ['list_req_home'] });
			},
			onError: (e) => {
				console.log(e);
			}
		})
	);
</script>

<div class="flex h-auto w-full flex-col space-y-8 px-4 py-6">
	<h4 class="text-2xl font-bold">Claim Requests</h4>
	<div class="flex items-center justify-between">
		<div class="hidden space-x-4 lg:flex">
			{#each tabs as ite}
				<Button
					class="flex cursor-pointer space-x-2 rounded-md px-3 py-2 {openedTab === ite.title
						? 'text-secondary bg-primary '
						: 'hover:bg-gray-200'}"
					onclick={() => (openedTab = ite.title)}
				>
					<span class="text-nowrap">{ite.title} </span>
					<span
						class="bg-secondary text-primary flex h-6 w-6 items-center justify-center rounded-full border p-1 text-xs font-medium"
						>{ite.count}</span
					>
				</Button>
			{/each}
		</div>
		<FilterButton bind:selected={filterstatus} />
	</div>

	<div class=" relative">
		<div class="w-full overflow-x-auto absolute">
			{#if $reqListReqQuery.isLoading}
				<Loading />
			{:else if $reqListReqQuery.isError}
				<Error />
			{:else if $reqListReqQuery.data && data}
				{#if data?.value.length > 0}
					<Table
						headColums={[
							'Case Number',
							'Custom Identifier',
							'Type of Claim',
							'Claim Amount',
							'Approve Amount',
							'Decision',
							'Status',
							'Date Submitted',
							'Created By',
							''
						]}
					>
						{#each data.value.filter( (ite) => (filterstatus.length ? filterstatus.includes(ite.status) : ite) ) as req}
							<tr class="border-b border-slate-200 text-slate-800">
								<th class="px-2 py-3 text-start font-semibold">
									<button
										onclick={() => {
											goto(`/agent/requests/${req.id}`);
										}}
										disabled={req.submission_status === RequestSubmissionStatus.PROCESSING ||
											RequestSubmissionStatus.ERROR == req.submission_status}
										class={!(
											req.submission_status === RequestSubmissionStatus.PROCESSING ||
											RequestSubmissionStatus.ERROR === req.submission_status
										)
											? 'text-primary hover:underline'
											: 'text-gray-300'}
									>
										{req.request_number || 'N/A'}
									</button>
								</th>
								<th class="px-3 py-4 text-start font-normal">{req.unique_identifier || ''}</th>
								<th class="px-3 py-4 text-start font-normal">{req.type_of_claim || 'N/A'}</th>
								<th class="px-3 py-4 text-start font-normal"
									>{req.requested_reimbursement_amount
										? req.requested_reimbursement_amount
										: req.claim_amount}</th
								>
								<th class="px-3 py-4 text-start font-normal">{req.premium_amount || '0'}</th>
	
								<th class="px-3 py-4 text-start font-normal">
									{#if req.status === APPETITESTATUS.PENDING}
										<div
											class="flex w-fit items-center space-x-2 rounded-full border bg-yellow-50 px-2 py-1 text-xs font-semibold text-yellow-600"
										>
											<Icon icon="eos-icons:bubble-loading" width="14" height="14" />
											<span class="text-xs"> Processing</span>
										</div>
									{:else}
										<StatusPill status={req.status} req_id={req.id} />
									{/if}
								</th>
								<th class="px-3 py-4 text-start font-normal">
									{#if req.submission_status === RequestSubmissionStatus.PROCESSING}
										<div
											class="flex w-fit items-center space-x-2 rounded-full border bg-yellow-50 px-2 py-1 text-xs font-semibold text-yellow-600"
										>
											<Icon icon="eos-icons:bubble-loading" width="14" height="14" />
											<span class="text-xs"> Processing</span>
										</div>
									{:else}
										<StatusPill status={req.submission_status} req_id={req.id} />
									{/if}
								</th>
	
								<th class="px-3 py-4 text-start font-medium text-nowrap"
									>{formatDate(req.created_at)} / {formatTime(req.created_at)}
								</th>
								<th class="px-3 py-4 text-start font-medium text-nowrap">
									{req.created_by || ''}
								</th>
								<th class="text-primary px-3 py-4 text-start text-sm font-bold">
									<div class="flex h-full items-center justify-start space-x-2">
										<!-- {#if APPETITESTATUS.PENDING !== req.status && RequestSubmissionStatus.ERROR !== req.submission_status}
										<a href="/agent/requests/{req.id}" class="underline">Review</a>
									{#if APPETITESTATUS.PENDING === req.status || RequestSubmissionStatus.PROCESSING === req.submission_status}
										<p>In Progress</p>
									{/if} -->
										<button class="cursor-pointer" onclick={() => $deleteReqMutation.mutate(req.id)}
											><Icon icon="line-md:trash" width="20" height="20" style="color: red" /></button
										>
									</div>
								</th>
							</tr>
						{/each}
					</Table>
				{:else}
					<Empty />
				{/if}
			{/if}
		</div>
	</div>
</div>
