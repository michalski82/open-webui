<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { onMount } from 'svelte';

	import { generateMusic, getMusicLimit } from '$lib/apis/music';
	import Spinner from '$lib/components/common/Spinner.svelte';

	let loading = false;
	let prompt = '';
	let makeInstrumental = false;
	let generatedTracks: any[] = [];
	let creditLimit: any = null;

	let promptTextareaElement: HTMLTextAreaElement;

	onMount(async () => {
		try {
			creditLimit = await getMusicLimit(localStorage.token);
		} catch (e) {
			console.error('Failed to fetch music limit:', e);
		}
	});

	const resizeTextarea = () => {
		if (promptTextareaElement) {
			promptTextareaElement.style.height = '';
			promptTextareaElement.style.height =
				Math.min(promptTextareaElement.scrollHeight, 200) + 'px';
		}
	};

	const submitHandler = async () => {
		if (!prompt.trim()) {
			toast.error('Wpisz opis muzyki.');
			return;
		}

		loading = true;
		try {
			const result = await generateMusic(localStorage.token, prompt, makeInstrumental);
			if (Array.isArray(result) && result.length > 0) {
				generatedTracks = [...result, ...generatedTracks];
			} else if (result && !Array.isArray(result)) {
				generatedTracks = [result, ...generatedTracks];
			} else {
				toast.error('Operacja nie zwróciła utworu. Spróbuj ponownie.');
			}
			try {
				creditLimit = await getMusicLimit(localStorage.token);
			} catch (_) {}
		} catch (error: any) {
			const detail = error?.detail ?? error?.message ?? String(error);
			toast.error(`Błąd: ${detail}`);
		} finally {
			loading = false;
		}
	};
</script>

<div class="flex flex-col justify-between w-full overflow-y-auto h-full">
	<div class="mx-auto w-full md:px-0 h-full">
		<div class="flex flex-col h-full px-4">

			<!-- Generated tracks list -->
			<div class="pt-0.5 pb-2.5 flex flex-col justify-between w-full flex-auto overflow-auto h-0">
				<div class="h-full w-full flex flex-col">
					<div class="flex-1 p-1">
						{#if generatedTracks.length > 0}
							<div class="flex flex-col gap-4">
								{#each generatedTracks as track, index}
									<div class="rounded-xl border border-gray-100/30 dark:border-gray-850/30 p-4 bg-gray-50/30 dark:bg-gray-900/30">
										{#if track.title}
											<p class="text-sm font-semibold text-gray-800 dark:text-gray-200 mb-1">
												{track.title}
											</p>
										{/if}
										{#if track.tags}
											<p class="text-xs text-gray-400 dark:text-gray-500 mb-2">
												{track.tags}
											</p>
										{/if}
										{#if track.audio_url}
											<audio controls src={track.audio_url} class="w-full mt-2" />
										{/if}
										{#if track.lyric}
											<details class="mt-3">
												<summary class="text-xs text-gray-400 dark:text-gray-500 cursor-pointer select-none hover:text-gray-600 dark:hover:text-gray-300">
													Tekst piosenki
												</summary>
												<pre class="mt-2 text-xs text-gray-600 dark:text-gray-400 whitespace-pre-wrap font-sans">{track.lyric}</pre>
											</details>
										{/if}
									</div>
								{/each}
							</div>
						{:else if !loading}
							<div class="h-full flex items-center justify-center text-gray-400 dark:text-gray-600 text-sm">
								Wygenerowane utwory pojawią się tutaj
							</div>
						{/if}

						{#if loading}
							<div class="flex flex-col items-center justify-center gap-3 mt-8">
								<Spinner className="size-8" />
								<p class="text-sm text-gray-400 dark:text-gray-500">
									Generuję muzykę, to może potrwać do minuty...
								</p>
							</div>
						{/if}
					</div>
				</div>
			</div>

			<!-- Credits info -->
			{#if creditLimit !== null}
				<div class="mb-2 px-3 py-2 rounded-lg bg-gray-50 dark:bg-gray-900/40 border border-gray-100/30 dark:border-gray-850/30 text-xs text-gray-500 dark:text-gray-400">
					Pozostałe kredyty: <strong>{creditLimit.credits_left ?? creditLimit.remaining ?? JSON.stringify(creditLimit)}</strong>
				</div>
			{/if}

			<!-- Input area -->
			<div class="pb-3">
				<div class="border border-gray-100/30 dark:border-gray-850/30 w-full px-3 py-2.5 rounded-xl">
					<!-- Textarea -->
					<div class="py-0.5">
						<textarea
							bind:this={promptTextareaElement}
							bind:value={prompt}
							class="w-full h-full bg-transparent resize-none outline-hidden text-sm"
							placeholder="Opisz muzykę którą chcesz wygenerować... np. 'energetyczny utwór elektroniczny z wokalem'"
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

					<!-- Checkbox + generate button row -->
					<div class="flex justify-between items-center gap-2 mt-2 flex-wrap">
						<!-- Left: instrumental checkbox -->
						<label class="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 cursor-pointer select-none">
							<input
								type="checkbox"
								bind:checked={makeInstrumental}
								class="rounded border-gray-300 dark:border-gray-600 bg-transparent"
							/>
							Tylko instrumentalne (bez wokalu)
						</label>

						<!-- Right: generate button -->
						<div class="shrink-0">
							{#if !loading}
								<button
									disabled={prompt.trim() === ''}
									class="px-3.5 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
									on:click={submitHandler}
								>
									GENERUJ
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
