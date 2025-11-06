import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
	return twMerge(clsx(inputs));
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type WithoutChild<T> = T extends { child?: any } ? Omit<T, "child"> : T;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type WithoutChildren<T> = T extends { children?: any } ? Omit<T, "children"> : T;
export type WithoutChildrenOrChild<T> = WithoutChildren<WithoutChild<T>>;
export type WithElementRef<T, U extends HTMLElement = HTMLElement> = T & { ref?: U | null };

export function debounce<T extends (...args: any[]) => void>(fn: T, wait: number) {
	let timeout: ReturnType<typeof setTimeout>
	return (...args: Parameters<T>) => {
		clearTimeout(timeout)
		timeout = setTimeout(() => fn(...args), wait)
	}
}

const multi_match_map: Record<string, string> = {
	ا: 'اأآإى',
	أ: 'أإءؤئ',
	إ: 'أإءؤئ',
	ء: 'ءأإؤئ',
	ت: 'تة',
	ة: 'ةته',
	ه: 'هة',
	ى: 'ىاي',
	ي: 'يى',
}

const multi_match_re = RegExp(`[${Object.keys(multi_match_map).join('')}]`, 'g')

export function prep_query(q: string) {
	q = q.replace(/[^\p{L}\p{N} ]/gu, '').trim()
	return RegExp(
		q.replace(/\s+/g, '.*?').replace(multi_match_re, (m: string) => `[${multi_match_map[m]}]`)
	)
}
