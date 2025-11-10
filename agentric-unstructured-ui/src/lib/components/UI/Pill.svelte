<script lang="ts">
    import type { Component, Snippet } from 'svelte';

    let {
        content,
        onClick,
        iconPosition = 'left',
        snippet,
        snippetPosition = 'left',
        variant = 'default'
    }: {
        content: string;
        onClick?: () => void;
        iconPosition?: 'left' | 'right';
        snippet?: Snippet;
        snippetPosition?: 'left' | 'right';
        variant?: 'default' | 'error';
    } = $props();

    let colorClass = $state('');
    let hoverClass = $state('');

    $effect(() => {
        switch (variant) {
            case 'error':
                colorClass = 'bg-red-700';
                break;
            default:
                colorClass = 'bg-grey text-txt-dark-gray';
                hoverClass = 'hover:bg-grey-hover';
        }
    });
</script>

{#if onClick}
    <button
        onclick={onClick}
        class="rounded-lg px-3 py-1 text-sm font-light {colorClass} {hoverClass} flex items-center gap-x-1 whitespace-nowrap transition-colors duration-150 [&>*]:shrink-0"
    >
 
        {#if snippet && snippetPosition === 'left'}
            {@render snippet()}
        {/if}

        {content}

 
        {#if snippet && snippetPosition === 'right'}
            {@render snippet()}
        {/if}
    </button>
{:else}
    <div
        class="rounded-lg px-3 py-1 text-sm font-medium {colorClass} flex w-fit items-center gap-x-1 whitespace-nowrap [&>*]:shrink-0"
    >
 
        {#if snippet && snippetPosition === 'left'}
            {@render snippet()}
        {/if}
        {content}
 
        {#if snippet && snippetPosition === 'right'}
            {@render snippet()}
        {/if}
    </div>
{/if}
