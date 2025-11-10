<script lang="ts">
	import { createTeam, createUser, getRoles, updateUser } from '$lib/query/auth';
	import { openOverlay } from '$lib/store/openOverlay';
	import type { UserProfile } from '$lib/types/user';
	import Icon from '@iconify/svelte';
	import { createMutation, createQuery, useQueryClient } from '@tanstack/svelte-query';
	import toast from 'svelte-french-toast';

	const client = useQueryClient();

	let name = $state('');
	let description = $state('');

	let createTeamMutation = $derived(
		createMutation({
			mutationFn: createTeam,
			onSuccess: async (data) => {
				toast.success('Team created successfully');

				await client.invalidateQueries({ queryKey: ['teams'] });
				openOverlay.set({ name: '', id: '' });
			},
			onError: (error) => {
				// handle error, maybe show a toast
				toast.error('Failed to create Team');
			}
		})
	);

	const handleSubmit = (e: Event) => {
		e.preventDefault();
		if (!name) {
			toast.error('Please fill in all fields');
			return;
		}

		$createTeamMutation.mutate({ name, description });
	};
</script>

<div class="w-full space-y-4 p-4">
	<div class="flex items-center justify-between">
		<h6 class="text-primary font-semibold">{'Create'} User</h6>
		<button
			type="button"
			onclick={() => {
				openOverlay.set({ name: '', id: '' });
			}}><Icon icon="jam:close" width="24" height="24" /></button
		>
	</div>
	<hr class="border-dashed border-neutral-200" />
	<form class="w-full min-w-96 text-sm" onsubmit={handleSubmit}>
		<label class="mb-2 block text-sm font-medium text-neutral-500" for="username">User Name</label>
		<input
			type="text"
			placeholder="Team Name"
			bind:value={name}
			id="username"
			required
			class="mb-4 w-full rounded border border-neutral-200 p-2 outline-0"
		/>
		<label class="mb-2 block text-sm font-medium text-neutral-500" for="email">Description</label>
		<input
			type="tetx"
			placeholder="Description"
			id="email"
			bind:value={description}
			class="mb-4 w-full rounded border border-neutral-200 p-2 outline-0"
		/>

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
