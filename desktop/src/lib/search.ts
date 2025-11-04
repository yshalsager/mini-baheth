import { pyInvoke } from 'tauri-plugin-pytauri-api'
import type { DirectoriesResponse, FileResponse } from '$lib/types'

export function get_data_root() {
  return pyInvoke<string>('get_data_root', {})
}

export function set_data_root(path: string) {
  return pyInvoke<string>('set_data_root', { path })
}

export function list_directories(query: string, limit = 200) {
  return pyInvoke<DirectoriesResponse>('list_directories', { query: query?.trim() ?? '', limit })
}

export function search(params: { query: string; directory: string; file_filter: string; request_id: string }) {
  return pyInvoke('search', params)
}

export function fetch_file(params: { path: string; line_number?: number }) {
  return pyInvoke<FileResponse>('fetch_file', params)
}

