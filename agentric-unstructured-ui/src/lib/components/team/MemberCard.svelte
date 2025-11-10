<script lang="ts">
	import { openOverlay } from '$lib/store/openOverlay';
	import { MemberType, type TeamMember } from '$lib/types/user';
	import Icon from '@iconify/svelte';
	import Modal from '../UI/Modal.svelte';
	import { page } from '$app/state';
	import { createMutation, useQueryClient } from '@tanstack/svelte-query';
	import { removeTeamMember, updateTeamMemberRole } from '$lib/query/auth';
	import toast from 'svelte-french-toast';

	let {
		member,
		selectedMember = $bindable(null)
	}: { member: TeamMember; selectedMember: TeamMember | null } = $props();

	const client = useQueryClient();

	let removeMemberMutation = $derived(
		createMutation({
			mutationFn: removeTeamMember,
			onSuccess: async () => {
				await client.invalidateQueries({ queryKey: ['teamDetails', page.params.team_id] });
				toast.success('Member removed successfully');
				openOverlay.set({ name: '', id: '' });
			},
			onError: (error) => {
				toast.error('Failed to remove member');
			}
		})
	);
</script>

<div
	class="bg-secondary flex flex-col space-y-4 rounded-lg border border-neutral-200 p-4 lg:min-w-52"
>
	<div class="flex items-center space-x-3">
		<p class="text-primary rounded-full border border-neutral-200 bg-slate-100 p-2">
			<Icon icon="basil:user-outline" width="24" height="24" />
		</p>
		<p class="text-primary truncate font-semibold text-nowrap">{member.name}</p>
	</div>
	<hr class="border-dashed border-neutral-300" />
	<div class="space-y-2">
		<p class="flex space-x-2 text-sm text-neutral-700">
			<span class="font-semibold">Email: </span>
			<span class="truncate text-nowrap text-neutral-600">{member.email}</span>
		</p>
		<p class="flex space-x-2 text-sm text-neutral-700">
			<span class="font-semibold">Member Type: </span>
			<span class={member.role === MemberType.MEMBER ? 'text-yellow-500' : 'text-green-600'}
				>{member.role}</span
			>
		</p>
	</div>
	<hr class="border-dashed border-neutral-300" />
	<div class="flex justify-between">
		<button
			class="flex items-center space-x-1 text-sm"
			onclick={() => {
				selectedMember = member;
				openOverlay.set({ name: 'EditMember', id: '' });
			}}
		>
			<Icon icon="mingcute:user-edit-line" width="16" height="16" />
			<span class="text-primary underline underline-offset-2">Edit </span>
		</button>
		<button
			class="flex items-center space-x-1 text-sm text-red-400"
			onclick={() => {
				$removeMemberMutation.mutate({
					team_id: page.params.team_id,
					data: {
						memberEmail: member.email,
						isOwner: member.isOwner,
						role: member.role
					}
				});
			}}
		>
			<Icon icon="lineicons:trash-3" width="16" height="16" />
		</button>
	</div>
</div>
