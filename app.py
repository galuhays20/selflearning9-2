from flask import ( 
    Flask, 
    request, 
    render_template, 
    jsonify, 
    redirect, 
    url_for
)
from pymongo import MongoClient
import requests
from datetime import datetime
from bson import ObjectId
from dotenv import load_dotenv


dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME =  os.environ.get("DB_NAME")


app = Flask(__name__)

password = 'test123'
cxn_str = f'mongodb+srv://test:{password}@cluster0.tlly1pu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
client = MongoClient(cxn_str)

db = client.dbsparta_plus_week2

# Home page
@app.route('/')
def main():
    words_result = db.words.find({}, {'_id': False})
    words = []
    for word in words_result:
        definition = word['definitions'][0]['shortdef']
        definition = definition if type(definition) is str else definition[0]
        words.append({
            'word': word['word'],
            'definition': definition,
        })
    msg = request.args.get('msg')
    return render_template('index.html', words=words, msg=msg)

# Detail page for a specific word
@app.route('/detail/<keyword>')
def detail(keyword):
    api_key = '169a19e4-9f01-4764-a9a7-a80651aad622'
    url = f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{keyword}?key={api_key}'
    response = requests.get(url)
    definitions = response.json()

    if not definitions:
        # No definitions found, suggest alternatives
        suggestions = get_word_suggestions(keyword)
        return render_template('error.html', keyword=keyword, suggestions=suggestions)

    if type(definitions[0]) is str:
        # API might return a list of string suggestions
        suggestions = ", ".join(definitions)
        return render_template('error.html', keyword=keyword, suggestions=suggestions)

    status = request.args.get('status_give', 'new')
    return render_template('detail.html', word=keyword, definitions=definitions, status=status)

def get_word_suggestions(keyword):
    api_key = '169a19e4-9f01-4764-a9a7-a80651aad622'
    url = f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{keyword}?key={api_key}'
    response = requests.get(url)
    suggestions = response.json()

    if not suggestions:
        return "No suggestions available"

    if type(suggestions[0]) is str:
        # API might return a list of string suggestions
        return ", ".join(suggestions)

    # Extract word suggestions from the API response
    suggested_words = [suggestion['word'] for suggestion in suggestions]
    return suggested_words


# API endpoint to save a word
@app.route('/api/save_word', methods=['POST'])
def save_word():
    json_data = request.get_json()
    word = json_data.get('word_give')
    definitions = json_data.get('definitions_give')

    doc = {
        'word': word,
        'definitions': definitions,
        'date': datetime.now().strftime('%Y%m%d')
    }

    db.words.insert_one(doc)

    return jsonify({
        'result': 'success',
        'msg': f'The word "{word}" was saved!',
    })

# API endpoint to delete a word
@app.route('/api/delete_word', methods=['POST'])
def delete_word():
    word = request.form.get('word_give')
    db.words.delete_one({'word': word})
    db.examples.delete_many({'word': word})
    return jsonify({
        'result': 'success',
        'msg': f'The word "{word}" was deleted!',
    })


@app.route('/api/get_exs', methods=['GET'])
def get_exs():
    word = request.args.get('word')
    example_data = db.examples.find({'word': word})
    examples = []
    for example in example_data:
        examples.append({
            'example': example.get('example'),
            'id': str(example.get('_id')),
        })
    return jsonify({
        'result': 'success',
        'examples': examples
        })

@app.route('/api/save_ex', methods=['POST'])
def save_ex():
    word = request.form.get('word')
    example = request.form.get('example')
    doc = {
        'word': word,
        'example': example,
    }
    db.examples.insert_one(doc)

    return jsonify({
        'result': 'success',
        'msg': f'your example,{example}for the word,{word}, was saved!',
    })


@app.route('/api/delete_ex', methods=['POST'])
def delete_ex():
    id = request.form.get('id')
    word = request.form.get('word')
    db.examples.delete_one({'_id': ObjectId(id)})
    return jsonify({
        'result': 'success',
        'msg': f'your example for the word, {word}, was deleted!',
    
    })

# Run the Flask app
if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
