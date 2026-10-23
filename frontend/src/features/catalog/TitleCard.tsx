import { Link } from 'react-router-dom'
import type { components } from '@/types/api'
import { ratingLabel } from './params'
import { Poster } from './Poster'

type Item = components['schemas']['TitleListItem']

export function TitleCard({ title }: { title: Item }) {
  return (
    <Link
      to={`/titles/${title.slug}`}
      className="group flex flex-col gap-2 rounded-md focus-visible:outline-offset-4"
    >
      <Poster
        url={title.poster_url}
        name={title.name}
        className="transition-transform group-hover:scale-[1.02]"
      />
      <span className="line-clamp-2 text-sm font-medium">{title.name}</span>
      <span className="text-xs text-text-muted">
        {[title.release_year, ratingLabel(title.maturity_rating)].filter(Boolean).join(' · ')}
      </span>
    </Link>
  )
}

export function TitleCardSkeleton() {
  return (
    <div aria-hidden="true" className="flex flex-col gap-2">
      <div className="aspect-[2/3] animate-pulse rounded-md bg-surface-2" />
      <div className="h-4 w-3/4 animate-pulse rounded bg-surface-2" />
      <div className="h-3 w-1/3 animate-pulse rounded bg-surface-2" />
    </div>
  )
}
