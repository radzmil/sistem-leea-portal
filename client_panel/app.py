# app.py - Panel Klien Sistem Leea & Enjin CRM (Modular Edition)
import os
import json
import logging
import base64
import requests
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from database import get_db_connection
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "sistem_leea_secret_key_2026")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

PORT = int(os.environ.get("PORT", 5000))

@app.route('/')
def index():
    return redirect(url_for('client_login'))

@app.route('/client/login', methods=['GET', 'POST'])
def client_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db_connection()
        if not conn:
            flash("Ralat sambungan pangkalan data.", "danger")
            return render_template('client_login.html')
            
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM clients WHERE username = %s", (username,))
        client = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if client:
            stored_hash = client.get('password_hash', '')
            login_valid = False
            
            if stored_hash and len(stored_hash) > 5:
                try:
                    login_valid = check_password_hash(stored_hash, password)
                except Exception:
                    login_valid = (password == 'defaultpass123')
            else:
                login_valid = (password == 'defaultpass123' or password == client.get('plain_password'))
                
            if login_valid:
                session['client_logged_in'] = True
                session['client_username'] = client['username']
                session['client_id'] = client['id']
                flash(f"Selamat datang, {client['nama_syarikat']}!", "success")
                return redirect(url_for('client_dashboard'))
                
        flash("ID Log Masuk atau Kata Sandi salah!", "danger")
            
    return render_template('client_login.html')

@app.route('/client/dashboard')
def client_dashboard():
    if not session.get('client_logged_in'):
        flash("Sila log masuk akaun klien terlebih dahulu!", "warning")
        return redirect(url_for('client_login'))
        
    client_id = session.get('client_id')
    conn = get_db_connection()
    if not conn:
        flash("Ralat pangkalan data.", "danger")
        return redirect(url_for('client_login'))
        
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM clients WHERE id = %s", (client_id,))
    client = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return render_template('client_dashboard.html', client=client)

@app.route('/api/client/dashboard-stats/', methods=['GET'])
def api_client_dashboard_stats(client_id):
    if not session.get('client_logged_in') or session.get('client_id') != client_id:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "error": "Database tidak tersambung"}), 500
        
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT sender, message, TO_CHAR(timestamp, 'HH24:MI:SS') as time_str
            FROM messages 
            WHERE client_id = %s 
            ORDER BY timestamp DESC LIMIT 1;
        """, (client_id,))
        latest_msg = cursor.fetchone()
        
        live_activity = "Menunggu interaksi pelanggan masuk..."
        if latest_msg:
            sender_display = latest_msg['sender'].replace("+", "")
            msg_preview = latest_msg['message'][:40] + ("..." if len(latest_msg['message']) > 40 else "")
            live_activity = f"Log Terkini [{latest_msg['time_str']}]: {sender_display} - {msg_preview}"

        cursor.execute("SELECT COUNT(*) as total FROM messages WHERE client_id = %s;", (client_id,))
        total_msgs = cursor.fetchone()['total'] or 0

        cursor.execute("""
            SELECT COUNT(DISTINCT sender) as leads 
            FROM messages 
            WHERE client_id = %s AND sender NOT ILIKE '%%Admin%%' AND sender NOT ILIKE '%%Zulfa%%';
        """, (client_id,))
        total_leads = cursor.fetchone()['leads'] or 0

        cursor.execute("SELECT COUNT(*) as today FROM messages WHERE client_id = %s AND DATE(timestamp) = CURRENT_DATE;", (client_id,))
        msgs_today = cursor.fetchone()['today'] or 0

        cursor.execute("SELECT COUNT(*) as bot_total FROM messages WHERE client_id = %s AND sender ILIKE '%%Zulfa%%';", (client_id,))
        total_bot = cursor.fetchone()['bot_total'] or 0
        
        cursor.execute("SELECT COUNT(*) as admin_total FROM messages WHERE client_id = %s AND sender ILIKE '%%Admin%%';", (client_id,))
        total_admin = cursor.fetchone()['admin_total'] or 0

        total_replies = total_bot + total_admin
        ai_rate = 0.0
        manual_rate = 0.0
        if total_replies > 0:
            ai_rate = (total_bot / total_replies) * 100
            manual_rate = (total_admin / total_replies) * 100

        real_estimated_sales = total_bot * 50.00
        real_closed_deals = int(total_bot / 3) if total_bot > 0 else 0

        widget_data = {
            'stat1_title': 'JUMLAH PROSPEK UNIK', 
            'stat1_val': f"{total_leads} Orang", 
            'stat1_sub': 'Pelanggan Dalam Pangkalan',
            'stat2_title': 'TRAFIK MESEJ HARI INI', 
            'stat2_val': f"{msgs_today} Mesej", 
            'stat2_sub': 'Interaksi Semasa',
            'stat3_title': 'KESELURUHAN INTERAKSI', 
            'stat3_val': f"{total_msgs} Rekod", 
            'stat3_sub': 'Sejarah Sepanjang Masa'
        }

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "live_activity": live_activity,
            "estimated_sales": f"RM {real_estimated_sales:,.2f}",
            "closed_deals": real_closed_deals,
            "ai_rate": f"{ai_rate:.1f}%",
            "conversion_pct": f"{min(100, total_leads * 10)}%",
            "manual_pct": f"{manual_rate:.1f}%",
            "widgets": widget_data
        })
    except Exception as e:
        logging.error(f"Ralat statistik: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/client/analytics-stats/', methods=['GET'])
def api_client_analytics_stats(client_id):
    if not session.get('client_logged_in') or session.get('client_id') != client_id:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "error": "DB disconnected"}), 500
        
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT EXTRACT(ISODOW FROM timestamp) as dow, COUNT(*) as msg_count
            FROM messages WHERE client_id = %s AND timestamp >= NOW() - INTERVAL '7 days'
            GROUP BY dow ORDER BY dow;
        """, (client_id,))
        rows = cursor.fetchall()
        msg_data_map = {int(row['dow']): row['msg_count'] for row in rows}
        msg_counts = [msg_data_map.get(i, 0) for i in range(1, 8)]
        
        cursor.execute("""
            SELECT EXTRACT(ISODOW FROM timestamp) as dow, COUNT(DISTINCT sender) as lead_count
            FROM messages WHERE client_id = %s AND timestamp >= NOW() - INTERVAL '7 days'
              AND sender NOT ILIKE '%%Admin%%' AND sender NOT ILIKE '%%Zulfa%%'
            GROUP BY dow ORDER BY dow;
        """, (client_id,))
        lead_rows = cursor.fetchall()
        lead_data_map = {int(row['dow']): row['lead_count'] for row in lead_rows}
        lead_counts = [lead_data_map.get(i, 0) for i in range(1, 8)]

        cursor.close()
        conn.close()

        return jsonify({'success': True, 'msg_counts': msg_counts, 'lead_counts': lead_counts})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/client/senders/', methods=['GET'])
def api_get_client_senders(client_id):
    if not session.get('client_logged_in') or session.get('client_id') != client_id:
        return jsonify({"error": "Unauthorized"}), 401
        
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT DISTINCT sender FROM messages 
            WHERE client_id = %s AND sender NOT ILIKE '%%Admin%%' AND sender NOT ILIKE '%%Zulfa%%'
            ORDER BY sender DESC;
        """, (client_id,))
        senders = [row['sender'] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return jsonify(senders)
    except Exception:
        return jsonify([])

@app.route('/api/client/chat/', methods=['GET'])
def api_get_chat_by_sender(client_id):
    if not session.get('client_logged_in') or session.get('client_id') != client_id:
        return jsonify({"error": "Unauthorized"}), 401
        
    phone = request.args.get('phone', '')
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT sender, message, TO_CHAR(timestamp, 'DD-MM-YYYY HH24:MI:SS') as timestamp 
            FROM messages WHERE client_id = %s AND (sender = %s OR sender LIKE 'Zulfa%%' OR sender = 'Admin')
            ORDER BY id ASC;
        """, (client_id, phone))
        messages = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(messages)
    except Exception:
        return jsonify([])

@app.route('/api/client/reply', methods=['POST'])
def api_client_manual_reply():
    if not session.get('client_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.json or {}
    client_id = session.get('client_id')
    recipient_phone = data.get('phone', '').strip()
    message_text = data.get('message', '').strip()
    
    if not recipient_phone or not message_text:
        return jsonify({"success": False, "error": "Maklumat tidak lengkap"}), 400
        
    try:
        token = os.getenv("WHATSAPP_TOKEN")
        phone_number_id = os.getenv("PHONE_NUMBER_ID", "1274341599093050")
        
        if token:
            clean_phone = recipient_phone.replace("+", "").strip()
            url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            payload = {"messaging_product": "whatsapp", "to": clean_phone, "type": "text", "text": {"body": message_text}}
            requests.post(url, json=payload, headers=headers, timeout=10)
            
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO messages (client_id, sender, message, timestamp) VALUES (%s, 'Admin', %s, NOW());", (client_id, message_text))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"success": True, "message": "Balasan berjaya dihantar!"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/client/toggle-mode', methods=['POST'])
def api_toggle_client_mode():
    if not session.get('client_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.json or {}
    phone = data.get('phone', '').strip()
    mode = data.get('mode', 'ai').strip()
    client_id = session.get('client_id')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS chat_modes (client_id INT, phone VARCHAR(50), mode VARCHAR(20), PRIMARY KEY (client_id, phone));")
        cursor.execute("INSERT INTO chat_modes (client_id, phone, mode) VALUES (%s, %s, %s) ON CONFLICT (client_id, phone) DO UPDATE SET mode = EXCLUDED.mode;", (client_id, phone.replace("+", "").strip(), mode))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": f"Mod ditukar kepada {mode.upper()}!"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/client/update-admin-phone', methods=['POST'])
def api_update_admin_phone():
    if not session.get('client_logged_in'):
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    data = request.json or {}
    client_id = data.get('client_id') or session.get('client_id')
    admin_phone = data.get('admin_phone', '').strip()
    
    if not admin_phone:
        return jsonify({"success": False, "error": "Nombor telefon tidak boleh kosong"}), 400
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE clients SET no_wa_bot = %s WHERE id = %s;", (admin_phone, client_id))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Nombor admin berjaya dikemas kini!"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/client/notifications/', methods=['GET'])
def api_get_client_notifications(client_id):
    if not session.get('client_logged_in') or session.get('client_id') != client_id:
        return jsonify([]), 401
    conn = get_db_connection()
    if not conn:
        return jsonify([]), 200
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT id, title, message, is_read, TO_CHAR(created_at, 'DD/MM/YYYY HH24:MI') as time 
            FROM admin_notifications 
            WHERE client_id IS NULL OR client_id = %s 
            ORDER BY created_at DESC LIMIT 15;
        """, (client_id,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        notifs = []
        for r in rows:
            notifs.append({
                "id": r['id'],
                "title": r['title'],
                "message": r['message'],
                "read": r['is_read'],
                "time": r['time']
            })
        return jsonify(notifs), 200
    except Exception:
        return jsonify([]), 200

@app.route('/api/client/notification/read', methods=['POST'])
def api_mark_notification_read():
    if not session.get('client_logged_in'):
        return jsonify({"success": False}), 401
    data = request.json or {}
    notif_id = data.get('id')
    conn = get_db_connection()
    if conn and notif_id:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE admin_notifications SET is_read = TRUE WHERE id = %s;", (notif_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({"success": True}), 200
        except Exception:
            pass
    return jsonify({"success": False}), 400

@app.route('/api/client/notification/delete', methods=['POST'])
def api_delete_notification():
    if not session.get('client_logged_in'):
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    data = request.json or {}
    notif_id = data.get('id')
    
    conn = get_db_connection()
    if conn and notif_id:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM admin_notifications WHERE id = %s;", (notif_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({"success": True}), 200
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
            
    return jsonify({"success": False, "error": "ID tidak sah"}), 400

@app.route('/client/update_profile', methods=['POST'])
def client_update_profile():
    if not session.get('client_logged_in'):
        return redirect(url_for('client_login'))
        
    client_id = session.get('client_id')
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    logo_file = request.files.get('logo_file')
    
    conn = get_db_connection()
    if not conn:
        flash("Ralat sambungan pangkalan data.", "danger")
        return redirect(url_for('client_dashboard'))
        
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM clients WHERE id = %s", (client_id,))
        client = cursor.fetchone()
        
        if new_password and current_password:
            stored_hash = client.get('password_hash', '')
            is_current_valid = check_password_hash(stored_hash, current_password) if (stored_hash and len(stored_hash) > 5) else (current_password == 'defaultpass123' or current_password == client.get('plain_password'))
            
            if is_current_valid:
                new_hash = generate_password_hash(new_password)
                cursor.execute("UPDATE clients SET password_hash = %s, plain_password = %s WHERE id = %s", (new_hash, new_password, client_id))
                conn.commit()
                flash("Kata laluan berjaya dikemaskini!", "success")
            else:
                flash("Kata laluan semasa salah!", "danger")
                
        if logo_file and logo_file.filename:
            file_data = logo_file.read()
            base64_encoded = base64.b64encode(file_data).decode('utf-8')
            mime_type = logo_file.content_type
            logo_base64_url = f"data:{mime_type};base64,{base64_encoded}"
            
            cursor.execute("UPDATE clients SET logo_path = %s WHERE id = %s", (logo_base64_url, client_id))
            conn.commit()
            flash("Logo berjaya dimuat naik!", "success")
            
        cursor.close()
        conn.close()
    except Exception as e:
        flash(f"Ralat kemaskini profil: {e}", "danger")
        
    return redirect(url_for('client_dashboard'))

@app.route('/client/logout')
def client_logout():
    session.clear()
    flash("Sesi klien telah ditamatkan.", "info")
    return redirect(url_for('client_login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=True)