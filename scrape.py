#!/usr/bin/env python
import os
import argparse
import requests
from bs4 import BeautifulSoup
import urllib.parse


def query(footprint: str, keyword: str):
    """
    return the results based on footprint and keywords
    :param footprint:
    :param keyword:
    :return:
    """
    # desktop user-agent
    USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:65.0) Gecko/20100101 Firefox/65.0"
    # mobile user-agent
    MOBILE_USER_AGENT = "Mozilla/5.0 (Linux; Android 7.0; SM-G930V Build/NRD90M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.125 Mobile Safari/537.36"
    HEADERS = {"user-agent": USER_AGENT}

    step = 0
    results = []

    # find the top 300 results for this particular footprint and keyword
    # Google limits the results to 300
    for start in range(0, 300, 100):
        query = {
            "q": "{} {}".format(footprint, keyword),
            "num": 100,
            "start": start,
        }

        query = urllib.parse.urlencode(query)
        url = f"https://google.com/search?{query}"

        resp = requests.get(url, headers=HEADERS)

        # check if we got captcha
        if resp.status_code == 200:
            # use beautifulsoup to parse the html code
            soup = BeautifulSoup(resp.content, "html.parser")
            gs = soup.find_all("div", class_="rc")
            # grab all results title, link, and description
            for g in gs:
                anchors = g.find_all("a")
                if anchors:
                    link = anchors[0]["href"]
                    title = g.find("h3").text
                    item = {"title": title, "link": link}
                    results.append(item)
            if len(gs) < 10:
                return results
        elif (resp.status_code == 429) or (
            "Our systems have detected unusual traffic from your computer network."
            in resp.content
        ):
            results.append(ValueError("Ran into captcha. Please use a proxy."))
            return results

    return results


def main():
    """
    scape list of urls based on command arguments
    :return:
    """
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument(
        "--footprint", type=str, help="Specify the type of footprint to search"
    )
    parser.add_argument("--keyword", type=str, help="The keyword to search for")

    args = parser.parse_args()

    # check arguments
    footprint_file = args.footprint
    if not footprint_file:
        print("No footprint was specified, defaulting to guestbook")
        footprint_file = "guestbook.txt"
    keyword = args.keyword
    if not keyword:
        raise ValueError("Keyword must be specified (Use --keyword)")

    # check if footprint exists
    supported_footprints = os.listdir("footprints")
    if ".txt" not in footprint_file:
        footprint_file = "{}.txt".format(footprint_file)

    if (footprint_file in supported_footprints) and (keyword):
        with open(
            os.path.join(os.getcwd(), "footprints", footprint_file), "rt"
        ) as fp:
            print()
            footprints = [f.strip() for f in fp.readlines()]

        links = set()
        # go through all the footprint in the files and save of the links
        for footprint in footprints:
            print(
                'Scraping footprint: {} , keyword: "{}"'.format(
                    footprint, keyword
                )
            )
            try:
                results = query(footprint=footprint, keyword=keyword)
                print("Found {} results.".format(len(results)))
                for r in results:
                    if type(r) == ValueError:
                        # ran into captcha
                        raise r
                    else:
                        links.add(r["link"])
            except Exception as e:
                # ran into captcha
                if type(e) == ValueError:
                    raise e
            finally:
                with open("results.txt", "wt") as fp:
                    fp.write("\n".join(list(links)))


if __name__ == "__main__":
    main()
