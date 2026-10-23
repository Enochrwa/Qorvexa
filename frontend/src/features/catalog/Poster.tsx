import { useState } from 'react'
import { cn } from '@/lib/cn'
import { safeImageUrl } from './params'

/** Fixed 2:3 box so images never shift the layout when they load. */
export function Poster({
  url,
  name,
  className,
}: {
  url: string | null
  name: string
  className?: string
}) {
  const src = safeImageUrl(url)
  const [failed, setFailed] = useState(false)
  return (
    <div className={cn('relative aspect-[2/3] overflow-hidden rounded-md bg-surface-2', className)}>
      {src && !failed ? (
        <img
          src={src}
          alt=""
          width={300}
          height={450}
          loading="lazy"
          decoding="async"
          onError={() => setFailed(true)}
          className="h-full w-full object-cover"
        />
      ) : (
        <span
          aria-hidden="true"
          className="flex h-full w-full items-center justify-center p-3 text-center text-sm text-text-muted"
        >
          {name}
        </span>
      )}
    </div>
  )
}
