import { Activity } from 'lucide-react';

export default function SkeletonCard() {
  return (
    <div className="glass-card p-4">
      <div className="flex justify-between items-start gap-3">
        {/* Left Side */}
        <div className="flex-1 space-y-3 w-full">
          <div className="flex items-center gap-2">
            <div className="h-5 w-20 skeleton-bg rounded-md" />
            <div className="h-4 w-12 skeleton-bg rounded-full" />
          </div>
          <div className="h-3 w-3/4 skeleton-bg rounded-md" />
          
          <div className="flex gap-4 mt-4">
            <div className="h-3 w-16 skeleton-bg rounded-md" />
            <div className="h-3 w-12 skeleton-bg rounded-md" />
            <div className="h-3 w-24 skeleton-bg rounded-md hidden sm:block" />
          </div>
        </div>

        {/* Right Side */}
        <div className="flex flex-col items-end gap-3 shrink-0">
          <div className="h-4 w-16 skeleton-bg rounded-md" />
          <div className="h-6 w-6 skeleton-bg rounded-md" />
        </div>
      </div>
    </div>
  );
}
