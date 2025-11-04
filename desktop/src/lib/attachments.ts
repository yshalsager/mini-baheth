export function infinite_scroll(load: () => void, opts?: { rootMargin?: string }) {
  return (node: HTMLElement) => {
    const observer = new IntersectionObserver(
      entries => {
        entries.forEach(entry => {
          if (!entry.isIntersecting) return
          load()
        })
      },
      { root: null, rootMargin: opts?.rootMargin ?? '200px 0px', threshold: 0 }
    )
    observer.observe(node)
    return () => observer.disconnect()
  }
}

