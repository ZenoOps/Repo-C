<script lang="ts">
	import Icon from "@iconify/svelte";

    let isDropdownOpen=$state(false)

    let {title="Select",options=[],class:dynamicClass='',value = $bindable<string>("")}=$props()
</script>

<div>
    <button onclick={()=>(isDropdownOpen = !isDropdownOpen)} type="button" class="bg-primary-600 bg-primary hover:bg-primary-700 flex items-center justify-center space-x-2 rounded-lg px-3 py-2 text-white">
        <p>{value || title}</p>
        <Icon icon="fe:arrow-down"/>
    </button>

    {#if isDropdownOpen}
        <div class="bg-primary-600 bg-primary text-white rounded-lg p-1 absolute w-[10%] m-1">
            {#each options as option}
                <div class="hover:bg-gray-300">
                    <button type="button" class="m-2 w-full text-left" onclick={()=>{
                        value=option 
                        isDropdownOpen=!isDropdownOpen
                    }}>
                        {option}
                    </button>
                </div>
            {/each}
        </div>
    {/if}
</div>