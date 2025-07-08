import requests
import unittest
import json
from datetime import datetime

class TwitterScraperAPITest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TwitterScraperAPITest, self).__init__(*args, **kwargs)
        self.base_url = "https://214afa96-935d-4512-a913-d5d8ac715108.preview.emergentagent.com/api"
        self.session = requests.Session()
    
    def test_01_health_check(self):
        """Test API health check endpoint"""
        print("\n🔍 Testing API health check...")
        response = self.session.get(f"{self.base_url}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "Twitter Scraper API is running")
        print("✅ API health check passed")
    
    def test_02_get_analytics(self):
        """Test analytics endpoint"""
        print("\n🔍 Testing analytics endpoint...")
        response = self.session.get(f"{self.base_url}/analytics")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify analytics structure
        self.assertIn("total_tweets", data)
        self.assertIn("avg_quality_score", data)
        self.assertIn("avg_engagement_score", data)
        self.assertIn("sentiment_distribution", data)
        self.assertIn("top_categories", data)
        print("✅ Analytics endpoint passed")
    
    def test_03_get_tweets(self):
        """Test tweets endpoint"""
        print("\n🔍 Testing tweets endpoint...")
        response = self.session.get(f"{self.base_url}/tweets?limit=5")
        self.assertEqual(response.status_code, 200)
        tweets = response.json()
        
        if tweets:
            # Verify tweet structure
            tweet = tweets[0]
            self.assertIn("id", tweet)
            self.assertIn("tweet_data", tweet)
            self.assertIn("ai_analysis", tweet)
            self.assertIn("text", tweet["tweet_data"])
            self.assertIn("author", tweet["tweet_data"])
            self.assertIn("sentiment", tweet["ai_analysis"])
            print(f"✅ Tweets endpoint passed - returned {len(tweets)} tweets")
        else:
            print("⚠️ Tweets endpoint returned no tweets - this might be expected if no scraping has been done yet")
    
    def test_04_get_sessions(self):
        """Test scraping sessions endpoint"""
        print("\n🔍 Testing scraping sessions endpoint...")
        response = self.session.get(f"{self.base_url}/scraper/sessions?limit=5")
        self.assertEqual(response.status_code, 200)
        sessions = response.json()
        
        if sessions:
            # Verify session structure
            session = sessions[0]
            self.assertIn("id", session)
            self.assertIn("started_at", session)
            self.assertIn("status", session)
            self.assertIn("tweets_processed", session)
            print(f"✅ Sessions endpoint passed - returned {len(sessions)} sessions")
        else:
            print("⚠️ Sessions endpoint returned no sessions - this might be expected if no scraping has been done yet")
    
    def test_05_get_scheduler_status(self):
        """Test scheduler status endpoint"""
        print("\n🔍 Testing scheduler status endpoint...")
        response = self.session.get(f"{self.base_url}/scheduler/status")
        self.assertEqual(response.status_code, 200)
        status = response.json()
        
        # Verify scheduler status structure
        self.assertIn("running", status)
        self.assertIn("jobs", status)
        print(f"✅ Scheduler status endpoint passed - scheduler is {'running' if status['running'] else 'stopped'}")
    
    def test_06_get_config(self):
        """Test config endpoint"""
        print("\n🔍 Testing config endpoint...")
        response = self.session.get(f"{self.base_url}/config")
        self.assertEqual(response.status_code, 200)
        config = response.json()
        
        # Verify config structure
        self.assertIn("enabled", config)
        self.assertIn("schedule_interval", config)
        self.assertIn("max_retries", config)
        self.assertIn("batch_size", config)
        print("✅ Config endpoint passed")
    
    def test_07_run_scraping(self):
        """Test manual scraping trigger"""
        print("\n🔍 Testing manual scraping trigger...")
        response = self.session.post(f"{self.base_url}/scraper/run")
        self.assertEqual(response.status_code, 200)
        session = response.json()
        
        # Verify session structure
        self.assertIn("id", session)
        self.assertIn("started_at", session)
        self.assertIn("status", session)
        self.assertIn("tweets_processed", session)
        print(f"✅ Manual scraping trigger passed - processed {session['tweets_processed']} tweets")
    
    def test_08_tweet_filtering(self):
        """Test tweet filtering"""
        print("\n🔍 Testing tweet filtering...")
        
        # Get all tweets first
        response = self.session.get(f"{self.base_url}/tweets?limit=10")
        self.assertEqual(response.status_code, 200)
        all_tweets = response.json()
        
        if not all_tweets:
            print("⚠️ No tweets available to test filtering")
            return
        
        # Test author filter if we have author data
        if all_tweets and "author" in all_tweets[0]["tweet_data"]:
            author = all_tweets[0]["tweet_data"]["author"]
            response = self.session.get(f"{self.base_url}/tweets?author={author}&limit=5")
            self.assertEqual(response.status_code, 200)
            filtered_tweets = response.json()
            
            if filtered_tweets:
                for tweet in filtered_tweets:
                    self.assertEqual(tweet["tweet_data"]["author"], author)
                print(f"✅ Author filtering passed - found {len(filtered_tweets)} tweets by {author}")
            else:
                print(f"⚠️ Author filtering returned no results for {author}")
        
        # Test sentiment filter
        if all_tweets and "sentiment" in all_tweets[0]["ai_analysis"]:
            sentiment = all_tweets[0]["ai_analysis"]["sentiment"]["label"]
            response = self.session.get(f"{self.base_url}/tweets?sentiment={sentiment}&limit=5")
            self.assertEqual(response.status_code, 200)
            filtered_tweets = response.json()
            
            if filtered_tweets:
                for tweet in filtered_tweets:
                    self.assertEqual(tweet["ai_analysis"]["sentiment"]["label"], sentiment)
                print(f"✅ Sentiment filtering passed - found {len(filtered_tweets)} {sentiment} tweets")
            else:
                print(f"⚠️ Sentiment filtering returned no results for {sentiment}")
        
        print("✅ Tweet filtering tests completed")
    
    def test_09_scheduler_control(self):
        """Test scheduler control endpoints"""
        print("\n🔍 Testing scheduler control...")
        
        # Get initial state
        response = self.session.get(f"{self.base_url}/scheduler/status")
        initial_state = response.json()["running"]
        
        # Stop scheduler
        response = self.session.post(f"{self.base_url}/scheduler/stop")
        self.assertEqual(response.status_code, 200)
        
        # Verify it's stopped
        response = self.session.get(f"{self.base_url}/scheduler/status")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["running"])
        print("✅ Scheduler stop endpoint passed")
        
        # Start scheduler
        response = self.session.post(f"{self.base_url}/scheduler/start")
        self.assertEqual(response.status_code, 200)
        
        # Verify it's running
        response = self.session.get(f"{self.base_url}/scheduler/status")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["running"])
        print("✅ Scheduler start endpoint passed")
        
        # Restore initial state if needed
        if not initial_state:
            self.session.post(f"{self.base_url}/scheduler/stop")
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        test_methods = [method for method in dir(self) if method.startswith('test_')]
        test_methods.sort()  # Ensure tests run in order
        
        results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        
        print("\n🔍 STARTING TWITTER SCRAPER API TESTS 🔍")
        print("=" * 50)
        
        for method in test_methods:
            try:
                getattr(self, method)()
                results["passed"] += 1
            except Exception as e:
                results["failed"] += 1
                error_msg = f"❌ {method} FAILED: {str(e)}"
                print(error_msg)
                results["errors"].append(error_msg)
        
        print("\n" + "=" * 50)
        print(f"📊 TEST RESULTS: {results['passed']} passed, {results['failed']} failed")
        
        if results["errors"]:
            print("\nERRORS:")
            for error in results["errors"]:
                print(f"  {error}")
        
        return results["failed"] == 0

if __name__ == "__main__":
    tester = TwitterScraperAPITest()
    success = tester.run_all_tests()
    exit(0 if success else 1)