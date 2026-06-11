import React from 'react';
import { Shield } from 'lucide-react';

interface ClickableTeamProps {
  name: string;
  onClick: (teamName: string) => void;
  className?: string;
  showIcon?: boolean;
}

// Map country names to flag emojis for high-fidelity presentation
export const TEAM_FLAGS: Record<string, string> = {
  'Mexico': '🇲🇽',
  'South Africa': '🇿🇦',
  'South Korea': '🇰🇷',
  'Czech Republic': '🇨🇿',
  'Canada': '🇨🇦',
  'Bosnia': '🇧🇦',
  'USA': '🇺🇸',
  'Paraguay': '🇵🇾',
  'Qatar': '🇶🇦',
  'Switzerland': '🇨🇭',
  'Brazil': '🇧🇷',
  'Morocco': '🇲🇦',
  'Haiti': '🇭🇹',
  'Scotland': '🏴󠁧󠁢󠁳󠁣󠁴󠁿',
  'Australia': '🇦🇺',
  'Turkey': '🇹🇷',
  'Germany': '🇩🇪',
  'Curacao': '🇨🇼',
  'Japan': '🇯🇵',
  'Netherlands': '🇳🇱',
  'Ivory Coast': '🇨🇮',
  'Ecuador': '🇪🇨',
  'Sweden': '🇸🇪',
  'Tunisia': '🇹🇳',
  'Spain': '🇪🇸',
  'Cabo Verde': '🇨🇻',
  'Caboi Verde': '🇨🇻', // supporting typo as parsed from CSV
  'Belgium': '🇧🇪',
  'Egypt': '🇪🇬',
  'Saudi Arabia': '🇸🇦',
  'Uruguay': '🇺🇾',
  'Iran': '🇮🇷',
  'New Zealand': '🇳🇿',
  'France': '🇫🇷',
  'Senegal': '🇸🇳',
  'Iraq': '🇮🇶',
  'Norway': '🇳🇴',
  'Argentina': '🇦🇷',
  'Algeria': '🇩🇿',
  'Austria': '🇦🇹',
  'Jordan': '🇯🇴',
  'Portugal': '🇵🇹',
  'Congo DR': '🇨🇩',
  'England': '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
  'Croatia': '🇭🇷',
  'Ghana': '🇬🇭',
  'Panama': '🇵🇦',
  'Uzbekistan': '🇺🇿',
  'Columbia': '🇨🇴',
};

export default function ClickableTeam({ name, onClick, className = '', showIcon = true }: ClickableTeamProps) {
  const flag = TEAM_FLAGS[name.trim()] || '🏳️';

  return (
    <button
      type="button"
      onClick={() => onClick(name)}
      className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-lg hover:bg-slate-800/80 hover:text-world-volt text-slate-200 transition-all cursor-pointer font-medium border border-transparent hover:border-slate-700/50 text-left active:scale-95 ${className}`}
      title={`Click to view ${name} prediction data`}
    >
      {showIcon && <span className="text-sm select-none">{flag}</span>}
      <span className="underline decoration-dotted decoration-slate-500 hover:decoration-world-volt underline-offset-4">
        {name}
      </span>
    </button>
  );
}
