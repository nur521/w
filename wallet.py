from flask import Flask, request, render_template
import sqlite3

app = Flask(__name__)

# Подключение к базе данных SQLite3
def connect_db():
    return sqlite3.connect('tokens.db')

@app.route('/')
def index():
    return render_template('wallet.html')

@app.route('/submit_wallet', methods=['POST'])
def submit_wallet():
    wallet_address = request.form['wallet']
    user_id = request.form['userid']
    
    # Обновляем запись в базе данных с UserID и WalletAddress
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users
        SET wallet_address = ?
        WHERE user_id = ?
    ''', (wallet_address, user_id))
    
    conn.commit()
    conn.close()
    
    return "Адрес кошелька успешно сохранён!"

if __name__ == '__main__':
    app.run(debug=True)
