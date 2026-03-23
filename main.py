"""
Team League Organizer

Fetches team ELO ratings and organizes them into leagues with country-based
distribution limits.
"""
from flask import Flask
from datetime import datetime
import csv
from dataclasses import dataclass
from typing import Dict, List
from io import StringIO
import requests

app = Flask(__name__)


# Configuration constants
MAX_TEAMS_PER_COUNTRY = 8
TEAMS_PER_LEAGUE = 24
GROUPS_PER_LEAGUE = 4
EXCLUDED_COUNTRIES = {'RUS'}

# League configuration
LEAGUES = ['Star', 'Gold', 'Blue']


@dataclass
class Team:
    """Represents a football team with ELO rating."""
    name: str
    country: str
    elo: float
    rank: int
    level: int

    @classmethod
    def from_csv_row(cls, row: Dict[str, str]) -> 'Team':
        """Create a Team instance from a CSV row dictionary."""
        return cls(
            name=row['Club'],
            country=row['Country'],
            elo=float(row['Elo']),
            rank=int(row['Rank']),
            level=int(row['Level'])
        )


class TeamSelector:
    """Handles team selection with country distribution limits."""

    def __init__(self, max_per_country: int, excluded_countries: set):
        self.max_per_country = max_per_country
        self.excluded_countries = excluded_countries
        self.country_counts: Dict[str, int] = {}

    def can_select_team(self, team: Team) -> bool:
        """Determine if a team can be selected based on constraints."""
        if team.country in self.excluded_countries:
            return False
        if team.level != 1:
            return False
        if self.country_counts.get(team.country, 0) >= self.max_per_country:
            return False
        return True

    def select_team(self, team: Team) -> None:
        """Register a team selection and update country counts."""
        self.country_counts[team.country] = self.country_counts.get(team.country, 0) + 1


def fetch_team_data(date: str) -> str:
    """Fetch team ELO data from the API for a given date."""
    url = f"http://api.clubelo.com/{date}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.text


def parse_teams(csv_content: str) -> List[Team]:
    """Parse CSV content into Team objects."""
    reader = csv.DictReader(StringIO(csv_content))
    teams = []
    for row in reader:
        try:
            teams.append(Team.from_csv_row(row))
        except (ValueError, KeyError) as e:
            # Skip malformed rows
            continue
    return teams


def select_teams_for_leagues(
    teams: List[Team],
    total_teams_needed: int,
    selector: TeamSelector
) -> List[Team]:
    """Select teams for all leagues based on selection criteria."""
    selected_teams = []
    
    for team in teams:
        if len(selected_teams) >= total_teams_needed:
            break
        
        if selector.can_select_team(team):
            selected_teams.append(team)
            selector.select_team(team)
    
    return selected_teams


def organize_into_leagues(teams: List[Team], teams_per_league: int) -> Dict[str, List[Team]]:
    """Organize selected teams into named leagues."""
    leagues = {}
    for i, league_name in enumerate(LEAGUES):
        start_idx = i * teams_per_league
        end_idx = start_idx + teams_per_league
        leagues[league_name] = teams[start_idx:end_idx]
    return leagues


def print_league(league_name: str, teams: List[Team], groups: int) -> None:
    """Print a formatted league with pot divisions."""
    print(f"\n{league_name} league teams:\n")
    teams_per_pot = len(teams) // groups
    
    for i, team in enumerate(teams):
        if i % teams_per_pot == 0:
            pot_number = (i // teams_per_pot) + 1
            print(f"Pot {pot_number}")
        print(f"  {team.name}")


def print_country_distribution(country_counts: Dict[str, int]) -> None:
    """Print the distribution of teams per country."""
    print('\n\nTeams per country:')
    for country, count in sorted(country_counts.items()):
        print(f"{country}: {count}")


def format_league(league_name: str, teams: List[Team], groups: int) -> str:
    lines = [f"\n{league_name} league teams:\n"]
    teams_per_pot = len(teams) // groups
    for i, team in enumerate(teams):
        if i % teams_per_pot == 0:
            pot_number = (i // teams_per_pot) + 1
            lines.append(f"Pot {pot_number}")
        lines.append(f"  {team.name}")
    return "\n".join(lines)


def format_country_distribution(country_counts: Dict[str, int]) -> str:
    lines = ['\n\nTeams per country:']
    for country, count in sorted(country_counts.items()):
        lines.append(f"{country}: {count}")
    return "\n".join(lines)


@app.route("/")
def index():
    today = datetime.today().strftime('%Y-%m-%d')
    csv_content = fetch_team_data(today)
    all_teams = parse_teams(csv_content)

    selector = TeamSelector(MAX_TEAMS_PER_COUNTRY, EXCLUDED_COUNTRIES)
    total_teams_needed = TEAMS_PER_LEAGUE * len(LEAGUES)
    selected_teams = select_teams_for_leagues(all_teams, total_teams_needed, selector)

    leagues = organize_into_leagues(selected_teams, TEAMS_PER_LEAGUE)

    output = []
    for league_name in LEAGUES:
        output.append(format_league(league_name, leagues[league_name], GROUPS_PER_LEAGUE))
    output.append(format_country_distribution(selector.country_counts))

    return "<pre>" + "\n".join(output) + "</pre>"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)