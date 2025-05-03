import requests
import csv
import os
from bs4 import BeautifulSoup
import time
import argparse


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Parse news from gov.kz and save to CSV')
    parser.add_argument('--output', type=str, default='gov_kz_news.csv',
                        help='Output CSV file path (default: gov_kz_news.csv)')
    return parser.parse_args()


def fetch_news(lang, project_id, project_name, url, max_retries=3, retry_delay=5):
    """Fetch news for a given language and project with pagination"""
    all_news = []
    page = 1
    headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}

    # GraphQL query template
    query_template = """
    query {
      news(projects: "$project", _lang: "$lang", _page: $page, _size: 50, _sort: "created_date:desc") {
        id
        title
        body
        created_date
        heropic
        slug
        hint
        comments_on
        projects
        directions {
          id
          title
        }
      }
    }
    """

    while True:
        query = query_template.replace("$lang", lang).replace("$page", str(page)).replace("$project", project_id)
        payload = {"query": query}

        for attempt in range(max_retries):
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=30)
                print(f"[{project_name}][{lang}] Response status for page {page}: {response.status_code}")

                if response.status_code != 200:
                    print(f"[{project_name}][{lang}] HTTP Error: {response.status_code}")
                    print(f"[{project_name}][{lang}] Response text: {response.text[:500]}...")
                    if response.status_code == 504:
                        print(f"[{project_name}][{lang}] Retrying {attempt + 1}/{max_retries} after delay...")
                        time.sleep(retry_delay)
                        continue
                    break

                data = response.json()

                if "errors" in data:
                    print(f"[{project_name}][{lang}] GraphQL errors on page {page}:", data["errors"])
                    return all_news

                news_list = data["data"]["news"]
                if not news_list:
                    print(f"[{project_name}][{lang}] Page {page}: no more news")
                    return all_news

                all_news.extend(news_list)
                print(f"[{project_name}][{lang}] Page {page}: got {len(news_list)} news")

                if len(news_list) < 50:
                    return all_news
                page += 1
                break

            except requests.RequestException as e:
                print(f"[{project_name}][{lang}] Request error on page {page}: {e}")
                if attempt < max_retries - 1:
                    print(f"[{project_name}][{lang}] Retrying {attempt + 1}/{max_retries} after delay...")
                    time.sleep(retry_delay)
                else:
                    print(f"[{project_name}][{lang}] Max retries exceeded")
                    return all_news
            except ValueError as e:
                print(f"[{project_name}][{lang}] JSON decoding error: {e}")
                print(f"[{project_name}][{lang}] Response text: {response.text[:500]}...")
                return all_news


def clean_html(text):
    """Convert HTML to plain text"""
    if text:
        return BeautifulSoup(text, 'html.parser').get_text().strip()
    return ""


def parse_directions(directions):
    """Convert directions list to string"""
    if directions:
        return "; ".join(f"{d['title']} (ID: {d['id']})" for d in directions)
    return ""


def main():
    """Main function to parse news from gov.kz"""
    args = parse_arguments()

    # Settings
    URL = "https://www.gov.kz/graphql"
    LANGUAGES = ["ru", "kk", "en"]  # Languages to parse
    PROJECTS = {
        "mvd": "eq:qriim",  # МВД
        "water": "eq:water",  # Министерство водных ресурсов
        "cultureandInformation": "eq:mam",  # Министерство культуры и информации
        "foreignAffairs": "eq:mfa",  # Министерство иностранных дел
        "health_care": "eq:dsm",  # Министерство здравоохранения
        "IndustryandConstruction": "eq:mps",  # Министерство промышленности и строительства
        "sport": "eq:sport",  # Министерство туризма и спорта
        "sci": "eq:sci",  # Министерство науки и высшего образования
        "economy": "eq:economy",  # Министерство национальной экономики
        "mod": "eq:mod",  # Министерство обороны
        "edu": "eq:edu",  # Министерство просвещения
        "moa": "eq:moa",  # Министерство сельского хозяйства
        "mti": "eq:mti",  # Министерство торговли и интеграции Республики Казахстан
        "transport": "eq:transport",  # Министерство транспорта
        "minfin": "eq:minfin",  # Министерство финансов
        "enbek": "eq:enbek",  # Министерство труда и социальной защиты населения
        "mdai": "eq:mdai",  # Министерство цифрового развития, инноваций и аэрокосмической промышленности
        "ecogeo": "eq:ecogeo",  # Министерство экологии и природных ресурсов
        "energo": "eq:energo",  # Министерство энергетики
        "adilet": "eq:adilet",  # Министерство юстиции
        "emer": "eq:emer",  # Министерство по чрезвычайным ситуациям
    }

    # Create a single CSV file for all news
    output_file = args.output
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)

    try:
        with open(output_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                "ID", "Title", "Body", "Created Date", "Hero Pic",
                "Slug", "Hint", "Comments On", "Projects", "Directions",
                "Ministry", "Language"  # Added two new columns to track source
            ])

            # Process all ministries and languages
            for project_name, project_id in PROJECTS.items():
                print(f"\n=== Starting news parsing for project: {project_name} ===")
                try:
                    for lang in LANGUAGES:
                        print(f"\n=== Parsing news in language: {lang} ===")
                        news_list = fetch_news(lang, project_id, project_name, URL)

                        if news_list:
                            # Write news to CSV
                            for news in news_list:
                                writer.writerow([
                                    news["id"],
                                    clean_html(news["title"]),
                                    clean_html(news["body"]),
                                    news["created_date"],
                                    news.get("heropic", ""),
                                    news["slug"],
                                    clean_html(news.get("hint", "")),
                                    str(news["comments_on"]),
                                    news["projects"],
                                    parse_directions(news["directions"]),
                                    project_name,  # Add ministry name
                                    lang  # Add language
                                ])
                            print(f"[{project_name}][{lang}] Saved {len(news_list)} news to CSV")
                        else:
                            print(f"[{project_name}][{lang}] No data to save")
                except Exception as e:
                    print(f"[{project_name}] Critical error during parsing: {e}")
                print(f"\n=== Finished parsing for project: {project_name} ===")

        print(f"\nAll news has been saved to {output_file}")
    except Exception as e:
        print(f"Error when writing to CSV: {e}")


if __name__ == "__main__":
    main()