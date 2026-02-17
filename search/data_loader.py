"""
Data loader for skills JSONL file.

Loads, parses, and normalizes skill data from skills_raw.jsonl.
"""

import json
import re
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path


def parse_install_count(count_str: str) -> float:
    """
    Parse install count strings like '223.0K', '4.2K', '1.5M' to floats.
    
    Args:
        count_str: String representation of count (e.g., "223.0K")
        
    Returns:
        Float representation of the count
    """
    if not count_str or count_str == "0":
        return 0.0
    
    count_str = count_str.strip().upper()
    
    # Handle K (thousands)
    if 'K' in count_str:
        return float(count_str.replace('K', '')) * 1000
    # Handle M (millions)
    elif 'M' in count_str:
        return float(count_str.replace('M', '')) * 1000000
    # Plain number
    else:
        try:
            return float(count_str)
        except ValueError:
            return 0.0


def parse_date(date_str: str) -> datetime:
    """
    Parse date strings like 'Jan 26, 2026' to datetime objects.
    
    Args:
        date_str: Date string (e.g., "Jan 26, 2026")
        
    Returns:
        datetime object
    """
    try:
        return datetime.strptime(date_str, "%b %d, %Y")
    except (ValueError, TypeError):
        # Default to a very old date if parsing fails
        return datetime(2000, 1, 1)


def clean_text(text: str) -> str:
    """
    Clean and normalize text for searching.
    
    Args:
        text: Raw text string
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove HTML entities
    text = re.sub(r'&#x[0-9A-F]+;', ' ', text)
    text = re.sub(r'&[a-z]+;', ' ', text)
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def load_skills(jsonl_path: str) -> List[Dict[str, Any]]:
    """
    Load and parse skills from JSONL file.
    
    Args:
        jsonl_path: Path to skills_raw.jsonl file
        
    Returns:
        List of skill dictionaries with normalized fields
    """
    skills = []
    path = Path(jsonl_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Skills file not found: {jsonl_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                skill = json.loads(line)
                
                # Extract and normalize fields
                name = skill.get('name', '').strip()
                description = clean_text(skill.get('description', ''))
                example_usage = clean_text(skill.get('example_usage', ''))
                skill_url = skill.get('skill_url', '').strip()
                
                # Parse numeric fields
                weekly_installs_raw = skill.get('weekly_installs', '0')
                weekly_installs = parse_install_count(str(weekly_installs_raw))
                
                total_installs_raw = skill.get('total_installs', 0)
                try:
                    total_installs = float(total_installs_raw)
                except (ValueError, TypeError):
                    total_installs = 0.0
                
                # Parse date
                first_seen_str = skill.get('first_seen', '')
                first_seen = parse_date(first_seen_str)
                
                # Create searchable text by combining fields
                searchable_text = f"{name} {description} {example_usage}"
                
                # Build normalized skill dict
                normalized_skill = {
                    'name': name,
                    'description': description,
                    'example_usage': example_usage,
                    'skill_url': skill_url,
                    'weekly_installs': weekly_installs,
                    'total_installs': total_installs,
                    'first_seen': first_seen,
                    'first_seen_str': first_seen_str,
                    'searchable_text': searchable_text
                }
                
                skills.append(normalized_skill)
                
            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse line {line_num}: {e}")
                continue
            except Exception as e:
                print(f"Warning: Error processing line {line_num}: {e}")
                continue
    
    print(f"Loaded {len(skills)} skills from {jsonl_path}")
    return skills


def get_default_data_path() -> str:
    """
    Get the default path to skills_raw.jsonl relative to this module.
    
    Returns:
        Path to skills_raw.jsonl
    """
    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    data_path = project_root / "skills_scraper" / "data" / "skills_raw.jsonl"
    return str(data_path)


if __name__ == "__main__":
    # Test the data loader
    data_path = get_default_data_path()
    skills = load_skills(data_path)
    
    if skills:
        print(f"\nFirst skill:")
        print(f"Name: {skills[0]['name']}")
        print(f"Weekly installs: {skills[0]['weekly_installs']}")
        print(f"Total installs: {skills[0]['total_installs']}")
        print(f"First seen: {skills[0]['first_seen']}")
        print(f"Searchable text length: {len(skills[0]['searchable_text'])} chars")
