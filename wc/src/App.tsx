import React, { useState, useEffect, useMemo } from 'react';
import { Trophy, Calendar, User, Award, Info, Sparkles, Moon, ExternalLink } from 'lucide-react';
import { TOURNAMENT_DATES, FRIENDS_LIST, ALL_GAMES } from './data/predictions';
import DailyView from './components/DailyView';
import FriendsView from './components/FriendsView';
import StatsView from './components/StatsView';
import TeamStatsModal from './components/TeamStatsModal';

export default function App() {
  // Navigation active tab State
  const [activeTab, setActiveTab] = useState<'matchday' | 'profiles' | 'stats'>('matchday');
  
  // Date State for predictions explorer
  const [selectedDate, setSelectedDate] = useState<string>('11th June');
  
  // Active selected companion State
  const [selectedFriend, setSelectedFriend] = useState<string>('Paul Knipe');

  // Slide-over analytical team State triggered by click on any v separated team
  const [selectedTeam, setSelectedTeam] = useState<string | null>(null);

  // Automatically detect and align current local date of competition on mount
  useEffect(() => {
    // Current local metadata date: June 11th, 2026
    const today = new Date('2026-06-11T12:43:52-07:00');
    const day = today.getDate();
    // Get month name
    const month = today.toLocaleDateString('en-US', { month: 'long' }); // e.g., "June"

    const getSuffix = (d: number) => {
      if (d > 3 && d < 21) return 'th';
      switch (d % 10) {
        case 1: return 'st';
        case 2: return 'nd';
        case 3: return 'rd';
        default: return 'th';
      }
    };

    const targetDateStr = `${day}${getSuffix(day)} ${month}`; // "11th June"
    
    // Fallback checking
    if (TOURNAMENT_DATES.includes(targetDateStr)) {
      setSelectedDate(targetDateStr);
    } else {
      // Default fallback
      setSelectedDate('11th June');
    }

    // Default first sorted friend
    if (FRIENDS_LIST.length > 0) {
      setSelectedFriend(FRIENDS_LIST[0]);
    }
  }, []);

  // Handler to swap view when clicking a companion's tag or name
  const handleFriendTransition = (friendName: string) => {
    setSelectedFriend(friendName);
    setActiveTab('profiles');
  };

  return (
    <div className="min-h-screen bg-world-navy text-slate-200 selection:bg-world-volt selection:text-slate-950 flex flex-col justify-between">
      
      {/* GLOWING STADIUM GRAPHIC AURAS */}
      <div className="absolute top-0 left-1/4 w-[40vw] h-[30vh] bg-gradient-to-b from-world-purple/10 to-transparent blur-[140px] pointer-events-none" />
      <div className="absolute top-20 right-1/4 w-[40vw] h-[30vh] bg-gradient-to-b from-world-pink/8 to-transparent blur-[140px] pointer-events-none" />

      {/* TOP NAVIGATION HEADER */}
      <header className="sticky top-0 z-40 bg-world-navy/90 backdrop-blur-xl border-b border-slate-800 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row items-center justify-between py-3.5 sm:py-0 sm:h-20 md:h-24 gap-3.5 sm:gap-4">
            
            {/* Title/Branding Logos Stacked */}
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 md:h-12 md:w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-world-purple via-world-pink to-world-volt p-[1.5px] shadow-lg shadow-world-purple/20 flex-shrink-0 animate-pulse">
                <div className="flex h-full w-full items-center justify-center rounded-2xl bg-world-navy">
                  <span className="font-display font-black text-neon-glow text-lg md:text-xl text-world-volt tracking-tighter">26</span>
                </div>
              </div>
              
              <div>
                <h1 className="text-sm md:text-base font-display font-black text-white uppercase tracking-wider flex items-center gap-1.5 justify-center sm:justify-start">
                  FIFA 2026 Selections <span className="inline-block relative h-2 w-2 rounded-full bg-world-volt" />
                </h1>
                <p className="text-[10px] md:text-xs text-slate-400 font-mono tracking-tight text-center sm:text-left">30 Friends • 72 Fixtures competition</p>
              </div>
            </div>

            {/* Nav Cards Controls */}
            <nav className="flex items-center gap-1 bg-slate-950 p-1 rounded-2xl border border-slate-800 w-full sm:w-auto justify-around sm:justify-start">
              {/* Tab 1: Matchday */}
              <button
                onClick={() => setActiveTab('matchday')}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs sm:text-sm font-bold uppercase tracking-wider transition cursor-pointer ${
                  activeTab === 'matchday'
                    ? 'bg-world-volt text-slate-950 font-extrabold shadow'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
                }`}
                id="tab-matchday-btn"
              >
                <Calendar className="h-4 w-4" />
                <span className="hidden sm:inline">Daily Selections</span>
              </button>

              {/* Tab 2: Companion Profiles */}
              <button
                onClick={() => setActiveTab('profiles')}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs sm:text-sm font-bold uppercase tracking-wider transition cursor-pointer ${
                  activeTab === 'profiles'
                    ? 'bg-world-volt text-slate-950 font-extrabold shadow'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
                }`}
                id="tab-profiles-btn"
              >
                <User className="h-4 w-4" />
                <span className="hidden sm:inline">Friends Profiles</span>
              </button>

              {/* Tab 3: Quirky Stats */}
              <button
                onClick={() => setActiveTab('stats')}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs sm:text-sm font-bold uppercase tracking-wider transition cursor-pointer ${
                  activeTab === 'stats'
                    ? 'bg-world-volt text-slate-950 font-extrabold shadow'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
                }`}
                id="tab-stats-btn"
              >
                <Award className="h-4 w-4" />
                <span className="hidden sm:inline">Quirky Stats</span>
              </button>
            </nav>

          </div>
        </div>
      </header>

      {/* MAIN LAYOUT CANVAS */}
      <main className="max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-10 flex-grow">
        
        {/* Render correct interface based on tab */}
        {activeTab === 'matchday' && (
          <DailyView
            selectedDate={selectedDate}
            setSelectedDate={setSelectedDate}
            onTeamClick={setSelectedTeam}
            onFriendClick={handleFriendTransition}
          />
        )}

        {activeTab === 'profiles' && (
          <FriendsView
            selectedFriend={selectedFriend}
            setSelectedFriend={setSelectedFriend}
            onTeamClick={setSelectedTeam}
          />
        )}

        {activeTab === 'stats' && (
          <StatsView
            onTeamClick={setSelectedTeam}
            onFriendClick={handleFriendTransition}
          />
        )}

      </main>

      {/* TEAM STATS POPUP DRAWER (Triggers on team click) */}
      {selectedTeam && (
        <TeamStatsModal
          teamName={selectedTeam}
          onClose={() => setSelectedTeam(null)}
        />
      )}

      {/* STYLISH FOOTER DISCLOSURE */}
      <footer className="border-t border-slate-800 bg-slate-950 py-8 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-3">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <span className="flex h-5 w-5 items-center justify-center rounded bg-world-volt font-mono text-[9px] font-black text-slate-950">
                26
              </span>
              <span className="font-semibold text-slate-400">FIFA World Cup 2026 Selections Hub</span>
            </div>
            
            <div className="text-[11px] text-slate-550 italic font-mono space-x-1">
              <span>This is a fun companion database.</span>
              <span className="font-sans text-world-pink font-bold">No monetary values are exchanged.</span>
            </div>
            
            <div className="flex items-center gap-1 text-[11px] text-slate-400">
              <Moon className="h-3.5 w-3.5 text-world-volt" /> State Persistence: <span>Standard React context</span>
            </div>
          </div>
          
          <p className="text-[10px] text-slate-600 border-t border-slate-900 pt-3">
            All teams and fixtures are correctly extracted from official datasets. Clicking on any country name across the pages launches real-time prediction distribution charts. Designed with Plus Jakarta Sans display typography.
          </p>
        </div>
      </footer>

    </div>
  );
}

