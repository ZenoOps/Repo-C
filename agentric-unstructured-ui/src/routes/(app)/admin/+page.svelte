<script lang="ts">
	import TeamForm from '$lib/components/form/TeamForm.svelte';
	import UserForm from '$lib/components/form/UserForm.svelte';
	import { toTitleCase } from '$lib/components/helper';
	import Empty from '$lib/components/UI/Empty.svelte';
	import Error from '$lib/components/UI/Error.svelte';
	import Loading from '$lib/components/UI/Loading.svelte';
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

	let currentPage = $state(1);
	let getUserListQuery = $derived(
		createQuery({
			queryKey: ['users_dash', currentPage],
			queryFn: getUserList
		})
	);

	let deleteUserMutation = $derived(
		createMutation({
			mutationFn: deleteUser,
			onSuccess: async () => {
				await client.invalidateQueries({ queryKey: ['users_dash', 1] });
				toast.success('User deleted successfully');
			},
			onError: (error) => {
				toast.error('Failed to delete user');
			}
		})
	);

	let users = $derived(
		($getUserListQuery.data ? $getUserListQuery.data.items : []) as UserProfile[]
	);

	let selectedUser: UserProfile | null = $state(null);

	let dropdownActions = $derived([
		{ name: 'Delete Profile', icon: 'hugeicons:delete-03', key: 'delete' }
	]);
</script>

<div class="flex h-full min-h-0 w-full flex-col space-y-4 overflow-hidden px-4 py-4">
	<div class="flex items-center justify-between">
		<h3 class="text-primary text-2xl font-semibold">Users</h3>
		<button
			class="bg-primary border-primary rounded-lg border px-4 py-1.5 text-white"
			onclick={() => openOverlay.set({ name: 'createUser', id: '' })}>Create User</button
		>
	</div>
	<hr class="border-dashed border-neutral-200" />
	{#if $getUserListQuery.isLoading}
		<Loading />
	{:else if $getUserListQuery.isError}
		<Error />
	{:else if $getUserListQuery.data}
		<div class="flex-1 overflow-auto">
			<Table headColums={['Username', 'Email', 'Verified', 'Team', 'Action']}>
				{#if users.length === 0}
					<tr>
						<td colspan="5" class="p-4 text-center text-slate-600">
							<Empty />
						</td>
					</tr>
				{:else}
					{#each users as user}
						<tr class="hover:bg-secondary text-sm">
							<td class="p-3 text-slate-700">{user.name || '----'}</td>
							<td class="p-3 text-slate-700">{user.email} </td>

							<td class="p-3 text-slate-700"
								><span class="text-xs">
									{#if user.isVerified}
										<Icon icon="gg:check-o" width="16" height="16" class="inline  text-green-600" />
									{:else}
										<Icon
											icon="charm:circle-cross"
											width="16"
											height="16"
											class="inline  text-red-600"
										/>
									{/if}
								</span>
							</td>
							<!-- <td class="p-3 text-slate-700"
								>{user.roles.length
									? toTitleCase(user.roles[0].roleName.replace('_', ' '))
									: '----'}
							</td> -->
							<td class="p-3 text-slate-700"
								>{user.teams.length ? user.teams[0].teamName : '----'}</td
							>

							<td class="p-3 text-slate-700">
								<div class="relative">
									<button
										class="cursor-pointer"
										onclick={() => {
											selectedUser = user;
											if ($openOverlay.name || $openOverlay.id) {
												openOverlay.set({ name: '', id: '' });
											} else {
												openOverlay.set({ name: user.name, id: user.id });
											}
										}}><Icon icon="ph:dots-three-bold" width="24" height="24" /></button
									>
									{#if $openOverlay.name === user.name && $openOverlay.id === user.id}
										<div
											class="absolute top-10 right-0 z-60 space-y-2 rounded-md border border-slate-200 bg-white p-2 shadow-lg"
										>
											{#each dropdownActions as ite}
												<button
													onclick={() => {
														if (ite.key === 'edit') {
															// openOverlay.set({ name: 'editUser', id: user.id });
														} else if (ite.key === 'delete') {
															openOverlay.set({ name: '', id: '' });
															if (selectedUser) {
																$deleteUserMutation.mutate(selectedUser?.id);
															}
														}
													}}
													class="hover:bg-secondary hover:text-primary flex w-full cursor-pointer space-x-2 rounded px-3 py-2 text-slate-800"
												>
													<Icon icon={ite.icon} width="20" height="20" class="" />
													<span class=" text-sm text-nowrap">{ite.name}</span>
												</button>
											{/each}
										</div>
									{/if}
								</div>
							</td>
						</tr>
					{/each}
				{/if}
			</Table>
		</div>
	{/if}

	<hr class="border-dashed border-neutral-200" />
	<Pagination
		bind:currentPage
		limit={$getUserListQuery.data?.limit ?? 20}
		offset={$getUserListQuery.data?.offset ?? 0}
		total={$getUserListQuery.data?.total ?? 0}
	/>
</div>

{#if $openOverlay.name === 'createUser'}
	<Modal>
		<UserForm bind:user={selectedUser} />
	</Modal>
{/if}
