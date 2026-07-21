import { WEBUI_API_BASE_URL } from '$lib/constants';

export const notifyAdmin = async (token: string): Promise<{ ok: boolean }> => {
    const res = await fetch(`${WEBUI_API_BASE_URL}/bot/notify-admin`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
        }
    });
    if (!res.ok) throw await res.json();
    return res.json();
};
