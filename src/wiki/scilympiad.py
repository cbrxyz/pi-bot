import asyncio

import aiohttp
import bs4


async def make_results_template(url):
    if not url.find("scilympiad.com") != -1:
        return False
    session = aiohttp.ClientSession()
    page = await session.get(url)
    html = await page.text()
    soup = bs4.BeautifulSoup(html, "html.parser")
    table = soup.select_one(".table-bordered")
    table_header = table.find("thead")
    events = []
    teams = []
    for col_title in table_header.find_all("th")[3:]:
        events.append(col_title.text)
    table_body = table.find("tbody")
    rows = table_body.find_all("tr")
    for row in table_body.find_all("tr")[:-1]:
        name = row.find("td").text
        scores = []
        for place in row.find_all("td")[3:]:
            scores.append(place.text)
        teams.append({"name": name, "scores": scores})
    res = "{{Final results table\n\n"
    for i, e in enumerate(events):
        res += f"|event_{i + 1} = {e}\n"
    res += "\n"
    for i, t in enumerate(teams):
        commaScores = ",".join(t["scores"])
        res += f"|team_{i + 1}_name = {t['name']}\n"
        res += f"|team_{i + 1}_scores = {commaScores}\n"
    res += "}}"
    await session.close()
    return res


async def get_points(url):
    if not url.find("scilympiad.com") != -1:
        return False
    session = aiohttp.ClientSession()
    page = await session.get(url)
    html = await page.text()
    soup = bs4.BeautifulSoup(html, "html.parser")
    table = soup.select_one(".table-bordered")
    table_body = table.find("tbody")
    rows = table_body.find_all("tr")
    points = []
    for row in rows[:-1]:
        points.append(int(row.find_all("td")[2].text))
    await session.close()
    return points
