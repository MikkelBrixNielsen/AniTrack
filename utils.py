import req

def create_indexed_nodes(url, headers, showStatus):
    response = req.requests.get(url, headers=headers)
    response.raise_for_status()
    reply = response.json()
    #search_results = sorted(
    #    reply["data"], key=lambda x: x["node"]["popularity"]
    #)
    reply = reply.get("data", [])
    indexed_nodes = []
    for i, item in enumerate(reply[:15], start=1):
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
            "status": item["node"]["my_list_status"]["status"]
            if showStatus
            else None,
        }
        indexed_nodes.append(node_dict)
    return indexed_nodes

def get_mylist(contentType, token):
    contentType = req.quote(contentType)
    url = f"https://api.myanimelist.net/v2/users/@me/{contentType}list?limit=500&fields=id,title,mean,main_picture,alternative_titles,popularity,synopsis,my_list_status&nsfw=true"
    headers = {"Authorization": f'Bearer {token["access_token"]}'}
    try:
        return create_indexed_nodes(url, headers, True)
    except req.requests.exceptions.RequestException as e:
        print("HTTP search error: ", e)
        return []

def refresh_token(clientId, token):
    data = {
        "client_id": clientId,
        "grant_type": "refresh_token",
        "refresh_token": token["refresh_token"],
    }
    try:
        response = req.requests.post("https://myanimelist.net/v1/oauth2/token", data=data)
        response.raise_for_status()
        token_data = req.json.loads(response.text)
        save_token(token_data)
        print("Token refreshed")
        return token_data
    except req.requests.exceptions.RequestException as e:
        print("Token refresh error:", e)
        print("Trying new authentication")
        authenticator()

def getClientId():
    try:
        response = req.requests.get(
            "https://suiz.org/api/mal?client=MALadder", headers={"Client": "MALadder"}
        )
        response.raise_for_status()
        reply = req.json.loads(response.text)
        return reply["clientId"]
    except req.requests.exceptions.RequestException as e:
        print("HTTP request error: ", e)

def get_code_verifier() -> str:
    token = req.secrets.token_urlsafe(100)
    return token[:128]

def getToken(code, code_verifier, clientId, mal_folder):
    data = {
        "client_id": clientId,
        "code": code,
        "code_verifier": code_verifier,
        "grant_type": "authorization_code",
    }
    try:
        response = req.requests.post(
            "https://myanimelist.net/v1/oauth2/token", data=data
            )
        response.raise_for_status()
        token_data = req.json.loads(response.text)
        save_token(token_data, mal_folder)
        return token_data
    except req.requests.exceptions.RequestException as e:
        print("Token http request error:", e)

def save_token(token_data, mal_folder):
    token_data["expiration_time"] = int(req.time.time()) + token_data["expires_in"]
    with open(req.os.path.join(mal_folder, "token.json"), "w") as file:
        req.json.dump(token_data, file)

def authenticator(clientId):
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
        match = req.re.search(r"code=(.*?)&state=RequestID", code)
        if match:
            return getToken(match.group(1), code_verifier)
        else:
            print("Not valid, please try again.")

def horizontal_line():
    line = req.QFrame()
    line.setFrameShape(req.QFrame.HLine)
    line.setFrameShadow(req.QFrame.Sunken)
    line.setFixedHeight(1)
    line.setStyleSheet("background-color: #003e80;")
    return line