import os
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi
from google import genai
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

CORS(app, resources={r"/api/*": {"origins": "https://ordinaryrock1.github.io"}})

key = os.environ.get("GEMINI_API_KEY")
if not key:
    raise ValueError("Chybí API klíč!")

client = genai.Client(api_key=key)

def ziskej_text_videa(video_url):
    try:
        match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", video_url)
        if not match:
            return "Chyba: Nepodařilo se rozpoznat YouTube odkaz."
        video_id = match.group(1) 
        
        api = YouTubeTranscriptApi()
        seznam_titulku = api.list(video_id)
        titulky_objekt = seznam_titulku.find_transcript(['cs', 'en'])
        titulky_data = titulky_objekt.fetch()
        
        cely_text = " ".join([polozka.text for polozka in titulky_data])
        return cely_text
    except Exception as e:
        return f"Chyba při stahování titulků: {str(e)}"

def sumarizuj_text(text):
    prompt = f"Zde je přepis videa. Udělej z něj přehledné a strukturované shrnutí v češtině. Zvýrazni hlavní body pomocí odrážek nebo krátkých odstavců. Vynech zbytečnou vatu:\n\n{text}"
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    return response.text

@app.route('/api/sumarizovat', methods=['POST'])
def api_sumarizovat():
    try:
        data = request.get_json(force=True)
        
        if not data or 'url' not in data:
            return jsonify({"error": f"Nenašel jsem URL. Data vypadají takto: {request.data.decode('utf-8')}"}), 400

        url = data['url']
        text_videa = ziskej_text_videa(url)
        
        if "Chyba" in text_videa:
            return jsonify({"error": text_videa}), 400

        shrnuti = sumarizuj_text(text_videa)
        return jsonify({"summary": shrnuti})

    except Exception as e:
        return jsonify({"error": f"Chyba při čtení dat: {str(e)}"}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
