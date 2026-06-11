import React from 'react';
import { PRECOMPUTED_QUIRKY_STATS, ALL_GAMES, TOURNAMENT_DATES, FRIENDS_LIST } from '../data/predictions';
import ClickableTeam from './ClickableTeam';
import { Award, Flame, ShieldAlert, Sparkles, TrendingUp, Info, User, HelpCircle, Swords, VolumeX, Shield, Heart } from 'lucide-react';

interface StatsViewProps {
  onTeamClick: (teamName: string) => void;
  onFriendClick: (friendName: string) => void;
}

export default function StatsView({ onTeamClick, onFriendClick }: StatsViewProps) {
  const stats = PRECOMPUTED_QUIRKY_STATS;

  // Render a mini podium for ranking metrics (Gold, Silver, Bronze)
  const renderPodium = (
    title: string,
    icon: React.ReactNode,
    data: { friend: string; scoreLabel: string | number }[],
    description: string,
    voltHighlight = false
  ) => {
    // Take top 3
    const podiumItems = data.slice(0, 3);
    
    // Sort array for physical placement: Silver (Index 1) on Left, Gold (Index 0) in Middle, Bronze (Index 2) on Right
    const physicalPodium = [];
    if (podiumItems[1]) physicalPodium.push({ item: podiumItems[1], rank: 2, bg: 'bg-slate-800 border-slate-700', rankColor: 'text-slate-400', height: 'h-24' });
    if (podiumItems[0]) physicalPodium.push({ item: podiumItems[0], rank: 1, bg: voltHighlight ? 'bg-gradient-to-t from-slate-950 to-world-volt/20 border-world-volt/60' : 'bg-gradient-to-t from-slate-950 to-amber-500/20 border-amber-500/10', rankColor: voltHighlight ? 'text-world-volt' : 'text-amber-400', height: 'h-32 shadow-xl shadow-world-volt/5' });
    if (podiumItems[2]) physicalPodium.push({ item: podiumItems[2], rank: 3, bg: 'bg-slate-900 border-slate-800/80', rankColor: 'text-amber-700', height: 'h-20' });

    return (
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-5 sm:p-6 shadow-xl flex flex-col justify-between">
        <div>
          {/* Header */}
          <div className="flex items-center gap-2 mb-2">
            <span className="p-2 bg-slate-950 rounded-xl border border-slate-850 text-world-volt flex-shrink-0">
              {icon}
            </span>
            <h3 className="font-display font-extrabold text-white text-base md:text-lg">
              {title}
            </h3>
          </div>
          <p className="text-xs text-slate-400 mb-6 leading-relaxed">
            {description}
          </p>
        </div>

        {/* The Graphic Podium blocks */}
        <div className="flex items-end justify-center gap-1.5 sm:gap-2 pt-6 border-t border-slate-800/40">
          {physicalPodium.map(({ item, rank, bg, rankColor, height }) => (
            <div key={item.friend} className="flex flex-col items-center flex-1">
              {/* Profile click shortcut */}
              <button
                onClick={() => onFriendClick(item.friend)}
                className="text-[10px] sm:text-xs font-bold text-center text-slate-200 hover:text-world-volt mb-2 transition truncate max-w-[70px] sm:max-w-[90px] cursor-pointer"
                title={`Click for ${item.friend}'s summary`}
              >
                {item.friend.split(' ')[0]}
              </button>
              
              {/* Podium Pillar */}
              <div className={`w-full ${height} ${bg} border-t border-x rounded-t-xl p-2 sm:p-3 flex flex-col items-center justify-between text-center`}>
                <span className={`font-display font-black text-sm sm:text-lg ${rankColor}`}>#{rank}</span>
                <div className="font-mono text-[9px] sm:text-xs font-bold text-white tracking-tight mt-1 truncate max-w-full">
                  {item.scoreLabel}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-8">
      
      {/* HEADER BANNER */}
      <div className="bg-gradient-to-r from-slate-900 via-violet-950/80 to-slate-900 border border-slate-800 rounded-3xl p-6 md:p-8 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 h-32 w-32 bg-world-volt/5 blur-3xl pointer-events-none" />
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div>
            <span className="text-xs font-bold text-world-volt uppercase tracking-widest flex items-center gap-1">
              <Award className="h-3.5 w-3.5 text-world-volt animate-bounce" /> FIFA 26 Special Analytics
            </span>
            <h1 className="text-2xl md:text-4xl font-display font-black text-white tracking-tight mt-1.5 uppercase leading-none">
              Quirky Stats Center
            </h1>
            <p className="text-sm text-slate-300 mt-2.5 max-w-2xl leading-relaxed">
              Diving deep into the 2,160 predicted score combinations of our 30 friends. Discover the extreme mavericks, the safe-bettors, the defense enthusiasts, and the patriots.
            </p>
          </div>
          
          {/* Micro global index stat */}
          <div className="bg-slate-950/80 border border-slate-805 px-5 py-4 rounded-2xl text-center self-stretch flex flex-col justify-center min-w-[120px]">
            <span className="text-slate-400 font-mono text-[9px] uppercase tracking-wider">Group consensus</span>
            <span className="text-2xl font-display font-black text-world-volt mt-1">{stats.mostPopularScoreOverall.score}</span>
            <span className="text-slate-500 font-sans text-[10px] mt-0.5">({stats.mostPopularScoreOverall.percent}% overlap)</span>
          </div>
        </div>
      </div>

      {/* THREE PODIUMS ROW: Mavericks, Conformists, Goal-Hungry */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {renderPodium(
          'Maverick Leaderboard 🌟',
          <Sparkles className="h-5 w-5" />,
          stats.maverickRank.map((m) => ({ friend: m.friend, scoreLabel: `${m.uniqueCount} unique` })),
          'Who showed the most courage? This tracks the amount of games where a friend made a predicted scoreline that absolutely NOBODY else in the group selected.',
          true
        )}

        {renderPodium(
          'Safe-Bettors/Conformists 🤝',
          <User className="h-5 w-5" />,
          stats.conformityRank.map((c) => ({ friend: c.friend, scoreLabel: `${c.avgOpponentsWithSameScore} avg co-voters` })),
          'Who predicted the most redundant/conservative scores? This measures the average number of other friends sharing their exact score prediction per game.',
          false
        )}

        {renderPodium(
          'Goal-Hungry Enthusiasts ⚽',
          <Flame className="h-5 w-5 text-orange-400" />,
          stats.goalHungryRank.map((g) => ({ friend: g.friend, scoreLabel: `${g.avgGoals} goals` })),
          'Who predictions expected the most goals? These guys predict attacking fiestas with zero respects to defensive systems.',
          false
        )}
      </div>

      {/* SECOND PODIUMS ROW: defensive Minded, Patriots */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* defensive masterminds podium */}
        {renderPodium(
          'Defensive Masterminds 🛡️',
          <Shield className="h-5 w-5" />,
          stats.defensiveMindedRank.map((d) => ({ friend: d.friend, scoreLabel: `${d.avgGoals} goals` })),
          'The clean-sheet advocates. These players predict low-scoring matches, tight tactical locks, and highly defensive football setups.',
          false
        )}

        {/* Global Match Dynamics Box */}
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="p-2 bg-slate-950 rounded-xl border border-slate-850 text-world-pink">
                <Swords className="h-5 w-5" />
              </span>
              <h3 className="font-display font-extrabold text-white text-base md:text-lg">
                Fixture Dynamics Outliers
              </h3>
            </div>
            <p className="text-xs text-slate-400 mb-6 font-medium">
              Which games in the 72 list saw the highest group consensus, and which ones split opinion completely?
            </p>
          </div>

          <div className="space-y-4 pt-4 border-t border-slate-800/40">
            {/* Divisive */}
            <div className="bg-slate-950/60 border border-red-950/40 rounded-2xl p-4 flex justify-between items-center text-xs">
              <div>
                <span className="text-[10px] font-bold text-rose-400 uppercase tracking-widest block mb-1">🔥 Most Divisive Match</span>
                <span className="font-display font-bold text-white text-sm">{stats.mostDivisiveGame.fixture}</span>
                <div className="text-slate-400 text-[10px] mt-0.5">Match No.{stats.mostDivisiveGame.matchNo}</div>
              </div>
              <div className="text-right">
                <span className="font-mono text-white font-extrabold text-base">{stats.mostDivisiveGame.uniqueScoresCount}</span>
                <span className="block text-[10px] text-slate-500">different predicted scores</span>
              </div>
            </div>

            {/* Consensus */}
            <div className="bg-slate-950/60 border border-emerald-950/40 rounded-2xl p-4 flex justify-between items-center text-xs">
              <div>
                <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-widest block mb-1">🤝 Most Unified Consensus</span>
                <span className="font-display font-bold text-white text-sm">{stats.mostConsensusGame.fixture}</span>
                <div className="text-slate-400 text-[10px] mt-0.5">Match No.{stats.mostConsensusGame.matchNo}</div>
              </div>
              <div className="text-right">
                <span className="font-mono text-world-volt font-black text-base">{stats.mostConsensusGame.percentage}%</span>
                <span className="block text-[10px] text-slate-400">agreed on <strong className="text-white">{stats.mostConsensusGame.consensusScore}</strong></span>
              </div>
            </div>
          </div>
        </div>

      </div>

      {/* NATIONAL PATRIOTICS & FANATICS */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl">
        <div className="flex items-center gap-2 mb-4 border-b border-slate-800 pb-4">
          <span className="p-2 bg-slate-950 rounded-xl border border-slate-850 text-world-pink">
            <Heart className="h-5 w-5 text-rose-500 animate-pulse" />
          </span>
          <div>
            <h3 className="font-display font-extrabold text-white text-base md:text-lg">
              National Patriots & Supporters
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">Which friends backing home nations or hosts (USA/Mexico/Canada) to win the highest amount of times?</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {/* England Fan */}
          {(() => {
            const sorted = [...stats.patriotsAndFanatics].sort((a, b) => b.englandWins - a.englandWins);
            const leader = sorted[0];
            return (
              <div className="bg-slate-950/50 border border-slate-800/80 rounded-2xl p-4 text-center">
                <span className="text-2xl block mb-1">🏴󠁧󠁢󠁥󠁮󠁧󠁿</span>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">England Believer</span>
                <strong className="text-xs text-white block mt-2 truncate">{leader?.friend || 'N/A'}</strong>
                <span className="font-mono text-world-volt font-bold text-xs block mt-1">{leader?.englandWins} wins predicted</span>
              </div>
            );
          })()}

          {/* Scotland Fan */}
          {(() => {
            const sorted = [...stats.patriotsAndFanatics].sort((a, b) => b.scotlandWins - a.scotlandWins);
            const leader = sorted[0];
            return (
              <div className="bg-slate-950/50 border border-slate-800/80 rounded-2xl p-4 text-center">
                <span className="text-2xl block mb-1">🏴󠁧󠁢󠁳󠁣󠁴󠁿</span>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Scotland Believer</span>
                <strong className="text-xs text-white block mt-2 truncate">{leader?.friend || 'N/A'}</strong>
                <span className="font-mono text-cyan-400 font-bold text-xs block mt-1">{leader?.scotlandWins} wins predicted</span>
              </div>
            );
          })()}

          {/* USA Fan */}
          {(() => {
            const sorted = [...stats.patriotsAndFanatics].sort((a, b) => b.usaWins - a.usaWins);
            const leader = sorted[0];
            return (
              <div className="bg-slate-950/50 border border-slate-800/80 rounded-2xl p-4 text-center">
                <span className="text-2xl block mb-1">🇺🇸</span>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">USA Supporter</span>
                <strong className="text-xs text-white block mt-2 truncate">{leader?.friend || 'N/A'}</strong>
                <span className="font-mono text-rose-450 font-bold text-xs block mt-1">{leader?.usaWins} wins predicted</span>
              </div>
            );
          })()}

          {/* Mexico Fan */}
          {(() => {
            const sorted = [...stats.patriotsAndFanatics].sort((a, b) => b.mexicoWins - a.mexicoWins);
            const leader = sorted[0];
            return (
              <div className="bg-slate-950/50 border border-slate-800/80 rounded-2xl p-4 text-center">
                <span className="text-2xl block mb-1">🇲🇽</span>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Mexico Believer</span>
                <strong className="text-xs text-white block mt-2 truncate">{leader?.friend || 'N/A'}</strong>
                <span className="font-mono text-emerald-400 font-bold text-xs block mt-1">{leader?.mexicoWins} wins predicted</span>
              </div>
            );
          })()}

          {/* Canada Fan */}
          {(() => {
            const sorted = [...stats.patriotsAndFanatics].sort((a, b) => b.canadaWins - a.canadaWins);
            const leader = sorted[0];
            return (
              <div className="bg-slate-950/50 border border-slate-800/80 rounded-2xl p-4 text-center">
                <span className="text-2xl block mb-1">🇨🇦</span>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Canada Believer</span>
                <strong className="text-xs text-white block mt-2 truncate">{leader?.friend || 'N/A'}</strong>
                <span className="font-mono text-slate-350 font-bold text-xs block mt-1">{leader?.canadaWins} wins predicted</span>
              </div>
            );
          })()}
        </div>
      </div>

      {/* THE WILDEST SCORE PREDICTIONS LIST */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl space-y-4">
        <div>
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <ShieldAlert className="h-4 w-4 text-red-500 animate-pulse" /> Extreme Score Predictions Archive
          </span>
          <h3 className="font-display font-extrabold text-white text-base md:text-lg mt-1">
            The Wildest Outlier Scorelines (6+ Goals predicted)
          </h3>
          <p className="text-xs text-slate-400">These predictions represent hilarious outstanding choices predicting extreme high score margins.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pt-2">
          {stats.wildestPredictions.map((wild, i) => (
            <div 
              key={`${wild.matchNo}-${wild.friend}-${i}`}
              className="bg-slate-950/60 border border-slate-800/80 rounded-2xl p-4 flex flex-col justify-between"
            >
              <div className="flex justify-between items-start">
                <div>
                  <span className="text-[10px] font-mono font-bold text-slate-500">Match No.{wild.matchNo} • {wild.date}</span>
                  <div className="font-display font-bold text-slate-200 text-sm mt-1">
                    {wild.fixture}
                  </div>
                </div>
                
                <span className="text-sm font-display font-black bg-gradient-to-r from-red-500 to-rose-600 text-white px-2.5 py-1 rounded-xl shadow border border-red-500/30 font-bold">
                  {wild.score}
                </span>
              </div>

              <div className="border-t border-slate-800/50 mt-4 pt-3 flex items-center justify-between">
                <span className="text-[10px] text-slate-400 font-medium">Predicted By:</span>
                <button
                  onClick={() => onFriendClick(wild.friend)}
                  className="text-xs font-bold text-world-volt hover:underline flex items-center gap-1 cursor-pointer"
                >
                  <User className="h-3.5 w-3.5" />
                  {wild.friend}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}
