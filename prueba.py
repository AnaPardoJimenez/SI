from quart import Quart, jsonify

app = Quart(__name__)

@app.route('/hello')
async def hello():
    return jsonify({'message': 'Hello, World!'})

if __name__ == '__main__':
    app.run(host='localhost', port=5050)