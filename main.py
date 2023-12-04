import os
import requests
import json
import secrets
import re
import time
from urllib.parse import quote

clientId = None
token = None
mal_folder = None


def get_code_verifier() -> str:
    token = secrets.token_urlsafe(100)
    return token[:128]


def getToken(code, code_verifier):
    global mal_folder
    data = {
        "client_id": clientId,
        "code": code,
        "code_verifier": code_verifier,
        "grant_type": "authorization_code",
    }
    try:
        response = requests.post("https://myanimelist.net/v1/oauth2/token", data=data)
        response.raise_for_status()
        token_data = json.loads(response.text)
        save_token(token_data)
        return token_data
    except requests.exceptions.RequestException as e:
        print("Token http request error:", e)


def save_token(token_data):
    token_data["expiration_time"] = int(time.time()) + token_data["expires_in"]
    with open(os.path.join(mal_folder, "token.json"), "w") as file:
        json.dump(token_data, file)


def is_token_expired():
    global token
    return token["expiration_time"] - int(time.time()) < 1209600


def refresh_token():
    data = {
        "client_id": clientId,
        "grant_type": "refresh_token",
        "refresh_token": token["refresh_token"],
    }
    try:
        response = requests.post("https://myanimelist.net/v1/oauth2/token", data=data)
        response.raise_for_status()
        token_data = json.loads(response.text)
        save_token(token_data)
        print("Token refreshed")
        return token_data
    except requests.exceptions.RequestException as e:
        print("Token refresh error:", e)
        print("Trying new authentication")
        authenticator()


def authenticator():
    code_verifier = code_challenge = get_code_verifier()
    print(
        "Go to the following URL to authorize the application: \n https://myanimelist.net/v1/oauth2/authorize?response_type=code&client_id="
        + clientId
        + "&code_challenge="
        + code_challenge
        + "&state=RequestID"
    )
    while True:
        code = input("Paste in the URL you are redirected to here: ")
        match = re.search(r"code=(.*?)&state=RequestID", code)
        if match:
            return getToken(match.group(1), code_verifier)
        else:
            print("Not valid, please try again.")


def getClientId():
    try:
        response = requests.get(
            "https://suiz.org/api/mal?client=MALadder", headers={"Client": "MALadder"}
        )
        response.raise_for_status()
        reply = json.loads(response.text)
        return reply["clientId"]
    except requests.exceptions.RequestException as e:
        print("HTTP request error: ", e)


def init():
    global clientId
    global token
    global mal_folder
    clientId = getClientId()

    home = os.path.expanduser("~")

    if os.name == "nt":  # Windows
        mal_folder = os.path.join(home, "MAL")
    else:  # other platforms
        mal_folder = os.path.join(home, ".config", "MAL")

    try:
        os.makedirs(mal_folder, exist_ok=True)
    except Exception as e:
        print("Error creating directories:", e)

    try:
        with open(os.path.join(mal_folder, "token.json"), "r") as file:
            token = json.load(file)
            print("Token loaded from file.")
            if is_token_expired():
                print("Token is expired, trying refresh")
                token = refresh_token()
    except json.JSONDecodeError:
        print("File is corrupted. Deleting file and getting new token.")
        os.remove(os.path.join(mal_folder, "token.json"))
        token = authenticator()
    except FileNotFoundError:
        print("Token file not found - Starting authentication process...")
        token = authenticator()
    except Exception as e:
        print("Error", e)

    print(" ------------------------------------------------------- ")
    print("|                                                       |")
    print("|                   ANIME SEARCH V2.00                  |")
    print("|                                                       |")
    print(" ------------------------------------------------------- ")


def search_mal(query):
    query = quote(query)
    url = f"https://api.myanimelist.net/v2/anime?q={query}&limit=10&fields=id,title,mean,main_picture,alternative_titles,popularity,synopsis&nsfw=true"
    headers = {
        "X-MAL-CLIENT-ID": clientId,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        reply = response.json()
        print(reply["data"])
        return sorted(reply["data"], key=lambda x: x["node"]["popularity"])
    except requests.exceptions.RequestException as e:
        print("HTTP search error: ", e)
        return []


def add_anime(id_):
    url = f"https://api.myanimelist.net/v2/anime/{id_}/my_list_status"
    data = {"status": "plan_to_watch"}
    headers = {"Authorization": f'Bearer {token["access_token"]}'}
    try:
        response = requests.put(url, data=data, headers=headers)
        response.raise_for_status()
        print(
            f"Anime with ID {id_} successfully added to 'plan to watch' list."
        )  # Confirmation message
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error occurred: {e}")
    except requests.exceptions.ConnectionError as e:
        print(f"Error connecting to the server: {e}")
    except requests.exceptions.Timeout as e:
        print(f"Timeout error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def mainloop():
    while True:
        search_query = input("Type in anime to search for (-1 to quit): ")
        if search_query == "-1":
            print("\nThank you for using MAL Adder.\n")
            break
        search_results = search_mal(search_query)
        if not search_results:
            print("No results found.")
        else:
            indexed_nodes = []
            print("Search results:")
            for i, item in enumerate(search_results, start=1):
                node_dict = {
                    "id": item["node"]["id"] if "id" in item["node"] else None,
                    "title": item["node"]["title"] if "title" in item["node"] else None,
                    "main_picture": item["node"]["main_picture"]
                    if "main_picture" in item["node"]
                    else None,
                    "alternative_titles": item["node"]["alternative_titles"]
                    if "alternative_titles" in item["node"]
                    else None,
                    "popularity": item["node"]["popularity"]
                    if "popularity" in item["node"]
                    else None,
                    "synopsis": item["node"]["synopsis"]
                    if "synopsis" in item["node"]
                    else None,
                    "mean": item["node"]["mean"] if "mean" in item["node"] else None,
                }

                indexed_nodes.append(node_dict)
                english_title = (
                    item["node"]["alternative_titles"]["en"]
                    if "en" in item["node"]["alternative_titles"]
                    and item["node"]["alternative_titles"]["en"]
                    else item["node"]["title"]
                )
                print(
                    f"{i:2}. {english_title:<80} (Popularity: {item['node']['popularity']:>3})"
                )

        while True and search_results:
            selected = input("Select a number to add to MAL (-1 to cancel): ")
            if selected == "-1":
                break

            try:
                selected = int(selected) - 1
                if 0 <= selected < len(search_results):
                    item = indexed_nodes[selected]
                    added_title = (
                        item["alternative_titles"]["en"]
                        if "en" in item["alternative_titles"]
                        and item["alternative_titles"]["en"]
                        else item["title"]
                    )
                    add_anime(item["id"])
                    print(f"\nAdded {added_title} to list\n")
                    break
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a valid number or '-1' to cancel")


def main():
    init()
    mainloop()


if __name__ == "__main__":
    main()
