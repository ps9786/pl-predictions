import { RAW_PREDICTIONS_CSV } from './rawCsv';

export interface Prediction {
  friend: string;
  score: string; // e.g., "2-1"
  isUnique: boolean; // Only one person predicted this specific score for this game
  homeGoals: number;
  awayGoals: number;
}

export interface Game {
  matchNo: number;
  date: string; // e.g., "11th June"
  fixture: string; // e.g., "Mexico v South Africa"
  homeTeam: string;
  awayTeam: string;
  predictions: Prediction[];
}

export interface ScoreGroup {
  score: string;
  homeGoals: number;
  awayGoals: number;
  friends: { name: string; isUnique: boolean }[];
  count: number;
  isUnique: boolean;
}

// Score parsing helper
export function parseScore(scoreStr: string) {
  const parts = (scoreStr || '').trim().split('-');
  const home = parseInt(parts[0], 10);
  const away = parseInt(parts[1], 10);
  return {
    home: isNaN(home) ? 0 : home,
    away: isNaN(away) ? 0 : away,
  };
}

// Score sorting comparator (0-0, 1-0, 1-1, 2-0 etc.)
export function compareScores(scoreA: string, scoreB: string): number {
  const a = parseScore(scoreA);
  const b = parseScore(scoreB);
  if (a.home !== b.home) {
    return a.home - b.home;
  }
  return a.away - b.away;
}

export function parsePredictionsData(): { games: Game[]; friendsList: string[]; dates: string[]; teams: string[] } {
  const lines = RAW_PREDICTIONS_CSV.split('\n').map((l) => l.trim()).filter((l) => l.length > 0);
  
  // Find the header with friend names (the one starting with "Match Date,Match No.")
  const headerIndex = lines.findIndex((line) => line.startsWith('Match Date,Match No.,FIXTURE'));
  if (headerIndex === -1) {
    throw new Error('Could not find header in CSV data');
  }

  const headerCols = lines[headerIndex].split(',');
  const friendsList = headerCols.slice(3).map((name) => name.trim().replace(/\s+/g, ' '));

  const games: Game[] = [];
  const uniqueDatesSet = new Set<string>();
  const uniqueTeamsSet = new Set<string>();

  // Process game rows (after the header)
  const gameLines = lines.slice(headerIndex + 1);
  for (const line of gameLines) {
    const cols: string[] = [];
    let currentVal = '';
    let inQuotes = false;
    
    // Simple CSV splitter that respects potential quotes, though standard lines are comma-separated
    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      if (char === '"') {
        inQuotes = !inQuotes;
      } else if (char === ',' && !inQuotes) {
        cols.push(currentVal);
        currentVal = '';
      } else {
        currentVal += char;
      }
    }
    cols.push(currentVal);

    if (cols.length < 4) continue; // Invalid row

    const rawDate = cols[0].trim();
    // Normalize June / june / July etc
    const date = rawDate
      .replace(/june/gi, 'June')
      .replace(/july/gi, 'July')
      .replace(/\s+/g, ' ');
    
    const matchNo = parseInt(cols[1].trim(), 10);
    const fixture = cols[2].trim().replace(/\s+/g, ' ');
    
    // Split by " v " or "  v  " with robust regex
    const teamParts = fixture.split(/\s+v\s+/i);
    const homeTeam = (teamParts[0] || 'Unknown').trim();
    const awayTeam = (teamParts[1] || 'Unknown').trim();

    uniqueDatesSet.add(date);
    uniqueTeamsSet.add(homeTeam);
    uniqueTeamsSet.add(awayTeam);

    // Friend predictions are from index 3 onwards
    const rawScores = cols.slice(3).map((s) => s.trim());

    // Group scores to find uniqueness
    const scoreCounts: Record<string, number> = {};
    rawScores.forEach((score) => {
      scoreCounts[score] = (scoreCounts[score] || 0) + 1;
    });

    const predictions: Prediction[] = friendsList.map((friendName, idx) => {
      const score = rawScores[idx] || '0-0';
      const parsed = parseScore(score);
      return {
        friend: friendName,
        score,
        isUnique: scoreCounts[score] === 1,
        homeGoals: parsed.home,
        awayGoals: parsed.away,
      };
    });

    games.push({
      matchNo,
      date,
      fixture,
      homeTeam,
      awayTeam,
      predictions,
    });
  }

  return {
    games,
    friendsList: friendsList.sort((a, b) => a.localeCompare(b)),
    dates: Array.from(uniqueDatesSet),
    teams: Array.from(uniqueTeamsSet).sort((a, b) => a.localeCompare(b)),
  };
}

// Load parsed data once
export const { games: ALL_GAMES, friendsList: FRIENDS_LIST, dates: TOURNAMENT_DATES, teams: ALL_TEAMS } = parsePredictionsData();

// Get the score groups/counts for a specific game, sorted by score order (0-0, 1-0, 1-1, 2-0 etc.)
export function getGameScoreGroups(game: Game): ScoreGroup[] {
  const groups: Record<string, { name: string; isUnique: boolean }[]> = {};
  
  game.predictions.forEach((pred) => {
    if (!groups[pred.score]) {
      groups[pred.score] = [];
    }
    groups[pred.score].push({ name: pred.friend, isUnique: pred.isUnique });
  });

  return Object.keys(groups)
    .sort(compareScores)
    .map((score) => {
      const parsed = parseScore(score);
      const friends = groups[score];
      return {
        score,
        homeGoals: parsed.home,
        awayGoals: parsed.away,
        friends,
        count: friends.length,
        isUnique: friends.length === 1,
      };
    });
}

// Get team specific statistics
export interface TeamStats {
  teamName: string;
  totalGames: number;
  gamesList: { matchNo: number; date: string; fixture: string; opponent: string; isHome: boolean }[];
  scorePredictions: { scoreRoot: string; count: number; percentage: number }[]; // Normalised scores for this team (e.g., "Win 2-0", "Draw 1-1", "Lose 1-2")
  scoreOccurrences: { score: string; count: number }[]; // Raw predicted score counts across all games involving this team
}

export function getTeamPredictionsStats(teamName: string): TeamStats {
  // Find all games involving this team
  const teamGames = ALL_GAMES.filter((g) => g.homeTeam === teamName || g.awayTeam === teamName);
  
  const gamesList = teamGames.map((g) => {
    const isHome = g.homeTeam === teamName;
    return {
      matchNo: g.matchNo,
      date: g.date,
      fixture: g.fixture,
      opponent: isHome ? g.awayTeam : g.homeTeam,
      isHome,
    };
  });

  const rawScoreCounts: Record<string, number> = {};
  
  teamGames.forEach((g) => {
    g.predictions.forEach((pred) => {
      // Score in raw format of the prediction (e.g. "3-0")
      // But the user clicks the team and wants to see all different scores with a count of occurrences
      // Do they want occurrences of raw scores (like "3-0" as listed) OR relative to the clicked team?
      // "Allow the clicking of a team ... to show all the different scores with a count of occurrences"
      // Raw score or oriented score? Raw score is standard, but keeping oriented score (Win/Draw/Loss) is also extremely analytical.
      // Let's offer BOTH! Showing the raw score predictions (e.g. 2-1, 1-1 etc as written in the cells) is exactly what is requested, so we'll aggregate raw scores.
      const rawScore = pred.score;
      rawScoreCounts[rawScore] = (rawScoreCounts[rawScore] || 0) + 1;
    });
  });

  const scoreOccurrences = Object.keys(rawScoreCounts)
    .map((score) => ({ score, count: rawScoreCounts[score] }))
    .sort((a, b) => b.count - a.count); // Most popular predicted scores first

  // Also relative outcomes for deep dashboard details
  const relativeCounts: Record<string, number> = {};
  let totalPredictions = 0;
  
  teamGames.forEach((g) => {
    const isHome = g.homeTeam === teamName;
    g.predictions.forEach((pred) => {
      const { home, away } = parseScore(pred.score);
      let outcome = '';
      if (home === away) {
        outcome = `Draw ${home}-${away}`;
      } else if ((home > away && isHome) || (away > home && !isHome)) {
        outcome = `Win ${isHome ? home : away}-${isHome ? away : home}`;
      } else {
        outcome = `Loss ${isHome ? home : away}-${isHome ? away : home}`;
      }
      relativeCounts[outcome] = (relativeCounts[outcome] || 0) + 1;
      totalPredictions++;
    });
  });

  const scorePredictions = Object.keys(relativeCounts)
    .map((outcome) => ({
      scoreRoot: outcome,
      count: relativeCounts[outcome],
      percentage: Math.round((relativeCounts[outcome] / (totalPredictions || 1)) * 100),
    }))
    .sort((a, b) => b.count - a.count);

  return {
    teamName,
    totalGames: teamGames.length,
    gamesList,
    scorePredictions,
    scoreOccurrences,
  };
}

// Precompute Quirky Stats
export interface QuirkyStats {
  mostPopularScoreOverall: { score: string; count: number; percent: number };
  maverickRank: { friend: string; uniqueCount: number }[]; // Most unique predictions made
  conformityRank: { friend: string; avgOpponentsWithSameScore: number }[]; // Most common/boring score predictors
  goalHungryRank: { friend: string; avgGoals: number }[]; // Highest average goals predicted
  defensiveMindedRank: { friend: string; avgGoals: number }[]; // Lowest average goals predicted
  wildestPredictions: { matchNo: number; fixture: string; date: string; friend: string; score: string; totalGoals: number }[]; // e.g. 8-0, 0-7
  patriotsAndFanatics: {
    friend: string;
    englandWins: number;
    scotlandWins: number;
    usaWins: number;
    mexicoWins: number;
    canadaWins: number;
  }[];
  mostDivisiveGame: { matchNo: number; fixture: string; uniqueScoresCount: number; consensusScore: string; consensusCount: number };
  mostConsensusGame: { matchNo: number; fixture: string; consensusScore: string; consensusCount: number; percentage: number };
}

export function computeQuirkyStats(): QuirkyStats {
  const totalPredsCount = ALL_GAMES.length * FRIENDS_LIST.length;

  // 1. Most Popular Score Overall
  const scoreCounts: Record<string, number> = {};
  ALL_GAMES.forEach((g) => {
    g.predictions.forEach((p) => {
      scoreCounts[p.score] = (scoreCounts[p.score] || 0) + 1;
    });
  });
  const sortedScores = Object.keys(scoreCounts)
    .map((score) => ({ score, count: scoreCounts[score] }))
    .sort((a, b) => b.count - a.count);
  const topScore = sortedScores[0] || { score: '2-0', count: 0 };
  const mostPopularScoreOverall = {
    score: topScore.score,
    count: topScore.count,
    percent: Math.round((topScore.count / totalPredsCount) * 100),
  };

  // 2. Mavericks & Conformists
  const maverickCounts: Record<string, number> = {};
  const conformityTotal: Record<string, number> = {}; // sum of how many others predicted the same score
  const goalSum: Record<string, number> = {};

  FRIENDS_LIST.forEach((name) => {
    maverickCounts[name] = 0;
    conformityTotal[name] = 0;
    goalSum[name] = 0;
  });

  ALL_GAMES.forEach((g) => {
    // Collect prediction counts for this match
    const matchScoreCounts: Record<string, number> = {};
    g.predictions.forEach((p) => {
      matchScoreCounts[p.score] = (matchScoreCounts[p.score] || 0) + 1;
    });

    g.predictions.forEach((p) => {
      if (p.isUnique) {
        maverickCounts[p.friend]++;
      }
      // Conformity details: how many other people had this exact prediction (out of remaining 29)
      const coPredictors = (matchScoreCounts[p.score] || 1) - 1;
      conformityTotal[p.friend] += coPredictors;

      // Goal sums
      goalSum[p.friend] += p.homeGoals + p.awayGoals;
    });
  });

  // Maverick Rank
  const maverickRank = FRIENDS_LIST.map((friend) => ({
    friend,
    uniqueCount: maverickCounts[friend],
  })).sort((a, b) => b.uniqueCount - a.uniqueCount);

  // Conformity Rank (Average speed dial companions: the average number of other friends who agreed with their exact prediction)
  const conformityRank = FRIENDS_LIST.map((friend) => ({
    friend,
    avgOpponentsWithSameScore: Math.round((conformityTotal[friend] / ALL_GAMES.length) * 10) / 10,
  })).sort((a, b) => b.avgOpponentsWithSameScore - a.avgOpponentsWithSameScore);

  // Goal Hunger Ranks
  const goalStats = FRIENDS_LIST.map((friend) => ({
    friend,
    avgGoals: Math.round((goalSum[friend] / ALL_GAMES.length) * 100) / 100,
  }));
  const goalHungryRank = [...goalStats].sort((a, b) => b.avgGoals - a.avgGoals);
  const defensiveMindedRank = [...goalStats].sort((a, b) => a.avgGoals - b.avgGoals);

  // 3. Wildest Predictions (Scores with 6 or more total goals, or high margin wins, ordered by total goals)
  const wildPreds: QuirkyStats['wildestPredictions'] = [];
  ALL_GAMES.forEach((g) => {
    g.predictions.forEach((p) => {
      const totalGoals = p.homeGoals + p.awayGoals;
      if (totalGoals >= 6 || p.homeGoals >= 6 || p.awayGoals >= 6) {
        wildPreds.push({
          matchNo: g.matchNo,
          fixture: g.fixture,
          date: g.date,
          friend: p.friend,
          score: p.score,
          totalGoals,
        });
      }
    });
  });
  const wildestPredictions = wildPreds.sort((a, b) => b.totalGoals - a.totalGoals).slice(0, 20);

  // 4. Patriots & Fanatics (most wins predicted for England, Scotland, USA, Mexico, Canada)
  const patriotsAndFanatics = FRIENDS_LIST.map((friendName) => {
    let englandWins = 0;
    let scotlandWins = 0;
    let usaWins = 0;
    let mexicoWins = 0;
    let canadaWins = 0;

    ALL_GAMES.forEach((g) => {
      // Find friend's prediction
      const p = g.predictions.find((pred) => pred.friend === friendName);
      if (!p) return;

      const { homeGoals, awayGoals } = p;
      if (homeGoals === awayGoals) return; // Draw is not a win

      const homeWon = homeGoals > awayGoals;

      if (g.homeTeam === 'England' && homeWon) englandWins++;
      if (g.awayTeam === 'England' && !homeWon) englandWins++;

      if (g.homeTeam === 'Scotland' && homeWon) scotlandWins++;
      if (g.awayTeam === 'Scotland' && !homeWon) scotlandWins++;

      if (g.homeTeam === 'USA' && homeWon) usaWins++;
      if (g.awayTeam === 'USA' && !homeWon) usaWins++;

      if (g.homeTeam === 'Mexico' && homeWon) mexicoWins++;
      if (g.awayTeam === 'Mexico' && !homeWon) mexicoWins++;

      if (g.homeTeam === 'Canada' && homeWon) canadaWins++;
      if (g.awayTeam === 'Canada' && !homeWon) canadaWins++;
    });

    return {
      friend: friendName,
      englandWins,
      scotlandWins,
      usaWins,
      mexicoWins,
      canadaWins,
    };
  });

  // 5. Divisive vs Consensus Matches
  let divisiveMatch = { matchNo: 0, fixture: '', uniqueScoresCount: 0, consensusScore: '', consensusCount: 99 };
  let consensusMatch = { matchNo: 0, fixture: '', consensusScore: '', consensusCount: 0, percentage: 0 };

  ALL_GAMES.forEach((g) => {
    const matchScores: Record<string, number> = {};
    g.predictions.forEach((p) => {
      matchScores[p.score] = (matchScores[p.score] || 0) + 1;
    });

    const uniqueScoresCount = Object.keys(matchScores).length;
    
    // Find consensus score
    let bestScore = '';
    let bestCount = 0;
    Object.keys(matchScores).forEach((sc) => {
      if (matchScores[sc] > bestCount) {
        bestCount = matchScores[sc];
        bestScore = sc;
      }
    });

    // Most Divisive (Max unique scores count)
    if (uniqueScoresCount > divisiveMatch.uniqueScoresCount) {
      divisiveMatch = {
        matchNo: g.matchNo,
        fixture: g.fixture,
        uniqueScoresCount,
        consensusScore: bestScore,
        consensusCount: bestCount,
      };
    }

    // Most Consensus (Max agreement count)
    if (bestCount > consensusMatch.consensusCount) {
      consensusMatch = {
        matchNo: g.matchNo,
        fixture: g.fixture,
        consensusScore: bestScore,
        consensusCount: bestCount,
        percentage: Math.round((bestCount / FRIENDS_LIST.length) * 100),
      };
    }
  });

  return {
    mostPopularScoreOverall,
    maverickRank,
    conformityRank,
    goalHungryRank,
    defensiveMindedRank,
    wildestPredictions,
    patriotsAndFanatics,
    mostDivisiveGame: divisiveMatch,
    mostConsensusGame: consensusMatch,
  };
}

export const PRECOMPUTED_QUIRKY_STATS = computeQuirkyStats();
