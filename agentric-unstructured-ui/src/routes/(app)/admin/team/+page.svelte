<script lang="ts">
	import TeamForm from '$lib/components/form/TeamForm.svelte';
	import UserForm from '$lib/components/form/UserForm.svelte';
	import Empty from '$lib/components/UI/Empty.svelte';
	import Modal from '$lib/components/UI/Modal.svelte';
	import Pagination from '$lib/components/UI/Pagination.svelte';
	import Table from '$lib/components/UI/Table.svelte';
	import { getUserList, deleteUser, getTeams } from '$lib/query/auth';
	import { openOverlay } from '$lib/store/openOverlay';
	import type { UserProfile } from '$lib/types/user';
	import Icon from '@iconify/svelte';
	import { createMutation, createQuery, useQueryClient } from '@tanstack/svelte-query';
	import toast from 'svelte-french-toast';

	const client = useQueryClient();

	let currentTeamPage = $state(1);

	let getTeamsQuery = $derived(
		createQuery({
			queryKey: ['teams', currentTeamPage],
			queryFn: getTeams
		})
	);

	let teams = $derived($getTeamsQuery.data ? $getTeamsQuery.data.items : []);
</script>

<div class="flex h-full min-h-0 w-full flex-col space-y-4 overflow-hidden px-4 py-4">
	<!-- </div> -->

	<!-- <div class="mt-18 h-full w-0.5 border-r border-dashed border-neutral-200"></div> -->
	<div class="flex h-full w-full flex-col space-y-4">
		<div class="flex items-center justify-between">
			<h4 class="text-primary text-2xl font-semibold">Organization List</h4>

			<button
				class="bg-primary border-primary rounded-lg border px-4 py-1.5 text-white"
				onclick={() => openOverlay.set({ name: 'createTeam', id: '' })}>Create Organization</button
			>
		</div>
		<hr class="border-dashed border-neutral-200" />

		<div class="flex-1 overflow-auto">
			{#if teams.length === 0}
				<div class="flex h-full w-full items-center justify-center">
					<Empty />
				</div>
			{:else}<Table headColums={['Name', 'description', 'members', 'Action']}>
					{#each teams as team}
						<tr>
							<td class="p-3 text-slate-700">
								<a
									href={`/admin/team/${team.id}`}
									class="text-primary font-semibold hover:underline">{team.name}</a
								>
							</td>
							<td class="p-3 text-slate-700">{team.description || '----'}</td>
							<td class="p-3 text-slate-700">{team.members.length}</td>
							<td class="p-3 text-slate-700">
								<button class="cursor-pointer" onclick={() => {}}
									><Icon icon="ph:dots-three-bold" width="24" height="24" /></button
								></td
							>
						</tr>
					{/each}
				</Table>
			{/if}
		</div>
		<hr class="border-dashed border-neutral-200" />
		<Pagination
			bind:currentPage={currentTeamPage}
			limit={$getTeamsQuery.data?.limit ?? 20}
			offset={$getTeamsQuery.data?.offset ?? 0}
			total={$getTeamsQuery.data?.total ?? 0}
		/>
	</div>
</div>

{#if $openOverlay.name === 'createTeam'}
	<Modal>
		<TeamForm />
	</Modal>
{/if}
