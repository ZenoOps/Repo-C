<script lang="ts">
	import { page } from '$app/state';
	import { addTeamMember, getUserList } from '$lib/query/auth';
	import { openOverlay } from '$lib/store/openOverlay';
	import { MemberType } from '$lib/types/user';
	import Icon from '@iconify/svelte';
	import { createMutation, createQuery, useQueryClient } from '@tanstack/svelte-query';
	import toast from 'svelte-french-toast';
	import DropDown from '../UI/DropDown.svelte';

	const client = useQueryClient();

	let currentPage = $state(1);
	let getUserListQuery = $derived(
		createQuery({
			queryKey: ['users', currentPage],
			queryFn: getUserList
		})
	);
	let users = $derived($getUserListQuery.data?.items ?? []);

	let member_email = $state('');
	let role: MemberType = $state(MemberType.MEMBER);

	let addTeamMemberMutation = $derived(
		createMutation({
			mutationFn: addTeamMember,
			onSuccess: async (data) => {
				toast.success('Team Member added successfully');

				await client.invalidateQueries({ queryKey: ['teamDetails', page.params.team_id] });
				openOverlay.set({ name: '', id: '' });
			},
			onError: (error) => {
				toast.error('Failed to added Team Member');
			}
		})
	);

	const handleSubmit = (e: Event) => {
		e.preventDefault();

		let data = {
			memberEmail: member_email,
			role: role,
			isOwner: false
		};

		$addTeamMemberMutation.mutate({ team_id: page.params.team_id, data });
	};
</script>

<div class="z-20 w-full space-y-4 p-4">
	<div class="flex items-center justify-between">
		<h6 class="text-primary font-semibold">Add Member to Team</h6>
		<button
			type="button"
			onclick={() => {
				openOverlay.set({ name: '', id: '' });
			}}><Icon icon="jam:close" width="24" height="24" /></button
		>
	</div>
	<hr class="border-dashed border-neutral-200" />
	<form class="w-full min-w-96 space-y-4 text-sm" onsubmit={handleSubmit}>
		<label class="mb-2 block text-sm font-medium text-neutral-500" for="emai_id">User Name</label>

		<select
			disabled={$getUserListQuery.isLoading}
			id="emai_id"
			placeholder="Select a user"
			bind:value={member_email}
			class="{$getUserListQuery.isLoading ? "opacity-50" : "opacity-100"}mb-4 w-full rounded border border-neutral-200 p-2 outline-0"
		>
			<option value="" disabled selected>Select User</option>
			{#each users as user}
				<option value={user.email}>{user.email}</option>
			{/each}
		</select>
		<label class="mb-2 block text-sm font-medium text-neutral-500" for="role_id">Role</label>

		<select
			id="role_id"
			bind:value={role}
			class="mb-4 w-full rounded border border-neutral-200 p-2 outline-0"
		>
			<option value="" disabled selected>Select a role</option>
			{#each Object.values(MemberType) as role}
				<option value={role}>{role.replaceAll('_', ' ')}</option>
			{/each}
		</select>
		<div class="flex w-full items-center justify-end space-x-4">
			<button
				type="submit"
				class="border-primary text-primary rounded-md border px-4 py-1.5"
				onclick={() => {
					openOverlay.set({ name: '', id: '' });
				}}>Cancel</button
			>

			<button
				type="submit"
				class="bg-primary border-primary rounded-md border px-4 py-1.5 text-white">Submit</button
			>
		</div>
	</form>
</div>
