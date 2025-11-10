<script lang="ts">
	let {
		label,
		required = false,
		disabled,
		isMultiple = false,
		onChangeAddFunction
	}: {
		label?: string;
		required?: boolean;
		disabled?: boolean;
		isMultiple?: boolean;
		onChangeAddFunction: (e: Event) => void;
	} = $props();
	let id = $derived(label?.replace(/ /g, '-'));
	let loading = $state(false);
</script>

<div class="relative md:col-span-2">
	<input
		onchange={(e) => onChangeAddFunction(e)}
		{disabled}
		type="file"
		{id}
		multiple={isMultiple}
		{required}
		class={`text-grey-500 text-sm
            file:mr-5 file:rounded-full file:border-0
             file:px-6
            file:py-2 file:text-sm
            file:font-medium
            ${loading ? 'file:bg-opacity-50' : 'file:cursor-pointer'}
            ${disabled ? 'file:bg-primary file:text-slate-500' : 'file:bg-secondary file:text-slate-500'}`}
	/>
</div>
