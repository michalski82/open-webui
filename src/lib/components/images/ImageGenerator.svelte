<script lang="ts">
	import { toast } from 'svelte-sonner';

	import { imageGenerations } from '$lib/apis/images';
	import Spinner from '$lib/components/common/Spinner.svelte';

	const MODELS = [
		{ value: 'gemini-2.5-flash-image', label: 'Gemini 2.5 Flash (najlepsza jakość)' },
		{ value: 'flux-realism', label: 'Flux Realism (fotorealizm)' },
		{ value: 'flux', label: 'Flux Schnell (szybki)' },
		{ value: 'flux-anime', label: 'Flux Anime' },
		{ value: 'flux-3d', label: 'Flux 3D' },
		{ value: 'turbo', label: 'SDXL Turbo' }
	];

	let loading = false;
	let prompt = '';
	let selectedModel = 'gemini-2.5-flash-image';
	let generatedImages: { url: string }[] = [];

	let promptTextareaElement: HTMLTextAreaElement;

	const resizeTextarea = () => {
		if (promptTextareaElement) {
			promptTextareaElement.style.height = '';
			promptTextareaElement.style.height =
				Math.min(promptTextareaElement.scrollHeight, 200) + 'px';
		}
	};

	const submitHandler = async () => {
		if (!prompt.trim()) {
			toast.error('Wpisz opis obrazu.');
			return;
		}

		loading = true;
		try {
			const result = await imageGenerations(localStorage.token, prompt, selectedModel);
			if (result) {
				generatedImages = [...result, ...generatedImages];
			}
		} catch (error) {
			toast.error(`${error}`);
		} finally {
			loading = false;
		}
	};

	const openExternal = async (url: string) => {
		try {
			await navigator.clipboard.writeText(prompt);
			toast.success('Prompt skopiowany do schowka');
		} catch {
			toast.error('Nie udalo sie skopiowac promptu');
		}
		window.open(url, '_blank', 'noopener,noreferrer');
	};

	const downloadImage = async (url: string, index: number) => {
		try {
			const response = await fetch(url);
			const blob = await response.blob();
			const blobUrl = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = blobUrl;
			a.download = `obraz-${Date.now()}-${index}.png`;
			a.click();
			URL.revokeObjectURL(blobUrl);
		} catch {
			toast.error('Nie udalo sie pobrac obrazu.');
		}
	};
</script>

<div class="flex flex-col justify-between w-full overflow-y-auto h-full">
	<div class="mx-auto w-full md:px-0 h-full">
		<div class="flex flex-col h-full px-4">

			<!-- Generated images grid -->
			<div class="pt-0.5 pb-2.5 flex flex-col justify-between w-full flex-auto overflow-auto h-0">
				<div class="h-full w-full flex flex-col">
					<div class="flex-1 p-1">
						{#if generatedImages.length > 0}
							<div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
								{#each generatedImages as image, index}
									<button
										class="relative group cursor-pointer"
										on:click={() => downloadImage(image.url, index)}
									>
										<img
											src={image.url}
											alt=""
											class="w-full aspect-square object-cover rounded-lg border border-gray-100/30 dark:border-gray-850/30"
										/>
										<div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition rounded-lg flex items-center justify-center">
											<svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
												<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
												<polyline points="7,10 12,15 17,10" />
												<line x1="12" y1="15" x2="12" y2="3" />
											</svg>
										</div>
									</button>
								{/each}
							</div>
						{:else}
							<div class="h-full flex items-center justify-center text-gray-400 dark:text-gray-600 text-sm">
								Wygenerowane obrazy pojawia sie tutaj
							</div>
						{/if}
					</div>
				</div>
			</div>

			<!-- Input area -->
			<div class="pb-3">
				<p class="text-xs text-gray-400 dark:text-gray-600 mb-1.5 px-1">
					Wskazowka: popros AI w czacie o napisanie szczegolowego promptu, a nastepnie wklej go tutaj.
				</p>

				<div class="border border-gray-100/30 dark:border-gray-850/30 w-full px-3 py-2.5 rounded-xl">
					<!-- Textarea -->
					<div class="py-0.5">
						<textarea
							bind:this={promptTextareaElement}
							bind:value={prompt}
							class="w-full h-full bg-transparent resize-none outline-hidden text-sm"
							placeholder="Opisz obraz, ktory chcesz wygenerowac..."
							on:input={resizeTextarea}
							on:focus={resizeTextarea}
							on:keydown={(e) => {
								if (e.key === 'Enter' && (e.metaKey || e.ctrlKey) && !loading) {
									e.preventDefault();
									submitHandler();
								}
							}}
							rows="3"
						/>
					</div>

					<!-- Model selector + actions row -->
					<div class="flex justify-between items-center gap-2 mt-2 flex-wrap">
						<!-- Left: model selector + external buttons -->
						<div class="flex gap-2 items-center shrink-0 flex-wrap">
							<select
								bind:value={selectedModel}
								class="text-xs bg-gray-50 dark:bg-gray-850 border border-gray-200/50 dark:border-gray-700/50 text-gray-700 dark:text-gray-300 rounded-lg px-2 py-1.5 outline-none cursor-pointer"
							>
								{#each MODELS as m}
									<option value={m.value}>{m.label}</option>
								{/each}
							</select>

							<button
								type="button"
								class="px-3 py-1.5 text-xs font-medium bg-gray-50 hover:bg-gray-100 text-gray-700 dark:bg-gray-850 dark:hover:bg-gray-800 dark:text-gray-300 transition rounded-lg"
								on:click={() => openExternal('https://gemini.google.com/app')}
							>
								Gemini ↗
							</button>
							<button
								type="button"
								class="px-3 py-1.5 text-xs font-medium bg-gray-50 hover:bg-gray-100 text-gray-700 dark:bg-gray-850 dark:hover:bg-gray-800 dark:text-gray-300 transition rounded-lg"
								on:click={() => openExternal('https://www.bing.com/images/create')}
							>
								Bing ↗
							</button>
							<button
								type="button"
								class="px-3 py-1.5 text-xs font-medium bg-gray-50 hover:bg-gray-100 text-gray-700 dark:bg-gray-850 dark:hover:bg-gray-800 dark:text-gray-300 transition rounded-lg"
								on:click={() => openExternal('https://ideogram.ai/t/generate')}
							>
								Ideogram ↗
							</button>
							<button
								type="button"
								class="px-3 py-1.5 text-xs font-medium bg-gray-50 hover:bg-gray-100 text-gray-700 dark:bg-gray-850 dark:hover:bg-gray-800 dark:text-gray-300 transition rounded-lg"
								on:click={() => openExternal('https://firefly.adobe.com/generate/images')}
							>
								Firefly ↗
							</button>
						</div>

						<!-- Right: generate button -->
						<div class="shrink-0">
							{#if !loading}
								<button
									disabled={prompt.trim() === ''}
									class="px-3.5 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
									on:click={submitHandler}
								>
									Generuj
								</button>
							{:else}
								<button
									class="px-3.5 py-1.5 text-sm font-medium bg-gray-300 text-black transition rounded-lg flex items-center gap-2"
									disabled
								>
									<Spinner className="size-4" />
									Generowanie...
								</button>
							{/if}
						</div>
					</div>
				</div>
			</div>

		</div>
	</div>
</div>
