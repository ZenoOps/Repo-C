<script lang="ts">
	import { page } from '$app/state';
	import TeamMemberForm from '$lib/components/form/TeamMemberForm.svelte';
	import MemberCard from '$lib/components/team/MemberCard.svelte';
	import Empty from '$lib/components/UI/Empty.svelte';
	import Error from '$lib/components/UI/Error.svelte';
	import Loading from '$lib/components/UI/Loading.svelte';
	import Modal from '$lib/components/UI/Modal.svelte';

	import { getTeamDetails, updateTeamMemberRole } from '$lib/query/auth';
	import { openOverlay } from '$lib/store/openOverlay';
	import { MemberType, type TeamMember } from '$lib/types/user';
	import Icon from '@iconify/svelte';

	import { createMutation, createQuery, useQueryClient } from '@tanstack/svelte-query';
	import toast from 'svelte-french-toast';

	const client = useQueryClient();

	let getTeamDetailsQuery = $derived(
		createQuery({
			queryKey: ['teamDetails', page.params.team_id],
			queryFn: getTeamDetails
		})
	);

	let selectedMember: TeamMember | null = $state(null);

	let memberRoleChangeMutation = $derived(
		createMutation({
			mutationFn: updateTeamMemberRole,
			onSuccess: async () => {
				await client.invalidateQueries({ queryKey: ['teamDetails', page.params.team_id] });
				selectedMember = null;
				toast.success('Member role updated successfully');
				openOverlay.set({ name: '', id: '' });
			},
			onError: (error) => {
				toast.error('Failed to update member role');
			}
		})
	);
	// let selectedMember: TeamMember | null = $state(null);
</script>

<div class="flex h-full min-h-0 w-full flex-col space-y-4 overflow-hidden px-6 py-4">
	{#if $getTeamDetailsQuery.isLoading}
		<Loading />
	{:else if $getTeamDetailsQuery.isError}
		<Error />
	{:else if $getTeamDetailsQuery.data}
		<div class="flex items-center justify-between">
			<h1 class="mb-4 text-2xl font-bold">{$getTeamDetailsQuery.data.name}</h1>

			<button
				class="bg-primary border-primary rounded-lg border px-4 py-1.5 text-white"
				onclick={() => openOverlay.set({ name: 'addMember', id: '' })}>Add Member</button
			>
		</div>
		<div class="flex flex-1 flex-col space-y-4">
			<div class="space-y-2 border-b border-dashed border-neutral-200 pb-4">
				<h2 class="text-primary text-xl font-semibold">Description:</h2>
				<p class="text-sm text-gray-500">{$getTeamDetailsQuery.data.description || 'N/A'}</p>
			</div>
			{#if $getTeamDetailsQuery.data.members.length === 0}
				<div class="flex h-full w-full items-center justify-center">
					<Empty />
				</div>
			{:else}
				<div class="grid grid-cols-2 gap-6 overflow-auto md:grid-cols-4 lg:grid-cols-5">
					{#each $getTeamDetailsQuery.data.members as member}
						<MemberCard {member} bind:selectedMember />
					{/each}
				</div>
			{/if}
		</div>
	{/if}
</div>

{#if $openOverlay.name === 'addMember'}
	<Modal>
		<TeamMemberForm />
	</Modal>
{/if}

{#if $openOverlay.name === 'EditMember' && selectedMember}
	<Modal>
		<div class="space-y-4 p-4">
			<div class="flex items-center justify-between">
				<h6 class="text-primary font-semibold">Edit Member Role</h6>
				<button
					type="button"
					onclick={() => {
						selectedMember = null;
						openOverlay.set({ name: '', id: '' });
					}}><Icon icon="jam:close" width="24" height="24" /></button
				>
			</div>
			<div class="space-y-4">
				<input
					type="text"
					placeholder="Member Email"
					value={selectedMember?.email}
					id="Member Email"
					disabled
					class="w-full rounded border border-neutral-200 bg-neutral-100 p-2 text-gray-600 outline-0"
				/>
				<select
					bind:value={selectedMember.role}
					class="w-full rounded border border-neutral-200 p-2 outline-0"
				>
					<option value="" disabled selected>Select a role</option>
					{#each Object.values(MemberType) as role}
						<option value={role}>{role.replaceAll('_', ' ')}</option>
					{/each}
				</select>
				<div
					class="flex cursor-pointer items-center space-x-2 px-2 text-sm font-semibold text-neutral-600"
				>
					<input type="checkbox" bind:checked={selectedMember.isOwner} id="owner" />
					<label for="owner">Is Owner?</label>
				</div>
			</div>
			<div class="flex w-full items-center justify-end space-x-4">
				<button
					type="submit"
					class="border-primary text-primary rounded-md border px-4 py-1.5"
					onclick={() => {
						selectedMember = null;
						openOverlay.set({ name: '', id: '' });
					}}>Cancel</button
				>
				<button
					type="submit"
					class="border-primary bg-primary rounded-md border px-4 py-1.5 text-white"
					onclick={() => {
						if (selectedMember) {
							$memberRoleChangeMutation.mutate({
								team_id: page.params.team_id,
								data: {
									memberEmail: selectedMember?.email,
									role: selectedMember?.role,
									isOwner: selectedMember?.isOwner
								}
							});
						}
					}}>Submit</button
				>
			</div>
		</div>
	</Modal>
{/if}
