export function useShare() {
  function shareLinkedIn(url, title) {
    const encoded = encodeURIComponent(url)
    window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${encoded}`, '_blank')
  }

  function shareX(url, title) {
    const u = encodeURIComponent(url)
    const t = encodeURIComponent(title)
    window.open(`https://x.com/intent/tweet?url=${u}&text=${t}`, '_blank')
  }

  function shareFacebook(url) {
    const encoded = encodeURIComponent(url)
    window.open(`https://www.facebook.com/sharer/sharer.php?u=${encoded}`, '_blank')
  }

  function shareTeams(url, title) {
    const u = encodeURIComponent(url)
    const t = encodeURIComponent(title)
    window.open(`https://teams.microsoft.com/share?href=${u}&msgText=${t}`, '_blank')
  }

  async function copyLink(url) {
    try {
      await navigator.clipboard.writeText(url)
    } catch {
      // Fallback for non-HTTPS contexts
      const el = document.createElement('textarea')
      el.value = url
      document.body.appendChild(el)
      el.select()
      document.execCommand('copy')
      document.body.removeChild(el)
    }
  }

  return { shareLinkedIn, shareX, shareFacebook, shareTeams, copyLink }
}
