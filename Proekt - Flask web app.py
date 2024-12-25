import sqlite3
from flask import Flask, request, jsonify
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, CallbackContext
from threading import Thread
import requests

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = '7576801255:AAHYG_Uhcduf3-DmsfdiBIz7yy-yck-m3Ik'
TELEGRAM_CHAT_IDS = [7442003971]
bot = Bot(token=TELEGRAM_BOT_TOKEN)

conn = sqlite3.connect('users_vouchers.db')
cursor = conn.cursor()
cursor.execute('''
         CREATE TABLE IF NOT EXISTS user_spending (
         user_id INTEGER,
         money_spent integer,
         year INTEGER
         )
''')
cursor.execute('''
         CREATE TABLE IF NOT EXISTS user_info (
         user_id INTEGER ,
         name TEXT,
         email TEXT,
         AGE INTEGER
         )
''')
cursor.execute('''
         CREATE TABLE IF NOT EXISTS high_spenders (
         user_id INTEGER ,
         total_spending INTEGER
         )
''')
conn.commit()
conn.close()


@app.route('/total_spent/<int:user_id>', methods=['GET'])
def total_spent(user_id):
    conn = sqlite3.connect('users_vouchers.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, SUM(money_spent) FROM user_spending WHERE user_id = ? GROUP BY user_id', (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return jsonify({'user_id': user[0], 'total_spent': user[1]})
    else:
        return jsonify({'error': 'Korisnikot ne e postoi ili nema nikakvi trosoci'})


@app.route('/average_spending_by_age', methods=['GET'])
def average_spending_by_age():
    results = calculate_average_spending()
    return jsonify(results)


def calculate_average_spending():
    conn = sqlite3.connect('users_vouchers.db')
    cursor = conn.cursor()

    query = '''
        SELECT 
            CASE 
                WHEN age BETWEEN 18 AND 24 THEN '18-24'
                WHEN age BETWEEN 25 AND 30 THEN '25-30'
                WHEN age BETWEEN 31 AND 36 THEN '31-36'
                WHEN age BETWEEN 37 AND 47 THEN '37-47'
                WHEN age > 47 THEN '>47'
            END AS age_group,
            AVG(money_spent) AS average_spending
        FROM user_spending
        JOIN user_info ON user_spending.user_id = user_info.user_id
        GROUP BY age_group
    '''
    cursor.execute(query)
    results = {row[0]: row[1] or 0 for row in cursor.fetchall()}
    conn.close()

    return results


def send_to_telegram(results):
    message = "Average Spending by Age Group:\n" + "\n".join(
        [f"{group}: ${spending:.2f}" for group, spending in results.items()])
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    for chat_id in TELEGRAM_CHAT_IDS:
        payload = {"chat_id": chat_id, "text": message}
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"Failed to send message to chat ID {chat_id}: {response.text}")


def handle_report(update: Update, context: CallbackContext) -> None:
    results = calculate_average_spending()
    send_to_telegram(results)
    # update.message.reply_text('The average spending by age group has been calculated and sent to the chat.')


def run_flask():
    app.run(debug=False, use_reloader=False)


def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("averagespending", handle_report))

    thread = Thread(target=run_flask)
    thread.daemon = True
    thread.start()

    application.run_polling()


@app.route('/write_high_spending_user', methods=['POST'])
def write_high_spending_user():
    data = request.get_json()
    user_id = data.get('user_id')
    total_spending = data.get('total_spending')

    if not user_id or total_spending is None:
        return jsonify({'error': 'Missing user_id or total_spending'})

    conn = sqlite3.connect('users_vouchers.db')
    cursor = conn.cursor()

    cursor.execute('SELECT user_id FROM user_info WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return jsonify({'error': 'User ne e pronajden'})

    try:
        total_spending = float(total_spending)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid total_spending'})

    cursor.execute('''
        INSERT OR REPLACE INTO high_spenders (user_id, total_spending)
        VALUES (?, ?)
    ''', (user_id, total_spending))
    conn.commit()
    conn.close()

    return jsonify({'message': 'User data e zacuvana uspesno'})


if __name__ == '__main__':
    main()
