import React from 'react';
import { X, Trophy, AlertCircle, Calendar, Sparkles, TrendingUp } from 'lucide-react';
import { getTeamPredictionsStats, parseScore } from '../data/predictions';

interface TeamStatsModalProps {
  teamName: string;
  onClose: () => void;
}

export default function TeamStatsModal({ teamName, onClose }: TeamStatsModalProps) {
  const stats = getTeamPredictionsStats(teamName);

  // Determine standard team initials/monogram
  const initials = teamName
    .split(/\s+/)
    .slice(0, 2)
    .map((word) => word[0])
    .join('')
    .toUpperCase();

  // Pick a stylized color theme for team initials badge based on first letter
  const getBadgeColor = (name: string) => {
    const code = name.charCodeAt(0) % 5;
    switch (code) {
      case 0: return 'from-pink-500 to-rose-600 shadow-pink-900/30';
      case 1: return 'from-cyan-500 to-blue-600 shadow-cyan-900/30';
      case 2: return 'from-amber-400 to-amber-600 shadow-amber-900/30';
      case 3: return 'from-emerald-500 to-teal-600 shadow-emerald-900/30';
      default: return 'from-violet-500 to-fuchsia-600 shadow-violet-900/30';
    }
  };

  // Find the most popular prediction
  const topPrediction = stats.scoreOccurrences[0];
  const totalOccurrences = stats.scoreOccurrences.reduce((acc, curr) => acc + curr.count, 0);

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-world-navy/85 backdrop-blur-md transition-opacity duration-300"
        onClick={onClose}
      />
      
      {/* Modal Container */}
      <div 
        className="relative w-full max-w-2xl max-h-[92vh] sm:max-h-[85vh] overflow-y-auto rounded-t-[32px] sm:rounded-3xl bg-slate-900 border-t sm:border border-slate-800 shadow-2xl shadow-world-volt/10 p-5 sm:p-6 md:p-8 animate-in fade-in slide-in-from-bottom-12 sm:zoom-in-95 duration-300"
        id="team-stats-modal"
      >
        {/* Mobile Swipe/Pull Handle Indicator */}
        <div className="w-12 h-1 bg-slate-800 rounded-full mx-auto mb-3 block sm:hidden cursor-pointer" onClick={onClose} />

        {/* Header Close Button */}
        <button 
          onClick={onClose}
          className="absolute right-4 top-4 sm:right-5 sm:top-5 rounded-full p-2 text-slate-400 hover:bg-slate-800 hover:text-white transition-all cursor-pointer"
          aria-label="Close"
          id="close-modal-btn"
        >
          <X className="h-5 w-5 sm:h-6 sm:w-6" />
        </button>

        {/* Modal Header */}
        <div className="flex flex-col sm:flex-row items-center gap-4 sm:gap-5 pb-5 sm:pb-6 border-b border-slate-800">
          <div className={`flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br ${getBadgeColor(teamName)} text-white font-display font-black text-2xl shadow-lg ring-4 ring-slate-800/50`}>
            {initials}
          </div>
          <div className="text-center sm:text-left">
            <div className="text-xs font-bold text-world-volt uppercase tracking-widest flex items-center justify-center sm:justify-start gap-1">
              <Trophy className="h-3 w-3 inline" /> FIFA World Cup 2026 Team Stats
            </div>
            <h2 className="text-2xl md:text-3xl font-display font-extrabold text-white tracking-tight mt-1">
              {teamName}
            </h2>
            <p className="text-sm text-slate-400 mt-1">
              Analyzing predictions across all 72 competition matches
            </p>
          </div>
        </div>

        {/* Modal Content Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
          
          {/* LEFT COLUMN: All Score Occurrences (Requested) */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-bold text-white tracking-wide uppercase flex items-center gap-1.5">
                <TrendingUp className="h-4 w-4 text-world-volt" /> Score Occurrences
              </span>
              <span className="text-xs text-slate-400 font-mono">
                {totalOccurrences} total votes
              </span>
            </div>

            {/* Unique score stats info box */}
            {topPrediction && (
              <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3 text-xs flex gap-2.5 items-center">
                <Sparkles className="h-5 w-5 text-world-volt flex-shrink-0" />
                <div>
                  <span className="text-slate-300">Conformist Choice: </span>
                  <strong className="text-world-volt">{topPrediction.score}</strong> is the most predicted scoreline, appearing <strong className="text-slate-200">{topPrediction.count} times</strong> ({Math.round((topPrediction.count / totalOccurrences) * 100)}% of predictions).
                </div>
              </div>
            )}

            {/* Occurrence List with horizontal bars */}
            <div className="space-y-2.5 max-h-[300px] overflow-y-auto pr-1">
              {stats.scoreOccurrences.map((item, i) => {
                const percentage = Math.round((item.count / totalOccurrences) * 100);
                
                // Color grades for visualization bars
                let barColor = 'bg-world-volt/60';
                if (i === 0) barColor = 'bg-gradient-to-r from-world-volt to-emerald-500';
                else if (i < 3) barColor = 'bg-slate-500';
                else barColor = 'bg-slate-700/60';

                return (
                  <div key={item.score} className="bg-slate-950/30 hover:bg-slate-950/70 border border-slate-800/40 rounded-lg p-2.5 transition-all">
                    <div className="flex justify-between items-center text-xs font-mono mb-1.5">
                      <span className="text-white font-bold bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                        {item.score}
                      </span>
                      <span className="text-slate-400">
                        <strong className="text-white">{item.count}</strong> {item.count === 1 ? 'vote' : 'votes'} ({percentage}%)
                      </span>
                    </div>
                    {/* The bar */}
                    <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                      <div 
                        className={`h-full rounded-full ${barColor}`} 
                        style={{ width: `${Math.max(percentage, 2)}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* RIGHT COLUMN: Fixtures Schedule & Oriented Results */}
          <div className="space-y-5">
            {/* Predicted Outcome breakdown */}
            <div>
              <span className="text-sm font-bold text-white tracking-wide uppercase flex items-center gap-1.5 mb-3">
                <Trophy className="h-4 w-4 text-world-pink" /> Prediction Outcome Profile
              </span>
              <div className="grid grid-cols-3 gap-2 text-center text-xs">
                {/* Wins, Draws, Losses counts based on orientated scores */}
                {(() => {
                  let wins = 0;
                  let draws = 0;
                  let losses = 0;
                  
                  stats.scorePredictions.forEach(sp => {
                    if (sp.scoreRoot.startsWith('Win')) wins += sp.count;
                    else if (sp.scoreRoot.startsWith('Draw')) draws += sp.count;
                    else if (sp.scoreRoot.startsWith('Loss')) losses += sp.count;
                  });

                  const total = wins + draws + losses || 1;
                  const winPercent = Math.round((wins / total) * 100);
                  const drawPercent = Math.round((draws / total) * 100);
                  const lossPercent = Math.round((losses / total) * 100);

                  return (
                    <>
                      <div className="bg-emerald-950/30 border border-emerald-900/40 p-2.5 rounded-xl">
                        <div className="text-emerald-400 font-extrabold text-base">{winPercent}%</div>
                        <div className="text-slate-400 text-[10px] mt-0.5 uppercase tracking-wider">To Win</div>
                        <div className="text-slate-500 text-[9px] font-mono">({wins} predictions)</div>
                      </div>
                      <div className="bg-slate-900 border border-slate-800/80 p-2.5 rounded-xl">
                        <div className="text-slate-300 font-extrabold text-base">{drawPercent}%</div>
                        <div className="text-slate-400 text-[10px] mt-0.5 uppercase tracking-wider">To Draw</div>
                        <div className="text-slate-500 text-[9px] font-mono">({draws} predictions)</div>
                      </div>
                      <div className="bg-red-950/35 border border-red-900/30 p-2.5 rounded-xl">
                        <div className="text-rose-400 font-extrabold text-base">{lossPercent}%</div>
                        <div className="text-slate-400 text-[10px] mt-0.5 uppercase tracking-wider">To Lose</div>
                        <div className="text-slate-500 text-[9px] font-mono">({losses} predictions)</div>
                      </div>
                    </>
                  );
                })()}
              </div>
            </div>

            {/* Fixture games list involving this team */}
            <div>
              <span className="text-sm font-bold text-white tracking-wide uppercase flex items-center gap-1.5 mb-3">
                <Calendar className="h-4 w-4 text-world-volt" /> Match Schedule ({stats.totalGames})
              </span>
              <div className="space-y-2 max-h-[220px] overflow-y-auto pr-1">
                {stats.gamesList.map((game) => (
                  <div key={game.matchNo} className="bg-slate-950/50 border border-slate-800/60 rounded-xl p-3 flex justify-between items-center text-xs">
                    <div>
                      <div className="text-slate-400 font-mono text-[10px] flex items-center gap-1">
                        <span>Match {game.matchNo}</span> • <span>{game.date}</span>
                      </div>
                      <div className="font-semibold text-slate-200 mt-1">
                        {game.fixture}
                      </div>
                    </div>
                    <div>
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        game.isHome 
                          ? 'bg-cyan-950 text-cyan-400 border border-cyan-900' 
                          : 'bg-indigo-950 text-indigo-400 border border-indigo-900'
                      }`}>
                        {game.isHome ? 'Home' : 'Away'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

          </div>
        </div>

        {/* Footer info disclosure */}
        <div className="mt-8 pt-5 border-t border-slate-800/70 text-center text-[10px] text-slate-500 flex items-center justify-center gap-1.5">
          <AlertCircle className="h-3 w-3 text-slate-500" />
          Clicking any team in the Selections Explorer opens this interactive occurrence panel.
        </div>
      </div>
    </div>
  );
}
