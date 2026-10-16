export default function Loading() {
  return (
    <div className="min-w-0 space-y-4" aria-busy="true" aria-label="Loading">
      <div className="h-8 w-2/3 animate-pulse rounded-lg bg-cream-200 sm:w-1/3" />
      <div className="grid grid-cols-1 gap-3 min-[400px]:grid-cols-2 sm:gap-4 lg:grid-cols-4">
        {[0, 1, 2, 3].map((i) => <div key={i} className="h-24 animate-pulse rounded-xl bg-cream-100 sm:h-28" />)}
      </div>
    </div>
  );
}
