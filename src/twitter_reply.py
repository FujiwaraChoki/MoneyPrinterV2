import time
import random
import urllib.parse
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests 

class TwitterReplyBot:
    def __init__(self, driver, keywords):
        """
        Initializes the bot with the existing Selenium driver 
        (passed from the main MPV2 execution) and your search keywords.
        """
        self.driver = driver
        self.keywords = keywords


    def _extract_tweets_from_page(self, max_tweets):
        """
        Internal method to parse the DOM and extract the raw text from tweet elements.
        """
        tweet_data = []
        try:
            # Wait until at least one tweet is present on the page
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//article[@data-testid="tweet"]'))
            )
            
            # Grab all tweet article elements currently loaded in the DOM
            tweets = self.driver.find_elements(By.XPATH, '//article[@data-testid="tweet"]')
            
            for tweet in tweets:
                # Stop if we hit our requested limit per keyword
                if len(tweet_data) >= max_tweets:
                    break
                    
                try:
                    # Find the actual text content block inside the tweet article
                    text_element = tweet.find_element(By.XPATH, './/div[@data-testid="tweetText"]')
                    tweet_text = text_element.text
                    
                    # Store both the text and the web element itself 
                    # (we need the element later to click the reply button!)
                    tweet_data.append({
                        "text": tweet_text,
                        "element": tweet
                    })
                except Exception:
                    # If a tweet has no text (e.g., just an image or a weird ad), skip it safely
                    continue
                    
        except Exception as e:
            print(f"[-] Could not extract tweets. Page might not have loaded correctly. Error: {e}")
            
        return tweet_data
    def generate_reply(self, openrouter_key, tweet_text):
        """
        Sends the extracted tweet to your local Ollama model to generate a reply.
        """
        print("[*] Generating AI reply via local Ollama...")
        
        prompt = f"""
        You are a helpful, casual human user on Twitter. 
        Read this tweet: "{tweet_text}"
        Write a short, natural-sounding helpful reply (under 200 characters).
        Do not use hashtags. Do not sound robotic or like an AI. 
        Keep it conversational. Just output the reply text, nothing else.
        """
        
        data = {
            "model": "llama3:latest", 
            "prompt": prompt,
            "stream": False
        }
        
        try:
            import requests 
            # Send the request directly to your local computer's port 11434
            response = requests.post("http://localhost:11434/api/generate", json=data)
            
            if response.status_code == 200:
                reply_text = response.json()['response'].strip(' "')
                print(f"[+] Generated Reply: {reply_text}")
                return reply_text
            else:
                print(f"[-] Ollama API Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"[-] Python Error during AI generation: {e}")
            return None

    def post_reply(self, tweet_element, reply_text):
        """
        Uses browser automation to click the reply button, type the text, and hit send.
        """
        try:
            # 1. Click the reply icon 
            reply_button = tweet_element.find_element(By.XPATH, './/*[@data-testid="reply"]')
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", reply_button)
            time.sleep(1)
            self.driver.execute_script("arguments[0].click();", reply_button)
            time.sleep(random.uniform(1.5, 3.0))
            
            # 2. Locate the reply input text box
            text_area = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@data-testid="tweetTextarea_0"]'))
            )
            
            # 3. Inject the AI-generated text
            text_area.send_keys(reply_text)
            time.sleep(random.uniform(1, 2))
            
            # 4. Click the final 'Reply' submit button (Using wildcard * and a Wait)
            submit_button = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//*[@data-testid="tweetButton"]'))
            )
            self.driver.execute_script("arguments[0].click();", submit_button)
            
            print("[+] Successfully posted reply!")
            
            # Wait for the modal to fully close before moving to the next tweet
            time.sleep(random.uniform(2, 4))
            return True
            
        except Exception as e:
            print(f"[-] Could not post reply. Error: {e}")
            
            # SAFETY FALLBACK: If posting fails, try to close the modal so it doesn't break the next tweet!
            try:
                close_button = self.driver.find_element(By.XPATH, '//*[@aria-label="Close"]')
                self.driver.execute_script("arguments[0].click();", close_button)
                print("[*] Modal closed to protect next iteration.")
                time.sleep(1)
            except:
                pass
                
            return False

    def run(self, config):
        """
        The main execution loop. Searches, scrapes, and replies one keyword at a time
        so the browser doesn't navigate away and cause StaleElement errors.
        """
        automation_config = config.get("twitter_reply_automation", {})
        max_replies = automation_config.get("max_replies_per_run", 5)
        delay_range = automation_config.get("delay_between_replies", [30, 120])
        api_key = config.get("openrouter_api_key", "")
        
        replies_sent = 0
        
        # Loop through one keyword at a time
        for keyword in self.keywords:
            if replies_sent >= max_replies:
                print("[*] Reached max replies for this run. Stopping to prevent rate limits.")
                break
                
            print(f"[*] Searching Twitter for keyword: '{keyword}'")
            query = urllib.parse.quote(keyword)
            search_url = f"https://twitter.com/search?q={query}&src=typed_query&f=live"
            
            # Navigate to the page
            self.driver.get(search_url)
            time.sleep(random.uniform(4, 7))
            
            # Scrape tweets ONLY for the current page
            tweets_on_page = self._extract_tweets_from_page(max_tweets=2)
            print(f"[+] Found {len(tweets_on_page)} tweets for '{keyword}'.\n")
            
            # Reply to them immediately before changing pages!
            for tweet_data in tweets_on_page:
                if replies_sent >= max_replies:
                    break
                    
                reply_text = self.generate_reply(api_key, tweet_data['text'])
                
                if reply_text:
                    success = self.post_reply(tweet_data['element'], reply_text)
                    
                    if success:
                        replies_sent += 1
                        sleep_time = random.uniform(delay_range[0], delay_range[1])
                        print(f"[*] Sleeping for {int(sleep_time)} seconds to mimic human behavior...\n")
                        time.sleep(sleep_time)