from flask import Flask, redirect, request, session, render_template, url_for
from oauthlib.oauth2 import WebApplicationClient
import mysql.connector
import requests
import waitress
import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

client = WebApplicationClient(config.DISCORD_CLIENT_ID)

# Connect to MySQL database
def get_db_connection():
    conn = mysql.connector.connect(
        host=config.MYSQL_HOST,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DB
    )
    return conn

@app.route('/')
def index():
    if 'discord_user' in session:
        return redirect(url_for('form'))
    return render_template('index.html')

@app.route('/login')
def login():
    authorization_url, state = client.prepare_authorization_request(
        config.DISCORD_OAUTH_URL,
        redirect_uri=config.DISCORD_REDIRECT_URI,
        scope=["identify", "guilds"]
    )
    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route('/callback')
def callback():
    token_url, headers, body = client.prepare_token_request(
        config.DISCORD_TOKEN_URL,
        authorization_response=request.url,
        redirect_uri=config.DISCORD_REDIRECT_URI,
        client_secret=config.DISCORD_CLIENT_SECRET
    )
    token_response = requests.post(token_url, headers=headers, data=body, auth=(config.DISCORD_CLIENT_ID, config.DISCORD_CLIENT_SECRET))
    client.parse_request_body_response(token_response.text)

    userinfo_response = requests.get(f"{config.DISCORD_API_BASE_URL}/users/@me", headers={
        "Authorization": f"Bearer {client.access_token}"
    })
    session['discord_user'] = userinfo_response.json()

    guilds_response = requests.get(f"{config.DISCORD_API_BASE_URL}/users/@me/guilds", headers={
        "Authorization": f"Bearer {client.access_token}"
    })
    user_guilds = guilds_response.json()

    for guild in user_guilds:
        if guild['id'] == config.DISCORD_GUILD_ID:
            role_check_response = requests.get(
                f"{config.DISCORD_API_BASE_URL}/guilds/{config.DISCORD_GUILD_ID}/members/{session['discord_user']['id']}",
                headers={"Authorization": f"Bearer {client.access_token}"}
            )
            if config.DISCORD_ROLE_ID in [role['id'] for role in role_check_response.json().get('roles', [])]:
                return redirect(url_for('form'))

    return "Unauthorized", 403

@app.route('/form', methods=['GET', 'POST'])
def form():
    if 'discord_user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Retrieve form data
        x, y, z = map(int, request.form['coordinates'].split(','))
        name = request.form['name'].replace(' ', '_')

        # Insert into the MySQL database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO your_table (x, y, z, name) VALUES (%s, %s, %s, %s)", (x, y, z, name))
        conn.commit()
        cursor.close()
        conn.close()

        return "Data submitted!"

    return render_template('form.html')

if __name__ == '__main__':
    waitress.serve(app, host='0.0.0.0', port=5000)
