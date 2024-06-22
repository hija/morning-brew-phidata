import json
import httpx
import dotenv
from phi.assistant import Assistant
from phi.llm.openai import OpenAIChat
import os
import traceback

dotenv.load_dotenv(".env")

REGION_BADEN_WUERTTEMBERG = 1
REGION_NIEDERSACHSEN = 9
REGION_NORDRHEIN_WESTFALEN = 10


def extract_relevant_news(newsElement):
    try:
        return {
            "title": newsElement["title"],
            "content": "\n".join(
                [
                    content_element["value"]
                    for content_element in newsElement["content"]
                    if content_element["type"] == "text"
                ]
            ),
            "breakingNews": newsElement["breakingNews"],
            "link": newsElement["detailsweb"],
        }
    except:
        return {}


def get_latest_news() -> str:
    """Use this function to return the news from Germany.

    Returns:
        str: JSON string of the news
    """
    response = httpx.get("https://www.tagesschau.de/api2u/homepage")
    tagesschau_news = response.json()

    breaking_news = []
    non_breaking_news = []

    for news in tagesschau_news["regional"]:
        if news["regionId"] in [
            REGION_BADEN_WUERTTEMBERG,
            REGION_NIEDERSACHSEN,
            REGION_NORDRHEIN_WESTFALEN,
        ]:
            if news["breakingNews"]:
                breaking_news.append(extract_relevant_news(news))
            else:
                non_breaking_news.append(extract_relevant_news(news))

    for news in tagesschau_news["news"]:
        if news["breakingNews"]:
            breaking_news.append(extract_relevant_news(news))
        else:
            non_breaking_news.append(extract_relevant_news(news))

    all_news = breaking_news + non_breaking_news
    while len(jsonToDump := json.dumps(all_news)) > 30000:
        all_news = all_news[:-1]
    return jsonToDump


template = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Nachrichtenzusammenfassung Deutschland</title>
  <meta name="robots" content="noindex">
</head>
<body>
  <div id="content"></div>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <script>
    document.getElementById('content').innerHTML =
      marked.parse('{content}');
  </script>
  
  <h6><i>Diese Nachrichten wurden AI generiert, indem Nachrichten der <a href="https://www.tagesschau.de/">Tagesschau</a> zusammengefasst worden sind. Diese Website wird nicht redaktionell gerpüft oder die Zusammenfassungen anderweitig verifiziert! Alle Angaben ohne Gewähr. Für die Inhalte kann keine Haftung übernommen werden.</i></h6>
</body>
</html>
"""

try:
    assistant = Assistant(
        llm=OpenAIChat(model="gpt-3.5-turbo-0125"),
        tools=[get_latest_news],
        show_tool_calls=False,
        debug_mode="GITHUB_ACTIONS" not in os.environ,
    )
    content = assistant.run(
        "Was sind die Nachrichten in Deutschland? Geben Sie die relevantesten Nachrichten zuerst (z. B. welche gerade passieren oder Themen, die von mehreren Nachrichtenquellen abgedeckt werden). Fassen Sie das Thema mit 4-10 Sätzen zusammen. Geben Sie für jedes Thema auch einen Link an.",
        stream=False,
    )
except:
    content = "** Error while running the assistant. **"
    if "GITHUB_ACTIONS" not in os.environ:
        traceback.print_exc()

content = content.replace("'", "\\'").replace("\n", "\\n")

parseed_template = template.format(content=content)

with open("public/index.html", "w") as f:
    f.write(parseed_template)
