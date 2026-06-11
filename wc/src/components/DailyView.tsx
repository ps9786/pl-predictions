import React, { useMemo } from 'react';
import { TOURNAMENT_DATES, ALL_GAMES, getGameScoreGroups, Game, ScoreGroup } from '../data/predictions';
import ClickableTeam from './ClickableTeam';
import { Calendar, ChevronLeft, ChevronRight, User, Sparkles, SlidersHorizontal, Info, Award } from 'lucide-react';

interface DailyViewProps {
  selectedDate: string;
  setSelectedDate: (date: string) => void;
  onTeamClick: (teamName: string) => void;
  onFriendClick: (friendName: string) => void;
}

export default function DailyView({ selectedDate, setSelectedDate, onTeamClick, onFriendClick }: DailyViewProps) {
  // Find current index of date
  const dateIndex = useMemo(() => {
    const idx = TOURNAMENT_DATES.indexOf(selectedDate);
    return idx === -1 ? 0 : idx;
  }, [selectedDate]);

  // Handler to navigate left/right through dates
  const handlePrevDate = () => {
    if (dateIndex > 0) {
      setSelectedDate(TOURNAMENT_DATES[dateIndex - 1]);
    }
  };

  const handleNextDate = () => {
    if (dateIndex < TOURNAMENT_DATES.length - 1) {
      setSelectedDate(TOURNAMENT_DATES[dateIndex + 1]);
    }
  };

  // Find all games on this selected date
  const gamesOnDate = useMemo(() => {
    return ALL_GAMES.filter((g) => g.date === selectedDate);
  }, [selectedDate]);

  return (
    <div className="space-y-6">
      
      {/* SECTION: Date Navigation Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-4 md:p-6 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <span className="text-xs font-bold text-world-volt uppercase tracking-widest flex items-center gap-1">
              <Calendar className="h-3 w-3 inline" /> Competition Timeline
            </span>
            <h2 className="text-xl md:text-2xl font-display font-extrabold text-white tracking-tight mt-1">
              Matchday Explorer
            </h2>
          </div>

          <div className="flex items-center gap-3">
            {/* Quick Dropdown selector */}
            <div className="relative">
              <select
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="appearance-none bg-slate-950 border border-slate-800 text-slate-200 text-sm rounded-xl px-4 py-2.5 pr-10 focus:outline-none focus:ring-2 focus:ring-world-volt/40 font-semibold cursor-pointer w-full sm:w-48"
                id="date-select-dropdown"
              >
                {TOURNAMENT_DATES.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-3 flex items-center text-slate-400">
                <ChevronRight className="h-4 w-4 rotate-90" />
              </div>
            </div>

            {/* Stepper buttons */}
            <div className="flex gap-1.5 bg-slate-950 p-1 rounded-xl border border-slate-800">
              <button
                onClick={handlePrevDate}
                disabled={dateIndex === 0}
                className="p-1 px-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-900 disabled:opacity-30 disabled:hover:bg-transparent disabled:hover:text-slate-400 transition"
                title="Previous Day"
              >
                <ChevronLeft className="h-5 w-5" />
              </button>
              <button
                onClick={handleNextDate}
                disabled={dateIndex === TOURNAMENT_DATES.length - 1}
                className="p-1 px-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-900 disabled:opacity-30 disabled:hover:bg-transparent disabled:hover:text-slate-400 transition"
                title="Next Day"
              >
                <ChevronRight className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Horizontal scrollable date pills */}
        <div className="flex gap-2 overflow-x-auto pb-2 -mx-2 px-2 border-t border-slate-800/60 pt-4 scroll-smooth snap-x scrollbar-none">
          {TOURNAMENT_DATES.map((d, index) => {
            const isActive = d === selectedDate;
            const gamesCount = ALL_GAMES.filter((g) => g.date === d).length;
            
            return (
              <button
                key={d}
                type="button"
                onClick={() => setSelectedDate(d)}
                className={`flex-shrink-0 px-4 py-2.5 rounded-2xl border text-xs font-semibold transition-all duration-200 flex flex-col items-center min-w-[90px] cursor-pointer snap-center ${
                  isActive
                    ? 'bg-world-volt text-slate-950 border-world-volt font-bold scale-105 shadow-md shadow-world-volt/10'
                    : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700/80 hover:text-slate-200'
                }`}
              >
                <span>{d.split(' ')[0]}</span>
                <span className={`text-[10px] uppercase font-bold tracking-tight mt-0.5 ${isActive ? 'text-slate-800' : 'text-slate-500'}`}>
                  {d.split(' ')[1]}
                </span>
                <div className={`mt-1 h-1.5 w-1.5 rounded-full ${isActive ? 'bg-slate-950' : 'bg-world-volt/60'}`} />
              </button>
            );
          })}
        </div>
      </div>

      {/* SECTION: Matches & Predictions list */}
      <div className="space-y-6">
        {gamesOnDate.length === 0 ? (
          <div className="text-center py-12 bg-slate-900 border border-slate-800 rounded-3xl">
            <Info className="h-10 w-10 text-slate-500 mx-auto mb-3 animate-pulse" />
            <p className="text-slate-400 font-medium">No games scheduled on {selectedDate}.</p>
          </div>
        ) : (
          gamesOnDate.map((game, gameIdx) => {
            const scoreGroups = getGameScoreGroups(game);

            return (
              <div
                key={game.matchNo}
                className="bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden shadow-xl"
                id={`game-card-${game.matchNo}`}
              >
                
                {/* Match Card Header Banner */}
                <div className="bg-slate-950/80 p-5 md:p-6 border-b border-slate-800/80 flex flex-col md:flex-row items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-world-purple border border-world-pink/30 text-world-volt font-mono text-xs font-bold shadow">
                      {game.matchNo}
                    </span>
                    <div>
                      <h3 className="text-sm font-semibold text-slate-400 flex items-center gap-2">
                        <span>FIFA Matches</span>
                        <span className="h-1 w-1 bg-slate-600 rounded-full" />
                        <span>Matchday #{game.matchNo}</span>
                      </h3>
                      <div className="text-xs text-slate-500 mt-0.5">{game.date} Tournament Stage</div>
                    </div>
                  </div>

                  {/* Interacting Teams */}
                  <div className="flex items-center gap-2 font-display text-base md:text-lg font-black text-white">
                    <ClickableTeam name={game.homeTeam} onClick={onTeamClick} />
                    <span className="text-xs font-bold px-2 py-1 rounded bg-slate-850 border border-slate-800 text-world-pink font-sans">
                      VS
                    </span>
                    <ClickableTeam name={game.awayTeam} onClick={onTeamClick} />
                  </div>
                </div>

                {/* Selections Space */}
                <div className="p-6 space-y-6">
                  
                  {/* Explanatory notes */}
                  <div className="flex items-center justify-between border-b border-slate-800/40 pb-4">
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                      <SlidersHorizontal className="h-3.5 w-3.5 text-world-volt" /> 
                      Predictions Grouped in Order of Scores ({scoreGroups.length} unique scorelines)
                    </span>
                    <span className="text-[10px] bg-slate-955 text-slate-400 px-2 py-0.5 rounded-md font-mono border border-slate-800">
                      30 Predictors
                    </span>
                  </div>

                  {/* Scores Grid Ordered Numerically */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                    {scoreGroups.map((group) => {
                      return (
                        <div
                          key={group.score}
                          className={`flex flex-col justify-between rounded-2xl p-4 border transition-all duration-200 relative overflow-hidden group ${
                            group.isUnique
                              ? 'bg-gradient-to-br from-amber-950/20 via-slate-900 to-amber-950/5 border-amber-500/50 shadow-lg shadow-amber-950/20 shadow-inner'
                              : 'bg-slate-950/50 border-slate-800 hover:border-slate-700/80 hover:bg-slate-950'
                          }`}
                        >
                          
                          {/* Top row of prediction tile */}
                          <div className="flex justify-between items-start mb-3">
                            <div className="flex items-center gap-2">
                              <span className={`font-display font-extrabold text-xl md:text-2xl px-3 py-1 rounded-xl shadow-inner ${
                                group.isUnique 
                                  ? 'bg-amber-400 text-slate-950 text-neon-glow font-black' 
                                  : 'bg-slate-900 text-world-volt border border-slate-800'
                              }`}>
                                {group.score}
                              </span>
                              
                              {group.isUnique && (
                                <span className="flex items-center gap-0.5 text-[9px] font-extrabold uppercase tracking-widest text-amber-400 bg-amber-950/80 px-2 py-1 rounded-lg border border-amber-900/60 animate-pulse">
                                  <Sparkles className="h-2.5 w-2.5 text-amber-400" /> Maverick
                                </span>
                              )}
                            </div>
                            
                            <span className="text-xs font-mono font-bold text-slate-400 bg-slate-900 border border-slate-800/80 px-2 py-1 rounded-lg">
                              {group.count} {group.count === 1 ? 'player' : 'players'}
                            </span>
                          </div>

                          {/* Friends list under this score */}
                          <div className="flex flex-wrap gap-1.5 mt-2">
                            {group.friends.map((friendObj) => (
                              <button
                                key={friendObj.name}
                                onClick={() => onFriendClick(friendObj.name)}
                                className={`text-[11px] font-semibold px-2 py-1 rounded-lg transition active:scale-95 text-left border cursor-pointer ${
                                  friendObj.isUnique
                                    ? 'bg-amber-950/70 border-amber-700 text-amber-300 hover:bg-amber-900 hover:text-white'
                                    : 'bg-slate-900 border-slate-800 text-slate-300 hover:bg-slate-850 hover:text-white hover:border-slate-700'
                                }`}
                                title={`Click to view ${friendObj.name}'s tournament profile`}
                              >
                                <span className="inline-flex items-center gap-1">
                                  <User className="h-2.5 w-2.5 opacity-60" />
                                  {friendObj.name}
                                </span>
                              </button>
                            ))}
                          </div>

                          {/* Subtle highlight visual effect code */}
                          {group.isUnique && (
                            <div className="absolute top-0 right-0 h-10 w-10 bg-gradient-to-bl from-amber-400/10 to-transparent -rotate-45 pointer-events-none" />
                          )}
                        </div>
                      );
                    })}
                  </div>

                </div>

                {/* Quick Info Box */}
                <div className="bg-slate-950/40 px-6 py-3.5 border-t border-slate-800/50 flex flex-wrap gap-3 text-[11px] text-slate-500 justify-between items-center">
                  <div className="flex items-center gap-1.5">
                    <Info className="h-3.5 w-3.5 text-slate-500" />
                    <span>Ordered elegantly in score magnitude (home goals, then away goals).</span>
                  </div>
                  <div>
                    <span>Holders: </span>
                    <strong className="text-slate-400 font-medium">Click on any name or team</strong> to navigate databases.
                  </div>
                </div>

              </div>
            );
          })
        )}
      </div>

    </div>
  );
}
