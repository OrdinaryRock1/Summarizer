import os
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import re
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
CORS(app) 

api = os.environ.get("GEMINI_API_KEY")

if not api:
    raise ValueError("Chybí API klíč! Nastavte proměnnou GEMINI_API_KEY.")

genai.configure(api_key=api)
model = genai.GenerativeModel('gemini-2.5-flash')

def ziskej_text_videa(video_url):
    try:
        video_id = video_url.split("v=")[1][:11] 
        titulky = YouTubeTranscriptApi.get_transcript(video_id, languages=['cs', 'en'])
        cely_text = " ".join([polozka['text'] for polozka in titulky])
        return cely_text
    except Exception as e:
        return f"Chyba: {e}"

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
    prompt = f"Zde je přepis YouTube videa. Udělej z něj přehledné a strukturované shrnutí v češtině. Zvýrazni hlavní body pomocí odrážek nebo krátkých odstavců. Vynech zbytečnou vatu:\n\n{text}"
    odpoved = model.generate_content(prompt)
    return odpoved.text

@app.route('/api/sumarizovat', methods=['POST', 'OPTIONS'])
def api_sumarizovat():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*") # Povolí všechny původy
        response.headers.add("Access-Control-Allow-Headers", "Content-Type") # Povolí JSON
        response.headers.add("Access-Control-Allow-Methods", "POST")
        return response

    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({"error": "Chybí URL adresa"}), 400

    text_videa = ziskej_text_videa(url)
    if "Chyba" in text_videa:
        return jsonify({"error": text_videa}), 400

    shrnuti = sumarizuj_text(text_videa)

    response = jsonify({"summary": shrnuti})
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
