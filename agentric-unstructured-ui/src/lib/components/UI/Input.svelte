<script lang="ts">
	let { value = $bindable<string | null>(null), class: dynamicClass = '', ...restProps } = $props();
</script>

<input
	{...restProps}
	bind:value={value}
	class={`${dynamicClass ? dynamicClass : 'mb-4 w-full rounded border border-neutral-200 p-2 outline-0'}`}
/>
