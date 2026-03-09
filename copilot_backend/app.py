from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)


TOKEN_URLS = {
    "ask_finance": "https://default534253fcdfb6462fb5cacbe81939f5.ee.environment.api.powerplatform.com/powervirtualagents/botsbyschema/crad5_agent3/directline/token?api-version=2022-03-01-preview",
    "ask_enterprise": "https://default534253fcdfb6462fb5cacbe81939f5.ee.environment.api.powerplatform.com/powervirtualagents/botsbyschema/crad5_agent2/directline/token?api-version=2022-03-01-preview",
    "ask_products": "https://default534253fcdfb6462fb5cacbe81939f5.ee.environment.api.powerplatform.com/powervirtualagents/botsbyschema/copilots_header_813e8/directline/token?api-version=2022-03-01-preview",

    "ask_scm": "https://default534253fcdfb6462fb5cacbe81939f5.ee.environment.api.powerplatform.com/powervirtualagents/botsbyschema/copilots_header_797da/directline/token?api-version=2022-03-01-preview",
    "ask_process": "https://default534253fcdfb6462fb5cacbe81939f5.ee.environment.api.powerplatform.com/powervirtualagents/botsbyschema/crad5_agent3_c0p6qM/directline/token?api-version=2022-03-01-preview",
    "ask_mintcrm": "https://default534253fcdfb6462fb5cacbe81939f5.ee.environment.api.powerplatform.com/powervirtualagents/botsbyschema/copilots_header_8f16f/directline/token?api-version=2022-03-01-preview",
    "backoffice_email": "https://default534253fcdfb6462fb5cacbe81939f5.ee.environment.api.powerplatform.com/powervirtualagents/botsbyschema/copilots_header_a245b/directline/token?api-version=2022-03-01-preview",

}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/get_token")
def get_token():
    try:
        domain = (request.args.get("domain") or "ask_finance").lower().strip()

        url = TOKEN_URLS.get(domain)
        if not url:
            return jsonify({
                "error": f"No DirectLine token URL configured for domain '{domain}'",
                "configured_domains": list(TOKEN_URLS.keys())
            }), 400

        response = requests.get(url, timeout=20)
        response.raise_for_status()
        data = response.json()
        return jsonify({"token": data.get("token")})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)
