export type Submatch = {
  match?: { text?: string }
  start?: number
  end?: number
}

export type SearchMatchPayload = {
  path: string
  line_number: number
  lines: string
  submatches: Submatch[]
  context_before: string
  context_after: string
  mtime?: number
  request_id?: string | null
}

export type SearchErrorPayload = {
  error: string
  request_id?: string | null
}

export type SearchCompletePayload = {
  complete?: boolean
  request_id?: string | null
}

export type SearchStartedPayload = {
  query: string
  directory: string
  file_filter: string
  request_id: string
}

export type DirectoriesResponse = {
  directories: string[]
}

export type FileResponse = {
  file: string
  lines: string[]
  line_number?: number | null
}
