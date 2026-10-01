import { t } from "../i18n";

export type Tier = "SAFE" | "CAUTION" | "HIGH_RISK";

interface ResultCardProps {
  tier: Tier;
  score: number;
  category: string;
  reasons: string[];
  advice: string[];
  explanation?: string;
  lang?: string;
}

const TIER_STYLES: Record<
  Tier,
  { bg: string; border: string; text: string; badge: string; icon: string; label: string }
> = {
  SAFE: {
    bg: "bg-green-50",
    border: "border-green-200",
    text: "text-green-800",
    badge: "bg-green-100 text-green-800",
    icon: "✓",
    label: "Safe",
  },
  CAUTION: {
    bg: "bg-yellow-50",
    border: "border-yellow-200",
    text: "text-yellow-800",
    badge: "bg-yellow-100 text-yellow-800",
    icon: "⚠",
    label: "Caution",
  },
  HIGH_RISK: {
    bg: "bg-red-50",
    border: "border-red-200",
    text: "text-red-800",
    badge: "bg-red-100 text-red-800",
    icon: "✗",
    label: "High Risk",
  },
};

export function ResultCard({
  tier,
  score,
  category,
  reasons,
  advice,
  explanation,
  lang = "en",
}: ResultCardProps) {
  const s = TIER_STYLES[tier];

  return (
    <div className={`rounded-2xl border-2 ${s.bg} ${s.border} p-5 space-y-4`}>
      {/* Tier header — colour + icon + text label (WCAG 1.4.1) */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className={`flex items-center gap-2 ${s.text}`}>
          <span
            className={`w-9 h-9 rounded-full ${s.badge} flex items-center justify-center text-lg font-bold`}
            aria-hidden="true"
          >
            {s.icon}
          </span>
          <div>
            <div className="font-bold text-lg leading-tight">{s.label}</div>
            <div className="text-xs opacity-75">
              {t(`tier.${tier.toLowerCase()}.description`, lang)}
            </div>
          </div>
        </div>
        {/* Score badge */}
        <span
          className={`${s.badge} text-sm font-semibold px-3 py-1 rounded-full`}
          aria-label={`Risk score ${score} out of 100`}
        >
          {score}/100
        </span>
      </div>

      {/* Category */}
      <div>
        <span className="text-xs font-semibold uppercase tracking-wider text-mukuru-gray">
          {t("scan.result.category", lang)}
        </span>
        <p className={`font-semibold mt-0.5 ${s.text}`}>
          {t(`category.${category}`, lang)}
        </p>
      </div>

      {/* Reasons (max 3) */}
      {reasons.length > 0 && (
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-mukuru-gray">
            {t("scan.result.reasons_title", lang)}
          </span>
          <ul className="mt-1.5 space-y-1">
            {reasons.slice(0, 3).map((code) => (
              <li key={code} className="flex items-start gap-2 text-sm">
                <span
                  className={`mt-0.5 shrink-0 ${s.text} font-bold`}
                  aria-hidden="true"
                >
                  •
                </span>
                <span className="text-mukuru-navy">
                  {t(`reason.${code.toLowerCase()}`, lang)}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Advice */}
      {advice.length > 0 && (
        <div className="bg-white/70 rounded-xl p-4 space-y-1.5">
          <span className="text-xs font-semibold uppercase tracking-wider text-mukuru-gray block mb-2">
            {t("scan.result.advice_title", lang)}
          </span>
          {advice.slice(0, 3).map((code) => (
            <p key={code} className="text-sm text-mukuru-navy flex items-start gap-2">
              <span className="text-mukuru-green font-bold shrink-0 mt-0.5" aria-hidden="true">→</span>
              {t(`advice.${code.toLowerCase()}`, lang)}
            </p>
          ))}
        </div>
      )}

      {/* Optional explanation */}
      {explanation && (
        <p className="text-xs text-mukuru-gray italic border-t border-current/10 pt-3">
          {explanation}
        </p>
      )}
    </div>
  );
}
