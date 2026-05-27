type Props = {
  current: number;
  total: number;
  label?: string;
};

export default function ProgressBar({ current, total, label }: Props) {
  const pct = total > 0 ? Math.min(100, Math.round((current / total) * 100)) : 0;
  return (
    <div>
      <div className="mb-1 flex justify-between text-xs text-neutral-400">
        <span>{label ?? "진행률"}</span>
        <span>
          {current}/{total} • {pct}%
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-neutral-800">
        <div
          className="h-full bg-emerald-500 transition-all duration-300"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
