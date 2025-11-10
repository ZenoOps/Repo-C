<script lang="ts">
	import { browser } from '$app/environment';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import RequestForm from '$lib/components/form/RequestForm.svelte';
	import { formatDate, formatTime, toTitleCase } from '$lib/components/helper';
	import Button from '$lib/components/UI/Button.svelte';
	import Empty from '$lib/components/UI/Empty.svelte';
	import Error from '$lib/components/UI/Error.svelte';
	import Loading from '$lib/components/UI/Loading.svelte';
	import Modal from '$lib/components/UI/Modal.svelte';
	import RequestStatsCard from '$lib/components/UI/RequestStatsCard.svelte';
	import StatusPill from '$lib/components/UI/StatusPill.svelte';
	import Table from '$lib/components/UI/Table.svelte';
	import { deleteReq, getCusList, getReqList } from '$lib/query/requests';
	import { openOverlay } from '$lib/store/openOverlay';
	import { APPETITESTATUS, RequestSubmissionStatus } from '$lib/types/request';
	import type { User } from '$lib/types/user';
	import Icon from '@iconify/svelte';
	import { createMutation, createQuery, useQueryClient } from '@tanstack/svelte-query';
	import toast from 'svelte-french-toast';

	let reqListQuery = createQuery({
		queryKey: ['list_req_home'],
		queryFn: getReqList,
		refetchInterval: (data) => {
			const hasPending = data.state.data?.some((req) => req.status === APPETITESTATUS.PENDING);
			return hasPending ? 5000 : false;
		}
	});

	let userListQuery = $derived(
		createQuery({
			queryKey: ['user_list'],
			queryFn: getCusList
		})
	);
	let statsCardsData = $derived([
		{
			title: 'New Requests',
			value: $reqListQuery.data
				? $reqListQuery.data.filter(
						(ite) => ite.submission_status === RequestSubmissionStatus.PROCESSING
					).length
				: 0,
			description: `${
				$reqListQuery.data
					? $reqListQuery.data.filter(
							(ite) =>
								ite.submission_status === RequestSubmissionStatus.PROCESSING &&
								ite.created_at.split('T')[0] === new Date().toISOString().split('T')[0]
						).length
					: 'NO'
			} new requests `
		},
		{
			title: 'Open Requests',
			value: $reqListQuery.data
				? $reqListQuery.data.filter(
						(ite) =>
							ite.status !== APPETITESTATUS.PAID ||
							ite.submission_status === RequestSubmissionStatus.CLOSED
					).length
				: 0,
			description: `${
				$reqListQuery.data
					? $reqListQuery.data.filter(
							(ite) =>
								ite.status !== APPETITESTATUS.PAID &&
								ite.created_at.split('T')[0] === new Date().toISOString().split('T')[0]
						).length
					: 'NO'
			} open requests `
		},
		{
			title: 'In Progress',
			value: $reqListQuery.data
				? $reqListQuery.data.filter(
						(ite) =>
							ite.submission_status === RequestSubmissionStatus.INREVIEW ||
							ite.status === APPETITESTATUS.PENDING
					).length
				: 0,
			description: `${($reqListQuery.data?.filter((ite) => ite.status === APPETITESTATUS.PENDING).length || 0) + ($reqListQuery.data?.filter((ite) => ite.submission_status === RequestSubmissionStatus.INREVIEW).length || 0)} pending requests `
		},
		{
			title: 'Closed Requests',
			value: ` ${$reqListQuery.data?.filter((ite) => ite.status === APPETITESTATUS.PAID).length || 0}`,
			description: 'No closed requests '
		}
	]);
	const client = useQueryClient();
	let deleteReqMutation = $derived(
		createMutation({
			mutationFn: deleteReq,
			onSuccess: async () => {
				await client.invalidateQueries({ queryKey: ['list_req_home'] });
				toast.success('Request deleted successfully!');
			},
			onError: (e) => {
				toast.error('Failed to delete the Request.');
			}
		})
	);
	let user: User = $derived(browser ? JSON.parse(localStorage.getItem('user') ?? '') : null);
</script>

<div class="flex h-auto flex-col space-y-8 px-4 py-6">
	<div class="w-full flex flex-col md:flex-row md:justify-between space-y-4 md:space-y-0">
		<h4 class="text-lg md:text-2xl font-bold">
			Claims Dashboard {!user.isSuperuser
				? `for ${user.teamName ? toTitleCase(user.teamName).replace('_', ' ') : '----'}`
				: ''}
		</h4>
		{#if !user.isSuperuser}
			<div>
				<Button onclick={() => openOverlay.set({ name: 'create_req', id: '' })}
					>Create Request</Button
				>
			</div>
		{/if}
	</div>
	<div class="grid lg:grid-cols-4 grid-cols-2 gap-4 lg:gap-6">
		{#each statsCardsData as ite}
			<RequestStatsCard title={ite.title} description={ite.description} value={ite.value} />
		{/each}
	</div>

	<h4 class="text-2xl font-bold">Recent Requests</h4>

	<div class="relative">
		<div class="w-full overflow-x-auto absolute">
			{#if $reqListQuery.isLoading}
				<Loading />
			{:else if $reqListQuery.isError}
				<Error />
			{:else if $reqListQuery.data}
				{#if $reqListQuery.data.length}
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
						{#each $reqListQuery.data as req}
							<tr class="border-b border-slate-200 text-slate-800">
								<th class="px-2 py-4 text-start font-semibold">
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
								<th class="px-2 py-4 text-start font-normal">{req.unique_identifier || ''}</th>
								<th class="px-2 py-4 text-start font-normal">{req.type_of_claim || 'N/A'}</th>
								<th class="px-2 py-4 text-start font-normal"
									>{req.claim_amount}</th
								>
								<th class="px-2 py-4 text-start font-normal">{req.approved_amount || '0'}</th>
	
								<th class="px-2 py-4 text-start font-normal">
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
								<th class="px-2 py-4 text-start font-normal">
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
	
								<th class="px-2 py-4 text-start font-medium text-nowrap"
									>{formatDate(req.created_at)} / {formatTime(req.created_at)}
								</th>
								<th class="px-2 py-4 text-start font-medium text-nowrap">
									{req.created_by || ''}
								</th>
								<th class="text-primary px-2 py-4 text-start text-sm font-bold">
									<div class="flex h-full items-center justify-start space-x-2">
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

{#if $openOverlay.name === 'create_req'}
	<Modal>
		<RequestForm />
	</Modal>
{/if}
