from flask import Flask, render_template, request, redirect, url_for, flash
import os
import threading
from uuid import uuid4
import schedule
import subprocess
import time

from utils import assert_folder_structure, rem_temp_files, fetch_songs, get_first_time_running
from cache import get_accounts, add_account, remove_account, get_products, add_product
from config import ROOT_DIR, get_ollama_model
from llm_provider import select_model, get_active_model
from classes.YouTube import YouTube
from classes.Twitter import Twitter
from classes.AFM import AffiliateMarketing
from classes.Outreach import Outreach

app = Flask(__name__)
app.secret_key = 'moneyprinter_secret_key'  # Needed for flash messages

# Select model on startup
configured_model = get_ollama_model()
if configured_model:
    try:
        select_model(configured_model)
    except Exception as e:
        print(f"Warning: Could not select model {configured_model}: {e}")

@app.route('/')
def index():
    return render_template('index.html')

# --- YOUTUBE ROUTES ---
@app.route('/youtube')
def youtube_list():
    accounts = get_accounts("youtube")
    return render_template('youtube.html', accounts=accounts)

@app.route('/youtube/add', methods=['POST'])
def youtube_add():
    generated_uuid = str(uuid4())
    account_data = {
        "id": generated_uuid,
        "nickname": request.form['nickname'],
        "firefox_profile": request.form['firefox_profile'],
        "niche": request.form['niche'],
        "language": request.form['language'],
        "videos": [],
    }
    add_account("youtube", account_data)
    flash(f"Account '{account_data['nickname']}' added successfully!", "success")
    return redirect(url_for('youtube_list'))

@app.route('/youtube/delete/<account_id>', methods=['POST'])
def youtube_delete(account_id):
    remove_account("youtube", account_id)
    flash("Account deleted.", "success")
    return redirect(url_for('youtube_list'))

@app.route('/youtube/<account_id>')
def youtube_manage(account_id):
    accounts = get_accounts("youtube")
    account = next((a for a in accounts if a['id'] == account_id), None)
    if not account:
        flash("Account not found.", "danger")
        return redirect(url_for('youtube_list'))

    youtube = YouTube(
        account["id"],
        account["nickname"],
        account["firefox_profile"],
        account["niche"],
        account["language"]
    )
    videos = youtube.get_videos()
    return render_template('youtube_manage.html', account=account, videos=videos)

@app.route('/youtube/<account_id>/generate', methods=['POST'])
def youtube_generate(account_id):
    accounts = get_accounts("youtube")
    account = next((a for a in accounts if a['id'] == account_id), None)
    if not account:
        flash("Account not found.", "danger")
        return redirect(url_for('youtube_list'))

    try:
        youtube = YouTube(
            account["id"],
            account["nickname"],
            account["firefox_profile"],
            account["niche"],
            account["language"]
        )
        from classes.Tts import TTS
        tts = TTS()
        youtube.generate_video(tts)
        if request.form.get('upload_to_yt'):
            youtube.upload_video()
            flash("Video generated and uploaded successfully!", "success")
        else:
            flash("Video generated successfully! (Not uploaded)", "success")
    except Exception as e:
        flash(f"An error occurred: {e}", "danger")

    return redirect(url_for('youtube_manage', account_id=account_id))

@app.route('/youtube/<account_id>/cron', methods=['POST'])
def youtube_cron(account_id):
    accounts = get_accounts("youtube")
    account = next((a for a in accounts if a['id'] == account_id), None)
    if not account:
        flash("Account not found.", "danger")
        return redirect(url_for('youtube_list'))

    frequency = request.form.get('frequency')
    cron_script_path = os.path.join(ROOT_DIR, "src", "cron.py")
    command = ["python", cron_script_path, "youtube", account['id'], get_active_model()]

    def job():
        subprocess.run(command)

    if frequency == "1":
        schedule.every(1).day.do(job)
        flash("Set up CRON Job for Once a day.", "success")
    elif frequency == "2":
        schedule.every().day.at("10:00").do(job)
        schedule.every().day.at("16:00").do(job)
        flash("Set up CRON Job for Twice a day.", "success")
    elif frequency == "3":
        schedule.every().day.at("08:00").do(job)
        schedule.every().day.at("12:00").do(job)
        schedule.every().day.at("18:00").do(job)
        flash("Set up CRON Job for Thrice a day.", "success")

    return redirect(url_for('youtube_manage', account_id=account_id))

# --- TWITTER ROUTES ---
@app.route('/twitter')
def twitter_list():
    accounts = get_accounts("twitter")
    return render_template('twitter.html', accounts=accounts)

@app.route('/twitter/add', methods=['POST'])
def twitter_add():
    generated_uuid = str(uuid4())
    account_data = {
        "id": generated_uuid,
        "nickname": request.form['nickname'],
        "firefox_profile": request.form['firefox_profile'],
        "topic": request.form['topic'],
        "posts": []
    }
    add_account("twitter", account_data)
    flash(f"Twitter account '{account_data['nickname']}' added successfully!", "success")
    return redirect(url_for('twitter_list'))

@app.route('/twitter/delete/<account_id>', methods=['POST'])
def twitter_delete(account_id):
    remove_account("twitter", account_id)
    flash("Account deleted.", "success")
    return redirect(url_for('twitter_list'))

@app.route('/twitter/<account_id>')
def twitter_manage(account_id):
    accounts = get_accounts("twitter")
    account = next((a for a in accounts if a['id'] == account_id), None)
    if not account:
        flash("Account not found.", "danger")
        return redirect(url_for('twitter_list'))

    twitter = Twitter(
        account["id"],
        account["nickname"],
        account["firefox_profile"],
        account["topic"]
    )
    posts = twitter.get_posts()
    return render_template('twitter_manage.html', account=account, posts=posts)

@app.route('/twitter/<account_id>/post', methods=['POST'])
def twitter_post(account_id):
    accounts = get_accounts("twitter")
    account = next((a for a in accounts if a['id'] == account_id), None)
    if not account:
        flash("Account not found.", "danger")
        return redirect(url_for('twitter_list'))

    try:
        twitter = Twitter(
            account["id"],
            account["nickname"],
            account["firefox_profile"],
            account["topic"]
        )
        twitter.post()
        flash("Tweet posted successfully!", "success")
    except Exception as e:
        flash(f"An error occurred while posting: {e}", "danger")

    return redirect(url_for('twitter_manage', account_id=account_id))

@app.route('/twitter/<account_id>/cron', methods=['POST'])
def twitter_cron(account_id):
    accounts = get_accounts("twitter")
    account = next((a for a in accounts if a['id'] == account_id), None)
    if not account:
        flash("Account not found.", "danger")
        return redirect(url_for('twitter_list'))

    frequency = request.form.get('frequency')
    cron_script_path = os.path.join(ROOT_DIR, "src", "cron.py")
    command = ["python", cron_script_path, "twitter", account['id'], get_active_model()]

    def job():
        subprocess.run(command)

    if frequency == "1":
        schedule.every(1).day.do(job)
        flash("Set up CRON Job for Once a day.", "success")
    elif frequency == "2":
        schedule.every().day.at("10:00").do(job)
        schedule.every().day.at("16:00").do(job)
        flash("Set up CRON Job for Twice a day.", "success")
    elif frequency == "3":
        schedule.every().day.at("08:00").do(job)
        schedule.every().day.at("12:00").do(job)
        schedule.every().day.at("18:00").do(job)
        flash("Set up CRON Job for Thrice a day.", "success")

    return redirect(url_for('twitter_manage', account_id=account_id))


# --- AFFILIATE MARKETING ROUTES ---
@app.route('/affiliate')
def affiliate_list():
    products = get_products()
    twitter_accounts = get_accounts("twitter")
    return render_template('affiliate.html', products=products, twitter_accounts=twitter_accounts)

@app.route('/affiliate/add', methods=['POST'])
def affiliate_add():
    product_data = {
        "id": str(uuid4()),
        "affiliate_link": request.form['affiliate_link'],
        "twitter_uuid": request.form['twitter_uuid']
    }
    add_product(product_data)
    flash("Affiliate product added successfully!", "success")
    return redirect(url_for('affiliate_list'))

@app.route('/affiliate/<product_id>/share', methods=['POST'])
def affiliate_share(product_id):
    products = get_products()
    product = next((p for p in products if p['id'] == product_id), None)
    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for('affiliate_list'))

    accounts = get_accounts("twitter")
    account = next((a for a in accounts if a['id'] == product['twitter_uuid']), None)

    if not account:
        flash("Associated Twitter account not found.", "danger")
        return redirect(url_for('affiliate_list'))

    try:
        afm = AffiliateMarketing(
            product["affiliate_link"],
            account["firefox_profile"],
            account["id"],
            account["nickname"],
            account["topic"]
        )
        afm.generate_pitch()
        afm.share_pitch("twitter")
        flash("Pitch generated and shared successfully!", "success")
    except Exception as e:
        flash(f"An error occurred: {e}", "danger")

    return redirect(url_for('affiliate_list'))


# --- OUTREACH ROUTES ---
@app.route('/outreach')
def outreach_index():
    return render_template('outreach.html')

@app.route('/outreach/start', methods=['POST'])
def outreach_start():
    try:
        outreach = Outreach()

        # We can either run this synchronously (might block web server for a long time)
        # or in a separate thread. For simplicity, we run it in a thread so the UI responds.
        def run_outreach():
            try:
                outreach.start()
                print("Outreach completed successfully.")
            except Exception as e:
                print(f"Outreach failed: {e}")

        thread = threading.Thread(target=run_outreach)
        thread.start()

        flash("Outreach campaign started in the background! Check the console/logs for progress.", "success")
    except Exception as e:
        flash(f"An error occurred: {e}", "danger")

    return redirect(url_for('outreach_index'))


def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    assert_folder_structure()
    rem_temp_files()
    fetch_songs()

    # Start the background thread for scheduling
    schedule_thread = threading.Thread(target=run_schedule, daemon=True)
    schedule_thread.start()

    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
