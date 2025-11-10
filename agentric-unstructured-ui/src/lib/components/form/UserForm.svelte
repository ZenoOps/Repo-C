<script lang="ts">
	import { createUser, getRoles, getTeams, updateUser } from '$lib/query/auth';
	import { openOverlay } from '$lib/store/openOverlay';
	import type { Team, UserProfile } from '$lib/types/user';
	import Icon from '@iconify/svelte';
	import { createMutation, createQuery, useQueryClient } from '@tanstack/svelte-query';
	import toast from 'svelte-french-toast';
	import Input from '../UI/Input.svelte';
	import Button from '../UI/Button.svelte';

	let { user = $bindable(null) }: { user: UserProfile | null } = $props();

	const client = useQueryClient();

	let name = $state(user ? user.name : '');
	let email = $state(user ? user.email : '');
	let password = $state('');
	let teamId = $state('');

	let getTeamsQuery = $derived(
		createQuery({
			queryKey: ['team_create_user'],
			queryFn: getTeams
		})
	);
	let teams = $derived($getTeamsQuery.data ? $getTeamsQuery.data.items : []) as Team[];

	let createUserMutation = $derived(
		createMutation({
			mutationFn: createUser,
			onSuccess: async (data) => {
				user = null;
				toast.success('User created successfully');

				await client.invalidateQueries({ queryKey: ['users_dash', 1] });
				openOverlay.set({ name: '', id: '' });
			},
			onError: (error) => {
				// handle error, maybe show a toast
				toast.error('Failed to create user');
			}
		})
	);

	// let updateUserMutation = $derived(
	// 	createMutation({
	// 		mutationFn: updateUser,
	// 		onSuccess: async (data) => {
	// 			user = null;
	// 			toast.success('User updated successfully');

	// 			await client.invalidateQueries({ queryKey: ['users_dash', 1] });
	// 			openOverlay.set({ name: '', id: '' });
	// 		},
	// 		onError: (error) => {
	// 			// handle error, maybe show a toast
	// 			toast.error('Failed to update user');
	// 		}
	// 	})
	// );

	const handleSubmit = (e: Event) => {
		e.preventDefault();
		if (!name || !email || !password) {
			toast.error('Please fill in all fields');
			return;
		}
		// if (user) {
		// 	$updateUserMutation.mutate({ userId: user.id, data: { name, email, password } });
		// } else {
		$createUserMutation.mutate({ name, email, password, teamId: teamId });
		// }
	};
</script>

<div class="w-full space-y-4 p-4">
	<div class="flex items-center justify-between">
		<h6 class="text-primary font-semibold">{user ? 'Edit' : 'Create'} User</h6>
		<button
			type="button"
			onclick={() => {
				user = null;
				openOverlay.set({ name: '', id: '' });
			}}><Icon icon="jam:close" width="24" height="24" /></button
		>
	</div>
	<hr class="border-dashed border-neutral-200" />
	<form class="w-full min-w-96 text-sm" onsubmit={handleSubmit}>
		<label class="mb-2 block text-sm font-medium text-neutral-500" for="username">User Name</label>
		<Input type="text" placeholder="Username" bind:value={name} id="username" required />
		<label class="mb-2 block text-sm font-medium text-neutral-500" for="email">Email</label>
		<Input type="email" placeholder="Email" required id="email" bind:value={email} />
		<label class="mb-2 block text-sm font-medium text-neutral-500" for="password">Password</label>
		<Input type="password" placeholder="Password" required id="password" bind:value={password} />
		<label class="mb-2 block text-sm font-medium text-neutral-500" for="teamId">Organization</label>
		<select
			id="teamId"
			bind:value={teamId}
			class="mb-4 w-full rounded border border-neutral-200 p-2 outline-0"
		>
			<option value="" disabled selected>Select a Organization</option>
			{#each teams as team}
				<option value={team.id}>{team.name.replaceAll('_', ' ')}</option>
			{/each}
		</select>

		<div class="flex w-full items-center justify-end space-x-4">
			<Button
				type="submit"
				class="border-primary text-primary rounded-md border px-4 py-1.5"
				onclick={() => {
					user = null;
					openOverlay.set({ name: '', id: '' });
				}}>Cancel</Button
			>

			<Button
				type="submit"
				class="bg-primary border-primary rounded-md border px-4 py-1.5 text-white">Submit</Button
			>
		</div>
	</form>
</div>
