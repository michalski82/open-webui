import { MUSIC_API_BASE_URL } from '$lib/constants';

export const generateMusic = async (
	token: string,
	prompt: string,
	makeInstrumental: boolean = false
): Promise<any> => {
	const response = await fetch(`${MUSIC_API_BASE_URL}/generate`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({ prompt, make_instrumental: makeInstrumental })
	});
	if (!response.ok) throw await response.json();
	return await response.json();
};

export const getMusicLimit = async (token: string): Promise<any> => {
	const response = await fetch(`${MUSIC_API_BASE_URL}/limit`, {
		headers: { Authorization: `Bearer ${token}` }
	});
	if (!response.ok) throw await response.json();
	return await response.json();
};
