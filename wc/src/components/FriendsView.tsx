import React, { useState, useMemo } from 'react';
import { FRIENDS_LIST, ALL_GAMES, parseScore, Game, Prediction } from '../data/predictions';
import ClickableTeam from './ClickableTeam';
import { User, Search, Award, Shield, Percent, Sparkles, Flame, SlidersHorizontal, Info, RefreshCw, Calendar } from 'lucide-react';

interface FriendsViewProps {
  selectedFriend: string;
  setSelectedFriend: (name: string) => void;
  onTeamClick: (teamName: string) => void;
}

export default function FriendsView({ selectedFriend, setSelectedFriend, onTeamClick }: FriendsViewProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<'all' | 'unique' | 'draws' | 'high_scoring'>('all');

  // Load all predictions for this selected friend
  const friendData = useMemo(() => {
    let totalGoals = 0;
    let homeWins = 0;
    let awayWins = 0;
    let draws = 0;
    let uniqueCount = 0;
    
    // Track most predicted score
    const scoreCounts: Record<string, number> = {};

    const predictionsList = ALL_GAMES.map((game) => {
      const pred = game.predictions.find((p) => p.friend === selectedFriend);
      if (!pred) return null;

      const { home, away } = parseScore(pred.score);
      totalGoals += home + away;
      
      if (home > away) homeWins++;
      else if (away > home) awayWins++;
      else draws++;

      if (pred.isUnique) uniqueCount++;

      scoreCounts[pred.score] = (scoreCounts[pred.score] || 0) + 1;

      return {
        game,
        prediction: pred,
        homeGoals: home,
        awayGoals: away,
        totalGoals: home + away,
      };
    }).filter(Boolean) as {
      game: Game;
      prediction: Prediction;
      homeGoals: number;
      awayGoals: number;
      totalGoals: number;
    }[];

    // Calculate favorite score
    let favoriteScore = 'N/A';
    let favoriteCount = 0;
    Object.keys(scoreCounts).forEach((score) => {
      if (scoreCounts[score] > favoriteCount) {
        favoriteCount = scoreCounts[score];
        favoriteScore = score;
      }
    });

    const avgGoals = predictionsList.length > 0 ? (totalGoals / predictionsList.length).toFixed(2) : '0';

    return {
      predictionsList,
      stats: {
        totalPredictions: predictionsList.length,
        totalGoals,
        avgGoals,
        homeWins,
        awayWins,
        draws,
        uniqueCount,
        favoriteScore,
        favoriteCount,
      },
    };
  }, [selectedFriend]);

  // Handle Search and Filter mapping
  const filteredPredictions = useMemo(() => {
    return friendData.predictionsList.filter((item) => {
      const homeMatch = item.game.homeTeam.toLowerCase().includes(searchTerm.toLowerCase());
      const awayMatch = item.game.awayTeam.toLowerCase().includes(searchTerm.toLowerCase());
      const fixtureMatch = item.game.fixture.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesSearch = homeMatch || awayMatch || fixtureMatch;

      if (!matchesSearch) return false;

      if (filterType === 'unique') {
        return item.prediction.isUnique;
      }
      if (filterType === 'draws') {
        return item.homeGoals === item.awayGoals;
      }
      if (filterType === 'high_scoring') {
        return item.totalGoals >= 4;
      }

      return true;
    });
  }, [friendData, searchTerm, filterType]);

  // Order of friend select cards
  const sortedFriends = useMemo(() => {
    return [...FRIENDS_LIST];
  }, []);

  return (
    <div className="space-y-6">

      {/* TOP EXPLORER: Dropdown or Grid to select Friend */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div>
            <span className="text-xs font-bold text-world-volt uppercase tracking-widest flex items-center gap-1">
              <User className="h-3 w-3 inline animate-pulse" /> Competitive Profiles
            </span>
            <h2 className="text-xl md:text-2xl font-display font-extrabold text-white tracking-tight mt-1">
              Friends Selection Hub
            </h2>
            <p className="text-sm text-slate-400 mt-1">Select any companion to view their complete 72 tournament picks.</p>
          </div>

          {/* Core dropdown selector */}
          <div className="relative w-full md:w-64">
            <select
              value={selectedFriend}
              onChange={(e) => {
                setSelectedFriend(e.target.value);
                setSearchTerm('');
                setFilterType('all');
              }}
              className="appearance-none bg-slate-950 border border-slate-800 text-slate-200 text-sm rounded-xl px-4 py-3 pr-10 focus:outline-none focus:ring-2 focus:ring-world-volt/40 font-bold cursor-pointer w-full"
              id="friend-select-dropdown"
            >
              {sortedFriends.map((fName) => (
                <option key={fName} value={fName}>
                  {fName}
                </option>
              ))}
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-3 flex items-center text-slate-400">
              <User className="h-4 w-4" />
            </div>
          </div>
        </div>

        {/* Rapid-select alphabetical list of friends for widescreen and touch swipers for mobile */}
        <div className="mt-4 pt-4 border-t border-slate-800/50">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 block mb-2 sm:hidden px-1">
            Swipe to select companion:
          </span>
          <div className="flex gap-2 overflow-x-auto pb-2 -mx-2 px-2 scrollbar-thin scrollbar-thumb-slate-800 scroll-smooth snap-x">
            {sortedFriends.map((fName) => {
              const isSelected = fName === selectedFriend;
              return (
                <button
                  key={fName}
                  onClick={() => {
                    setSelectedFriend(fName);
                    setSearchTerm('');
                    setFilterType('all');
                  }}
                  className={`flex-shrink-0 px-3.5 py-2 rounded-xl text-xs font-semibold border transition-all duration-150 cursor-pointer snap-center ${
                    isSelected
                      ? 'bg-gradient-to-r from-world-purple to-violet-950 text-world-volt border-world-volt font-bold scale-102 shadow-md shadow-world-purple/10'
                      : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700/80 hover:text-slate-200'
                  }`}
                  style={{ contentVisibility: 'auto' }}
                >
                  {fName}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* PERSONAL PROFILE BOARD */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Maverick Achievement Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 h-16 w-16 bg-gradient-to-bl from-world-volt/10 to-transparent rounded-bl-full pointer-events-none" />
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-950/50 border border-amber-800 text-amber-400 mb-4 shadow">
            <Sparkles className="h-6 w-6" />
          </div>
          <span className="text-xs text-slate-400 uppercase tracking-wider font-bold">The Maverick Index</span>
          <div className="text-3xl font-display font-black text-white mt-1.5">
            {friendData.stats.uniqueCount} <span className="text-xs font-normal text-slate-500 font-sans">unique picks</span>
          </div>
          <p className="text-xs text-slate-400 mt-2.5 leading-relaxed">
            Unique scorelines predicted alone in the group of 30. High indices indicate courage or highly risk-tolerant football perspectives!
          </p>
        </div>

        {/* Prediction Goal/Ratio Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl relative overflow-hidden">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-orange-950/50 border border-orange-900 text-orange-400 mb-4 shadow">
            <Flame className="h-6 w-6 animate-pulse" />
          </div>
          <span className="text-xs text-slate-400 uppercase tracking-wider font-bold">Goal Tendencies</span>
          <div className="text-3xl font-display font-black text-white mt-1.5 flex items-baseline gap-1.5">
            <span>{friendData.stats.avgGoals}</span>
            <span className="text-xs font-normal text-slate-500 font-sans">goals / match</span>
          </div>
          <div className="mt-3 flex items-center justify-between text-xs font-mono text-slate-400">
            <span>Total Expected Goals:</span>
            <span className="text-white font-bold">{friendData.stats.totalGoals}</span>
          </div>
          <div className="mt-1 flex items-center justify-between text-xs font-mono text-slate-400">
            <span>Most Favorite Scoreline:</span>
            <span className="text-world-volt font-bold bg-slate-950 px-2 py-0.5 rounded border border-slate-850">
              {friendData.stats.favoriteScore}
            </span>
          </div>
        </div>

        {/* Soccer Biases Box (Wins vs Draws) */}
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-cyan-950/55 border border-cyan-900 text-cyan-400 mb-4 shadow">
            <Award className="h-6 w-6" />
          </div>
          <span className="text-xs text-slate-400 uppercase tracking-wider font-bold">Result Selection Trait</span>
          <div className="text-sm font-semibold text-slate-200 mt-3 space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400 flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-emerald-500" /> Home Wins predicted:
              </span>
              <span className="font-mono text-white font-extrabold">{friendData.stats.homeWins}</span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400 flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-amber-500" /> Draws predicted:
              </span>
              <span className="font-mono text-white font-extrabold">{friendData.stats.draws}</span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400 flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-blue-500" /> Away Wins predicted:
              </span>
              <span className="font-mono text-white font-extrabold">{friendData.stats.awayWins}</span>
            </div>
          </div>
        </div>

      </div>

      {/* FILTER & 72 SELECTIONS EXPLORER TABLE */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl space-y-4">
        
        {/* Table Controls */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="h-4 w-4 text-world-volt" />
            <h3 className="font-display font-extrabold text-white text-base md:text-lg">
              Fixtures Predictions Directory ({filteredPredictions.length} matchcards)
            </h3>
          </div>

          <div className="flex flex-col sm:flex-row gap-3 w-full md:w-auto">
            {/* Search Bar */}
            <div className="relative flex-grow">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
              <input
                type="text"
                placeholder="Search country or fixture..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 text-slate-200 text-xs rounded-xl pl-9 pr-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-world-volt/40 font-medium"
              />
            </div>

            {/* Quick Filter Select */}
            <div className="flex gap-1.5 bg-slate-950 p-1 rounded-xl border border-slate-800 text-[10px] font-bold uppercase tracking-wider overflow-x-auto">
              <button
                onClick={() => setFilterType('all')}
                className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
                  filterType === 'all' ? 'bg-slate-900 text-world-volt font-extrabold' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                All
              </button>
              <button
                onClick={() => setFilterType('unique')}
                className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
                  filterType === 'unique' ? 'bg-amber-950 text-amber-400 font-extrabold' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Unique
              </button>
              <button
                onClick={() => setFilterType('draws')}
                className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
                  filterType === 'draws' ? 'bg-cyan-950 text-cyan-400 font-extrabold' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Draws
              </button>
              <button
                onClick={() => setFilterType('high_scoring')}
                className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
                  filterType === 'high_scoring' ? 'bg-rose-950/80 text-rose-400 font-extrabold' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                High Goal
              </button>
            </div>
          </div>
        </div>

        {/* Predictions Spreadsheet grid: Responsive dual-view */}
        
        {/* VIEW 1: Mobile-First Card List (sm / screens under 768px) */}
        <div className="md:hidden space-y-4">
          {filteredPredictions.length === 0 ? (
            <div className="text-center py-10 bg-slate-950/30 border border-slate-850 rounded-2xl text-slate-500 font-medium font-sans text-xs">
              No predictions found matching active rules or tags.
            </div>
          ) : (
            filteredPredictions.map((item) => {
              const isUnique = item.prediction.isUnique;
              return (
                <div 
                  key={item.game.matchNo} 
                  className={`relative p-4 rounded-2xl border transition-all ${
                    isUnique 
                      ? 'bg-gradient-to-br from-amber-950/15 via-slate-900 to-amber-950/5 border-amber-500/50 shadow-md shadow-amber-950/10' 
                      : 'bg-slate-950/60 border-slate-850 hover:border-slate-800 hover:bg-slate-950/90'
                  }`}
                >
                  {/* Card Header row */}
                  <div className="flex items-center justify-between border-b border-slate-800/40 pb-2.5 mb-3">
                    <div className="flex items-center gap-2">
                      <span className="flex h-6 w-6 items-center justify-center rounded bg-slate-900 border border-slate-800 text-slate-400 font-mono text-[10px] font-bold">
                        #{item.game.matchNo}
                      </span>
                      <span className="text-[10px] font-mono text-slate-400 font-medium flex items-center gap-1">
                        <Calendar className="h-3 w-3 text-slate-500 flex-shrink-0" />
                        {item.game.date}
                      </span>
                    </div>

                    {isUnique ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[9px] font-extrabold bg-amber-950/80 text-amber-400 border border-amber-900/40 uppercase tracking-widest animate-pulse">
                        <Sparkles className="h-2 w-2" /> Maverick
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-bold bg-slate-900 text-slate-500 border border-slate-850 uppercase tracking-wider">
                        Consensus
                      </span>
                    )}
                  </div>

                  {/* Scoreboard-like matchup row */}
                  <div className="flex items-center justify-between gap-2 py-1">
                    {/* Home Team & away Team */}
                    <div className="flex-grow space-y-1.5">
                      <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-200">
                        <ClickableTeam name={item.game.homeTeam} onClick={onTeamClick} className="p-0 text-slate-100 hover:text-world-volt" />
                      </div>
                      <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-200">
                        <ClickableTeam name={item.game.awayTeam} onClick={onTeamClick} className="p-0 text-slate-100 hover:text-world-volt" />
                      </div>
                    </div>

                    {/* Big Interactive Score Sticker */}
                    <div className="text-right flex-shrink-0 min-w-[70px]">
                      <span className="text-[9px] text-slate-500 font-mono block uppercase tracking-wider mb-0.5">Prediction</span>
                      <span className={`px-3 py-1.5 rounded-xl text-sm font-extrabold font-display border block text-center shadow-inner ${
                        isUnique 
                          ? 'bg-amber-400 text-slate-950 border-amber-500 font-black text-neon-glow' 
                          : 'bg-slate-900 text-world-volt border-slate-800'
                      }`}>
                        {item.prediction.score}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* VIEW 2: Desktop Spreadsheet table (md / screens 768px and wider) */}
        <div className="hidden md:block overflow-x-auto rounded-2xl border border-slate-800/80">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-950/80 text-slate-400 border-b border-slate-805 font-mono text-[10px] uppercase tracking-wider">
                <th className="p-4 font-bold text-center w-16">No.</th>
                <th className="p-4 font-bold w-28">Date</th>
                <th className="p-4 font-bold text-center sm:text-left">Home Team v Away Team</th>
                <th className="p-4 font-bold text-center w-28">Picks</th>
                <th className="p-4 font-bold text-center w-32">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {filteredPredictions.length === 0 ? (
                <tr>
                  <td colSpan={5} className="text-center py-12 text-slate-500 font-medium bg-slate-950/20">
                    No predictions found matching terms or active filters. Try resetting search criteria!
                  </td>
                </tr>
              ) : (
                filteredPredictions.map((item) => {
                  const isUnique = item.prediction.isUnique;
                  return (
                    <tr 
                      key={item.game.matchNo} 
                      className={`hover:bg-slate-950/50 transition-all ${
                        isUnique ? 'bg-amber-950/5' : ''
                      }`}
                    >
                      {/* Match Number */}
                      <td className="p-4 text-center font-mono font-bold text-slate-400">
                        {item.game.matchNo}
                      </td>

                      {/* Date */}
                      <td className="p-4 font-mono text-slate-400 text-[11px] flex items-center gap-1.5">
                        <Calendar className="h-3 w-3 text-slate-500 flex-shrink-0" />
                        <span>{item.game.date}</span>
                      </td>

                      {/* Fixtures interactive wrapper */}
                      <td className="p-4">
                        <div className="flex flex-col sm:flex-row sm:items-center gap-1.5">
                          <ClickableTeam name={item.game.homeTeam} onClick={onTeamClick} className="px-1 text-xs sm:text-sm" />
                          <span className="text-slate-500 px-1 font-semibold text-[10px] sm:text-xs">v</span>
                          <ClickableTeam name={item.game.awayTeam} onClick={onTeamClick} className="px-1 text-xs sm:text-sm" />
                        </div>
                      </td>

                      {/* Score values */}
                      <td className="p-4 text-center">
                        <span className={`px-3 py-1 rounded-lg text-xs font-extrabold font-display border block w-20 mx-auto ${
                          isUnique 
                            ? 'bg-amber-400 text-slate-950 border-amber-500 font-black text-neon-glow' 
                            : 'bg-slate-950 text-world-volt border-slate-800'
                        }`}>
                          {item.prediction.score}
                        </span>
                      </td>

                      {/* Status */}
                      <td className="p-4 text-center">
                        <div className="flex justify-center">
                          {isUnique ? (
                            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[9px] font-extrabold bg-amber-950/80 text-amber-400 border border-amber-900/40 uppercase tracking-widest animate-pulse">
                              <Sparkles className="h-2.5 w-2.5" /> Unique
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-bold bg-slate-900 text-slate-400 border border-slate-850 uppercase tracking-wider">
                              Consensus
                            </span>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Footer descriptor */}
        <div className="text-[11px] text-slate-500 flex items-center gap-1 pt-2">
          <Info className="h-3.5 w-3.5" />
          <span>Clicking any country flag or name inside the spreadsheet launches the prediction analysis drawer instantly.</span>
        </div>
      </div>

    </div>
  );
}
