export type RequestEvent<T> = { payload: T }

export function with_current(get_id: () => string) {
  return <T extends { request_id?: string | null }>(fn: (p: T) => void) => (event: RequestEvent<T>) => {
    if (event.payload.request_id !== get_id()) return
    fn(event.payload)
  }
}
