<script lang="ts">
	let { class: dynamicClass = '', ...restProps } = $props();
</script>

<input
	{...restProps}
	class={`${dynamicClass ? dynamicClass : 'mb-4'}`}
    type="checkbox"
/>
