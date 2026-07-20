<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { WEBUI_NAME, showSidebar, config, user, mobile } from '$lib/stores';
	import { goto } from '$app/navigation';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Sidebar from '$lib/components/icons/Sidebar.svelte';

	const i18n = getContext('i18n');

	let loaded = false;

	onMount(async () => {
		if (
			!($config?.features?.enable_image_generation ?? false) ||
			!($user?.role === 'admin' || ($user?.permissions?.features?.image_generation ?? false))
		) {
			goto('/');
			return;
		}
		loaded = true;
	});
</script>

<svelte:head>
	<title>Obrazy • {$WEBUI_NAME}</title>
</svelte:head>

{#if loaded}
	<div
		class="flex flex-col w-full h-screen max-h-[100dvh] transition-width duration-200 ease-in-out {$showSidebar
			? 'md:max-w-[calc(100%-var(--sidebar-width))]'
			: ''} max-w-full"
	>
		<nav class="px-2.5 pt-1.5 backdrop-blur-xl w-full drag-region select-none">
			<div class="flex items-center">
				{#if $mobile}
					<div class="{$showSidebar ? 'md:hidden' : ''} flex flex-none items-center self-end">
						<Tooltip
							content={$showSidebar ? $i18n.t('Close Sidebar') : $i18n.t('Open Sidebar')}
							interactive={true}
						>
							<button
								id="sidebar-toggle-button"
								class="cursor-pointer flex rounded-lg hover:bg-gray-100 dark:hover:bg-gray-850 transition"
								on:click={() => showSidebar.set(!$showSidebar)}
							>
								<div class="self-center p-1.5">
									<Sidebar />
								</div>
							</button>
						</Tooltip>
					</div>
				{/if}

				<div class="ml-2 py-0.5 self-center flex items-center w-full">
					<div class="text-sm font-medium">Obrazy</div>
				</div>
			</div>
		</nav>

		<div class="flex-1 max-h-full overflow-y-auto">
			<slot />
		</div>
	</div>
{/if}
