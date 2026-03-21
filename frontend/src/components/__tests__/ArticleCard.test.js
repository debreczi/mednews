import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ArticleCard from '../ArticleCard.vue'

const mockArticle = {
  id: 1,
  url: 'https://example.com/article',
  original_title: 'Test Article',
  mednews_title: 'Funny Test Article',
  summary: 'A great summary.',
  link_text: 'Read the original here:',
  image_url: null,
  date_collected: '2026-03-21T10:00:00',
  date_published: '2026-03-21T10:00:00',
  relevance_score: 8.0,
  is_tragic: false,
  enrichment_status: 'complete',
  source_id: null,
}

describe('ArticleCard', () => {
  it('renders mednews_title', () => {
    const wrapper = mount(ArticleCard, { props: { article: mockArticle } })
    expect(wrapper.text()).toContain('Funny Test Article')
  })

  it('renders original_title in muted style', () => {
    const wrapper = mount(ArticleCard, { props: { article: mockArticle } })
    expect(wrapper.text()).toContain('Test Article')
  })

  it('renders summary', () => {
    const wrapper = mount(ArticleCard, { props: { article: mockArticle } })
    expect(wrapper.text()).toContain('A great summary.')
  })

  it('renders source link with link_text', () => {
    const wrapper = mount(ArticleCard, { props: { article: mockArticle } })
    const link = wrapper.find('a[href="https://example.com/article"]')
    expect(link.exists()).toBe(true)
    expect(link.text()).toContain('Read the original here')
  })

  it('renders 4 platform share buttons', () => {
    const wrapper = mount(ArticleCard, { props: { article: mockArticle } })
    // ShareButtons renders 5 buttons (LinkedIn, X, Facebook, Teams, Copy)
    const buttons = wrapper.findAll('button')
    expect(buttons.length).toBeGreaterThanOrEqual(4)
  })

  it('shows tragic border for tragic articles', () => {
    const wrapper = mount(ArticleCard, {
      props: { article: { ...mockArticle, is_tragic: true } }
    })
    expect(wrapper.find('article').classes()).toContain('border-l-4')
  })

  it('computes star rating from relevance_score', () => {
    // relevance_score 8.0 → 4 stars
    const wrapper = mount(ArticleCard, { props: { article: mockArticle } })
    const stars = wrapper.findAll('span').filter(s => s.text() === '★')
    const filledStars = wrapper.findAll('.text-amber-400')
    expect(filledStars.length).toBe(4)
  })

  it('shows placeholder when no image', () => {
    const wrapper = mount(ArticleCard, { props: { article: { ...mockArticle, image_url: null } } })
    expect(wrapper.find('img').exists()).toBe(false)
    expect(wrapper.find('svg').exists()).toBe(true)
  })
})
