export function infinite_scroll(load: () => void, opts?: { rootMargin?: string; root?: Element | null }) {
  return (node: HTMLElement) => {
    const get_scroll_parent = (el: HTMLElement | null): HTMLElement | null => {
      let cur: HTMLElement | null = el?.parentElement ?? null
      while (cur) {
        const style = getComputedStyle(cur)
        const oy = style.overflowY
        if ((oy === 'auto' || oy === 'scroll') && cur.scrollHeight > cur.clientHeight) return cur
        cur = cur.parentElement
      }
      return null
    }

    const root = opts?.root ?? get_scroll_parent(node)

    const observer = new IntersectionObserver(
      entries => {
        entries.forEach(entry => {
          if (!entry.isIntersecting) return
          load()
        })
      },
      { root: root ?? null, rootMargin: opts?.rootMargin ?? '200px 0px', threshold: 0 }
    )
    observer.observe(node)
    return () => observer.disconnect()
  }
}
