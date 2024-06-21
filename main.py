import json
import httpx
import dotenv
from phi.assistant import Assistant

dotenv.load_dotenv(".env")


def get_latest_news() -> str:
    """Use this function to return the news from Germany.

    Returns:
        str: JSON string of the news
    """
    response = httpx.get("https://www.tagesschau.de/api2u/homepage")
    tagesschau_news = response.json()

    all_news = []
    for news in tagesschau_news["news"]:
        news_extracted = {
            "tags": [tag["tag"] for tag in news["tags"]],
            "title": news["title"],
            "content": "\n".join(
                [
                    content_element["value"]
                    for content_element in news["content"]
                    if content_element["type"] == "text"
                ]
            ),
            "breakingNews": news["breakingNews"],
            "link": news["detailsweb"],
        }
        all_news.append(news_extracted)
    return json.dumps(all_news)


assistant = Assistant(tools=[get_latest_news], show_tool_calls=False)

template = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Marked in the browser</title>
</head>
<body>
  <div id="content"></div>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <script>
    document.getElementById('content').innerHTML =
      marked.parse('{content}');
  </script>
</body>
</html>
"""

content = assistant.run(
    "What are the news in Germany? Give the most relevant news first (e.g. which are breaking or topics which are covered by multiple news). Summarize the topic with 4-10 sentences. For each topic also give one link.",
    stream=False,
)

content = content.replace("'", "\\'").replace("\n", "\\n")

parseed_template = template.format(content=content)

with open("public/news.html", "w") as f:
    f.write(parseed_template)
